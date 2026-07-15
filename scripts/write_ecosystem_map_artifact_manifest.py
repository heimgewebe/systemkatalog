#!/usr/bin/env python3
"""Write or verify the published read-only Systemkatalog map handoff manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

CONTRACT_VERSION = "1"
MANIFEST_KIND = "system_catalog_map_artifact_manifest"
SCHEMA_PATH = "catalog/ecosystem-map-artifact-manifest.schema.v1.json"
DEFAULT_OUTPUT = Path("rendered/ecosystem-map-artifact-manifest.json")
DEFAULT_BRANCH_REF = "refs/remotes/origin/main"
ALLOWED_DURABLE_REF_PREFIXES = ("refs/remotes/origin/", "refs/remotes/pull-request/")
GENERATED_FILE_MODE = 0o644
DOES_NOT_ESTABLISH = (
    "claim_truth",
    "runtime_correctness",
    "merge_readiness",
    "system_catalog_registry_correctness",
    "consumer_view_correctness",
    "render_success_validates_map",
)
ARTIFACT_SPECS: tuple[dict[str, str], ...] = (
    {
        "role": "canonical_ecosystem_map_mermaid",
        "path": "rendered/ecosystem-registry-map.mmd",
        "contentType": "text/mermaid",
    },
    {
        "role": "rendered_catalog_markdown",
        "path": "rendered/system-catalog.md",
        "contentType": "text/markdown",
    },
    {
        "role": "registry_nodes",
        "path": "registry/ecosystem/nodes.json",
        "contentType": "application/json",
    },
    {
        "role": "registry_edges",
        "path": "registry/ecosystem/edges.json",
        "contentType": "application/json",
    },
    {
        "role": "authority_matrix",
        "path": "registry/ecosystem/authority-matrix.v1.json",
        "contentType": "application/json",
    },
)


class EcosystemMapManifestError(RuntimeError):
    pass


def _safe_path(root: Path, raw: str | Path, label: str) -> Path:
    value = Path(raw)
    resolved = value.resolve() if value.is_absolute() else (root / value).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EcosystemMapManifestError(f"{label} path escapes repository: {resolved}") from exc
    return resolved


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *arguments: str, text: bool = True) -> str | bytes:
    try:
        return subprocess.check_output(
            ["git", *arguments],
            cwd=root,
            text=text,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        rendered = " ".join(arguments)
        raise EcosystemMapManifestError(f"git command failed: {rendered}") from exc


def _git_commit(root: Path) -> str:
    value = str(_git(root, "rev-parse", "HEAD")).strip()
    if not _is_sha(value):
        raise EcosystemMapManifestError("invalid source commit")
    return value


def _git_commit_timestamp(root: Path, commit: str) -> str:
    if not _is_sha(commit):
        raise EcosystemMapManifestError("invalid source commit")
    raw = str(_git(root, "show", "-s", "--format=%cI", commit)).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EcosystemMapManifestError("invalid source commit timestamp") from exc
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_ref_exists(root: Path, ref: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise EcosystemMapManifestError("could not inspect durable source ref") from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise EcosystemMapManifestError("could not inspect durable source ref")


def _durable_source_ref(root: Path) -> str:
    return DEFAULT_BRANCH_REF if _git_ref_exists(root, DEFAULT_BRANCH_REF) else "HEAD"


def _validate_durable_source_ref(root: Path, ref: str) -> str:
    if not isinstance(ref, str) or not ref.startswith(ALLOWED_DURABLE_REF_PREFIXES):
        raise EcosystemMapManifestError(
            "durable source ref must be a remote-tracking origin or pull-request ref"
        )
    try:
        result = subprocess.run(
            ["git", "check-ref-format", ref],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise EcosystemMapManifestError("could not validate durable source ref") from exc
    if result.returncode != 0 or not _git_ref_exists(root, ref):
        raise EcosystemMapManifestError(f"durable source ref is missing or invalid: {ref}")
    return ref


def _git_is_ancestor(root: Path, commit: str, descendant: str) -> bool:
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, descendant],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 1:
            return False
        raise EcosystemMapManifestError("could not verify source commit ancestry") from exc
    except OSError as exc:
        raise EcosystemMapManifestError("could not verify source commit ancestry") from exc


def _git_artifact(root: Path, commit: str, relative: str) -> bytes:
    value = _git(root, "show", f"{commit}:{relative}", text=False)
    if not isinstance(value, bytes):
        raise EcosystemMapManifestError(f"could not read committed artifact: {relative}")
    return value


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        ch in "0123456789abcdef" for ch in value
    )


def _artifact(root: Path, spec: dict[str, str]) -> dict[str, Any]:
    path = _safe_path(root, spec["path"], spec["role"])
    if not path.is_file() or path.stat().st_size < 1:
        raise EcosystemMapManifestError(f"missing or empty map artifact: {spec['path']}")
    return {
        "role": spec["role"],
        "path": spec["path"],
        "contentType": spec["contentType"],
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def build_manifest(
    repo_root: Path,
    *,
    source_commit: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    commit = source_commit or _git_commit(root)
    if not _is_sha(commit):
        raise EcosystemMapManifestError("source_commit must be a lowercase 40 character git SHA")
    deterministic_time = _git_commit_timestamp(root, commit)
    if generated_at is not None and generated_at != deterministic_time:
        raise EcosystemMapManifestError("generated_at must equal the source commit timestamp")
    artifacts = [_artifact(root, spec) for spec in ARTIFACT_SPECS]
    return {
        "schemaVersion": 1,
        "kind": MANIFEST_KIND,
        "contractVersion": CONTRACT_VERSION,
        "schemaPath": SCHEMA_PATH,
        "mode": "read_only_projection_source",
        "source": {
            "repository": "heimgewebe/systemkatalog",
            "commit": commit,
            "generatedAt": deterministic_time,
        },
        "artifactCount": len(artifacts),
        "artifacts": artifacts,
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    expected_fields = {
        "schemaVersion", "kind", "contractVersion", "schemaPath", "mode",
        "source", "artifactCount", "artifacts", "doesNotEstablish",
    }
    if set(manifest) != expected_fields:
        raise EcosystemMapManifestError("manifest fields mismatch")
    if manifest["schemaVersion"] != 1 or manifest["kind"] != MANIFEST_KIND:
        raise EcosystemMapManifestError("manifest identity mismatch")
    if manifest["contractVersion"] != CONTRACT_VERSION or manifest["schemaPath"] != SCHEMA_PATH:
        raise EcosystemMapManifestError("manifest contract binding mismatch")
    if manifest["mode"] != "read_only_projection_source":
        raise EcosystemMapManifestError("manifest mode mismatch")
    source = manifest["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "commit", "generatedAt"}:
        raise EcosystemMapManifestError("manifest source fields mismatch")
    if source["repository"] != "heimgewebe/systemkatalog" or not _is_sha(source["commit"]):
        raise EcosystemMapManifestError("manifest source identity mismatch")
    if not isinstance(source["generatedAt"], str) or not source["generatedAt"]:
        raise EcosystemMapManifestError("manifest generatedAt missing")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != len(ARTIFACT_SPECS):
        raise EcosystemMapManifestError("artifact count mismatch")
    if manifest["artifactCount"] != len(ARTIFACT_SPECS):
        raise EcosystemMapManifestError("artifactCount mismatch")
    for item, spec in zip(artifacts, ARTIFACT_SPECS, strict=True):
        if not isinstance(item, dict) or set(item) != {"role", "path", "contentType", "bytes", "sha256"}:
            raise EcosystemMapManifestError("artifact fields mismatch")
        if item["role"] != spec["role"] or item["path"] != spec["path"] or item["contentType"] != spec["contentType"]:
            raise EcosystemMapManifestError(f"artifact contract mismatch: {spec['role']}")
        if not isinstance(item["bytes"], int) or item["bytes"] < 1:
            raise EcosystemMapManifestError(f"artifact byte count invalid: {spec['role']}")
        if not _is_sha256(item["sha256"]):
            raise EcosystemMapManifestError(f"artifact digest invalid: {spec['role']}")
    if tuple(manifest["doesNotEstablish"]) != DOES_NOT_ESTABLISH:
        raise EcosystemMapManifestError("manifest non-claims mismatch")


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EcosystemMapManifestError(f"published manifest missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EcosystemMapManifestError(f"published manifest is invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise EcosystemMapManifestError("published manifest root must be an object")
    return value


def _validate_source_binding(
    root: Path,
    manifest: dict[str, Any],
    *,
    durable_source_ref: str | None = None,
) -> None:
    commit = manifest["source"]["commit"]
    durable_ref = (
        _validate_durable_source_ref(root, durable_source_ref)
        if durable_source_ref is not None
        else _durable_source_ref(root)
    )
    if not _git_is_ancestor(root, commit, durable_ref):
        raise EcosystemMapManifestError(
            f"manifest source commit is not an ancestor of durable ref {durable_ref}"
        )
    for item in manifest["artifacts"]:
        content = _git_artifact(root, commit, item["path"])
        if len(content) != item["bytes"] or _sha256_bytes(content) != item["sha256"]:
            raise EcosystemMapManifestError(
                f"artifact does not match bound source commit: {item['path']}"
            )


def check_manifest(
    repo_root: Path,
    output: Path = DEFAULT_OUTPUT,
    *,
    durable_source_ref: str | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    target = _safe_path(root, output, "output")
    manifest = _load_manifest(target)
    validate_manifest(manifest)
    source = manifest["source"]
    _validate_source_binding(
        root, manifest, durable_source_ref=durable_source_ref
    )
    expected = build_manifest(
        root,
        source_commit=source["commit"],
        generated_at=source["generatedAt"],
    )
    if manifest != expected:
        raise EcosystemMapManifestError("published manifest is stale for current artifacts")
    return manifest


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            os.fchmod(handle.fileno(), GENERATED_FILE_MODE)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_manifest(
    repo_root: Path,
    output: Path,
    *,
    source_commit: str | None = None,
    generated_at: str | None = None,
    durable_source_ref: str | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    target = _safe_path(root, output, "output")
    manifest = build_manifest(root, source_commit=source_commit, generated_at=generated_at)
    validate_manifest(manifest)
    _validate_source_binding(
        root, manifest, durable_source_ref=durable_source_ref
    )
    _atomic_write(
        target,
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--generated-at")
    parser.add_argument(
        "--durable-source-ref",
        help=(
            "Published remote-tracking ref used to prove the source commit is durable. "
            "Defaults to refs/remotes/origin/main."
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    output = Path(args.output)
    try:
        if args.check:
            if args.source_commit or args.generated_at:
                raise EcosystemMapManifestError(
                    "--source-commit and --generated-at are write-only options"
                )
            manifest = check_manifest(
                root,
                output,
                durable_source_ref=args.durable_source_ref,
            )
        else:
            manifest = write_manifest(
                root,
                output,
                source_commit=args.source_commit,
                generated_at=args.generated_at,
                durable_source_ref=args.durable_source_ref,
            )
    except (EcosystemMapManifestError, OSError, UnicodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"write_ecosystem_map_artifact_manifest: {exc}", file=sys.stderr)
        return 2
    result = {
        "ok": True,
        "action": "check" if args.check else "write",
        "kind": manifest["kind"],
        "sourceCommit": manifest["source"]["commit"],
        "artifactCount": manifest["artifactCount"],
        "output": str(output),
    }
    print(json.dumps(result, sort_keys=True) if args.json else (
        f"ecosystemMapArtifactManifest={manifest['kind']} action={result['action']} "
        f"artifactCount={manifest['artifactCount']} output={result['output']}"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
