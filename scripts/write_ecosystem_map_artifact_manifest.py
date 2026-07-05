#!/usr/bin/env python3
"""Write or validate the Cabinet ecosystem map artifact manifest.

The manifest is a read-only source contract for downstream viewers such as
Leitstand. It records the Cabinet commit, map artifact paths, digests and
non-claims. It does not edit the map, render diagrams, update registries,
dispatch work, or claim runtime truth.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1"
MANIFEST_KIND = "cabinet_ecosystem_map_artifact_manifest"
CONTRACT_PATH = "docs/contracts/cabinet-ecosystem-map-artifact-manifest-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-ecosystem-map-artifact-manifest-v1.schema.json"
DEFAULT_OUTPUT = Path("rendered/ecosystem-map-artifact-manifest.json")

DOES_NOT_ESTABLISH = (
    "claim_truth",
    "runtime_correctness",
    "merge_readiness",
    "cabinet_registry_correctness",
    "leitstand_view_correctness",
    "render_success_validates_map",
)

ARTIFACT_SPECS: tuple[dict[str, str], ...] = (
    {
        "role": "readable_overview_mermaid",
        "path": "rendered/ecosystem-map.mmd",
        "contentType": "text/mermaid",
    },
    {
        "role": "generated_registry_projection_mermaid",
        "path": "rendered/ecosystem-registry-map.mmd",
        "contentType": "text/mermaid",
    },
    {
        "role": "map_blueprint",
        "path": "docs/blueprints/ecosystem-map-v0.md",
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
        "role": "registry_claims",
        "path": "registry/ecosystem/claims.jsonl",
        "contentType": "application/x-ndjson",
    },
)


class EcosystemMapManifestError(RuntimeError):
    """Raised when map artifact manifest creation cannot proceed safely."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_relative_to_repo(repo_root: Path, raw_path: str | Path, label: str) -> Path:
    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise EcosystemMapManifestError(f"{label} path escapes repository: {resolved}") from exc
    return resolved


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EcosystemMapManifestError("could not determine git source commit") from exc
    commit = result.stdout.strip()
    if not _is_commit_sha(commit):
        raise EcosystemMapManifestError(f"invalid git source commit: {commit!r}")
    return commit


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_commit_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _artifact_entry(repo_root: Path, spec: dict[str, str]) -> dict[str, Any]:
    path = _ensure_relative_to_repo(repo_root, spec["path"], spec["role"])
    if not path.is_file():
        raise EcosystemMapManifestError(f"missing map artifact: {spec['path']}")
    if path.stat().st_size == 0:
        raise EcosystemMapManifestError(f"empty map artifact: {spec['path']}")
    return {
        "role": spec["role"],
        "path": spec["path"],
        "contentType": spec["contentType"],
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def build_manifest(
    repo_root: Path,
    *,
    source_commit: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    commit = source_commit or _git_commit(repo_root)
    if not _is_commit_sha(commit):
        raise EcosystemMapManifestError("source_commit must be a 40 character lowercase git SHA")
    timestamp = generated_at or _generated_at()
    artifacts = [_artifact_entry(repo_root, spec) for spec in ARTIFACT_SPECS]
    return {
        "schemaVersion": 1,
        "kind": MANIFEST_KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "mode": "read_only_projection_source",
        "source": {
            "repository": "heimgewebe/cabinet",
            "commit": commit,
            "generatedAt": timestamp,
        },
        "artifactCount": len(artifacts),
        "artifacts": artifacts,
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schemaVersion",
        "kind",
        "contractVersion",
        "contractPath",
        "schemaPath",
        "mode",
        "source",
        "artifactCount",
        "artifacts",
        "doesNotEstablish",
    }
    missing = sorted(required - set(manifest))
    extra = sorted(set(manifest) - required)
    if missing:
        raise EcosystemMapManifestError(f"manifest missing fields: {', '.join(missing)}")
    if extra:
        raise EcosystemMapManifestError(f"manifest has unexpected fields: {', '.join(extra)}")
    if manifest["schemaVersion"] != 1:
        raise EcosystemMapManifestError("schemaVersion must be 1")
    if manifest["kind"] != MANIFEST_KIND:
        raise EcosystemMapManifestError("kind mismatch")
    if manifest["contractVersion"] != CONTRACT_VERSION:
        raise EcosystemMapManifestError("contractVersion mismatch")
    if manifest["contractPath"] != CONTRACT_PATH:
        raise EcosystemMapManifestError("contractPath mismatch")
    if manifest["schemaPath"] != SCHEMA_PATH:
        raise EcosystemMapManifestError("schemaPath mismatch")
    if manifest["mode"] != "read_only_projection_source":
        raise EcosystemMapManifestError("mode mismatch")
    source = manifest["source"]
    if not isinstance(source, dict):
        raise EcosystemMapManifestError("source must be an object")
    if source.get("repository") != "heimgewebe/cabinet":
        raise EcosystemMapManifestError("source.repository mismatch")
    if not _is_commit_sha(source.get("commit")):
        raise EcosystemMapManifestError("source.commit must be a 40 character lowercase git SHA")
    if not isinstance(source.get("generatedAt"), str) or not source["generatedAt"]:
        raise EcosystemMapManifestError("source.generatedAt must be a non-empty string")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list):
        raise EcosystemMapManifestError("artifacts must be a list")
    if manifest["artifactCount"] != len(ARTIFACT_SPECS) or len(artifacts) != len(ARTIFACT_SPECS):
        raise EcosystemMapManifestError("artifact count mismatch")
    expected_roles = [spec["role"] for spec in ARTIFACT_SPECS]
    roles = [artifact.get("role") if isinstance(artifact, dict) else None for artifact in artifacts]
    if roles != expected_roles:
        raise EcosystemMapManifestError("artifact roles are not in contract order")
    for artifact, spec in zip(artifacts, ARTIFACT_SPECS, strict=True):
        if not isinstance(artifact, dict):
            raise EcosystemMapManifestError("artifact entry must be an object")
        allowed = {"role", "path", "contentType", "bytes", "sha256"}
        if set(artifact) != allowed:
            raise EcosystemMapManifestError(f"artifact {spec['role']} has invalid fields")
        if artifact["path"] != spec["path"]:
            raise EcosystemMapManifestError(f"artifact {spec['role']} path mismatch")
        if artifact["contentType"] != spec["contentType"]:
            raise EcosystemMapManifestError(f"artifact {spec['role']} contentType mismatch")
        if not isinstance(artifact["bytes"], int) or artifact["bytes"] < 1:
            raise EcosystemMapManifestError(f"artifact {spec['role']} bytes must be positive")
        if not isinstance(artifact["sha256"], str) or len(artifact["sha256"]) != 64:
            raise EcosystemMapManifestError(f"artifact {spec['role']} sha256 must be 64 hex chars")
    non_claims = manifest["doesNotEstablish"]
    if not isinstance(non_claims, list) or set(non_claims) != set(DOES_NOT_ESTABLISH):
        raise EcosystemMapManifestError("doesNotEstablish mismatch")


def write_manifest(repo_root: Path, output: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = _ensure_relative_to_repo(repo_root, output, "output")
    manifest = build_manifest(repo_root)
    validate_manifest(manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Manifest output path")
    parser.add_argument("--check", action="store_true", help="validate manifest contract without writing")
    parser.add_argument("--json", action="store_true", help="emit machine-readable status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        if args.check:
            manifest = build_manifest(repo_root)
            validate_manifest(manifest)
            action = "check"
        else:
            manifest = write_manifest(repo_root, Path(args.output))
            action = "write"
    except (EcosystemMapManifestError, OSError, UnicodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"write_ecosystem_map_artifact_manifest: {exc}", file=sys.stderr)
        return 2

    result = {
        "ok": True,
        "action": action,
        "kind": manifest["kind"],
        "sourceCommit": manifest["source"]["commit"],
        "artifactCount": manifest["artifactCount"],
        "output": str(args.output) if not args.check else None,
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "ecosystemMapArtifactManifest=%s action=%s artifactCount=%s"
            % (manifest["kind"], action, manifest["artifactCount"])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
