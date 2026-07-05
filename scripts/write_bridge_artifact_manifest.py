#!/usr/bin/env python3
"""Validate Cabinet bridge evidence artifacts and write a manifest.

This script is evidence-only. It checks files already produced by CI and writes
`bridge-artifact-manifest.json`. It does not import into Bureau, mutate queues,
create tasks, dispatch work, or touch runtime state.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ARTIFACT_SPECS: tuple[dict[str, str], ...] = (
    {
        "path": "bridge-import-policy-review.json",
        "kind": "bureau.cabinet_bridge_import_review_contract_policy_review",
    },
    {"path": "bridge-probe-report.json", "kind": "cabinet_bureau_bridge_probe"},
    {"path": "bridge-probe-summary.md", "kind": "markdown_summary"},
    {"path": "bridge-preview.json", "kind": "cabinet_bridge_promotion_preview"},
    {"path": "bridge-review.json", "kind": "cabinet_bridge_preview_review_gate"},
    {"path": "bridge-receipt.json", "kind": "cabinet_bridge_review_receipt"},
)

EFFECT_FLAGS = (
    "importAllowed",
    "dispatchAllowed",
    "queueMutationAllowed",
    "taskCreationAllowed",
)

MANIFEST_EFFECT_FLAGS = {field: False for field in EFFECT_FLAGS}
MANIFEST_KIND = "cabinet_bridge_artifact_manifest"


class BridgeArtifactManifestError(RuntimeError):
    """Raised when the bridge artifact contract is violated."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeArtifactManifestError(f"missing bridge artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BridgeArtifactManifestError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise BridgeArtifactManifestError(f"{path} must contain a JSON object")
    return payload


def validate_and_build_manifest(root: Path, bureau_ref: str) -> dict[str, Any]:
    if not bureau_ref.strip():
        raise BridgeArtifactManifestError("bureau_ref must be non-empty")

    payloads: dict[str, dict[str, Any]] = {}
    for spec in ARTIFACT_SPECS:
        artifact = root / spec["path"]
        if not artifact.exists():
            raise BridgeArtifactManifestError(f"missing bridge artifact: {artifact}")
        if artifact.suffix == ".json":
            payload = _load_json(artifact)
            payloads[spec["path"]] = payload
            if payload.get("kind") != spec["kind"]:
                raise BridgeArtifactManifestError(
                    f"{artifact} kind mismatch: {payload.get('kind')!r}"
                )
            for field in EFFECT_FLAGS:
                if field in payload and payload.get(field) is not False:
                    raise BridgeArtifactManifestError(f"{artifact} {field} must be false")
        elif not artifact.read_text(encoding="utf-8").strip():
            raise BridgeArtifactManifestError(f"empty bridge artifact: {artifact}")

    if payloads["bridge-import-policy-review.json"].get("importReviewRequired") is not True:
        raise BridgeArtifactManifestError("policy review must require import review")
    if payloads["bridge-receipt.json"].get("importReviewRequired") is not True:
        raise BridgeArtifactManifestError("receipt must require import review")

    return {
        "schemaVersion": 1,
        "kind": MANIFEST_KIND,
        "mode": "evidence_only",
        "bureauRef": bureau_ref,
        "artifactCount": len(ARTIFACT_SPECS),
        "artifacts": list(ARTIFACT_SPECS),
        "effectFlags": dict(MANIFEST_EFFECT_FLAGS),
    }


def write_manifest(root: Path, output: Path, bureau_ref: str) -> dict[str, Any]:
    manifest = validate_and_build_manifest(root, bureau_ref)
    target = output if output.is_absolute() else root / output
    target.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="write_bridge_artifact_manifest")
    result.add_argument("--root", default=".", help="Directory containing bridge evidence files.")
    result.add_argument("--output", default="bridge-artifact-manifest.json")
    result.add_argument(
        "--bureau-ref",
        default=os.environ.get("BUREAU_PROBE_REF", ""),
        help="Pinned Bureau commit used to produce/validate bridge evidence.",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest = write_manifest(Path(args.root), Path(args.output), args.bureau_ref)
    except BridgeArtifactManifestError as exc:
        print(f"write_bridge_artifact_manifest: {exc}", file=sys.stderr)
        return 2
    print("artifactManifest=%s artifactCount=%s" % (manifest["kind"], manifest["artifactCount"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
