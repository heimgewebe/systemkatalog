#!/usr/bin/env python3
"""Build the read-only Systemkatalog map handoff manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

CONTRACT_VERSION = "1"
MANIFEST_KIND = "system_catalog_map_artifact_manifest"
SCHEMA_PATH = "catalog/ecosystem-map-artifact-manifest.schema.v1.json"
DEFAULT_OUTPUT = Path("rendered/ecosystem-map-artifact-manifest.json")
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
        "role": "readable_overview_mermaid",
        "path": "rendered/ecosystem-registry-map.mmd",
        "contentType": "text/mermaid",
    },
    {
        "role": "generated_registry_projection_mermaid",
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(root: Path) -> str:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EcosystemMapManifestError("could not determine source commit") from exc
    if not _is_sha(value):
        raise EcosystemMapManifestError("invalid source commit")
    return value


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
            "generatedAt": generated_at or _generated_at(),
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
        if not isinstance(item["sha256"], str) or len(item["sha256"]) != 64:
            raise EcosystemMapManifestError(f"artifact digest invalid: {spec['role']}")
    if set(manifest["doesNotEstablish"]) != set(DOES_NOT_ESTABLISH):
        raise EcosystemMapManifestError("manifest non-claims mismatch")


def write_manifest(repo_root: Path, output: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    target = _safe_path(root, output, "output")
    manifest = build_manifest(root)
    validate_manifest(manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        manifest = build_manifest(root) if args.check else write_manifest(root, Path(args.output))
        validate_manifest(manifest)
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
    }
    print(json.dumps(result, sort_keys=True) if args.json else (
        f"ecosystemMapArtifactManifest={manifest['kind']} action={result['action']} artifactCount={manifest['artifactCount']}"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
