"""Tests for the Cabinet bridge artifact manifest writer."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

from write_bridge_artifact_manifest import (  # noqa: E402
    ARTIFACT_SPECS,
    CONTRACT_PATH,
    CONTRACT_VERSION,
    EFFECT_FLAGS,
    MANIFEST_KIND,
    SCHEMA_PATH,
    BridgeArtifactManifestError,
    validate_and_build_manifest,
    write_manifest,
)

SCHEMA_FILE = ROOT / SCHEMA_PATH


def write_json(root: Path, path: str, payload: dict[str, Any]) -> None:
    (root / path).write_text(json.dumps(payload), encoding="utf-8")


def write_valid_artifacts(root: Path) -> None:
    payload_by_path = {
        "bridge-import-policy-review.json": {
            "kind": "bureau.cabinet_bridge_import_review_contract_policy_review",
            "status": "valid",
            "importAllowed": False,
            "importReviewRequired": True,
        },
        "bridge-probe-report.json": {
            "kind": "cabinet_bureau_bridge_probe",
            "importAllowed": False,
            "dispatchAllowed": False,
            "queueMutationAllowed": False,
            "taskCreationAllowed": False,
        },
        "bridge-preview.json": {
            "kind": "cabinet_bridge_promotion_preview",
            "importAllowed": False,
            "dispatchAllowed": False,
            "queueMutationAllowed": False,
            "taskCreationAllowed": False,
        },
        "bridge-review.json": {
            "kind": "cabinet_bridge_preview_review_gate",
            "importAllowed": False,
            "dispatchAllowed": False,
            "queueMutationAllowed": False,
            "taskCreationAllowed": False,
        },
        "bridge-receipt.json": {
            "kind": "cabinet_bridge_review_receipt",
            "importAllowed": False,
            "importReviewRequired": True,
            "dispatchAllowed": False,
            "queueMutationAllowed": False,
            "taskCreationAllowed": False,
        },
    }
    for path, payload in payload_by_path.items():
        write_json(root, path, payload)
    (root / "bridge-probe-summary.md").write_text("# Summary\n", encoding="utf-8")


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


class BridgeArtifactManifestTests(unittest.TestCase):
    def test_manifest_is_written_for_complete_effect_closed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_artifacts(root)

            manifest = write_manifest(root, Path("bridge-artifact-manifest.json"), "b" * 40)
            stored = json.loads((root / "bridge-artifact-manifest.json").read_text())

        self.assertEqual(manifest["kind"], MANIFEST_KIND)
        self.assertEqual(manifest["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(manifest["contractPath"], CONTRACT_PATH)
        self.assertEqual(manifest["schemaPath"], SCHEMA_PATH)
        self.assertEqual(manifest["mode"], "evidence_only")
        self.assertEqual(manifest["artifactCount"], len(ARTIFACT_SPECS))
        self.assertEqual(stored, manifest)
        self.assertFalse(manifest["effectFlags"]["importAllowed"])

    def test_schema_matches_manifest_contract_constants(self) -> None:
        schema = load_schema()
        properties = schema["properties"]
        schema_artifacts = [
            {
                "path": item["properties"]["path"]["const"],
                "kind": item["properties"]["kind"]["const"],
            }
            for item in properties["artifacts"]["prefixItems"]
        ]

        self.assertEqual(properties["kind"]["const"], MANIFEST_KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        self.assertEqual(properties["artifactCount"]["const"], len(ARTIFACT_SPECS))
        self.assertEqual(schema_artifacts, list(ARTIFACT_SPECS))
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])

    def test_manifest_rejects_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_artifacts(root)
            (root / "bridge-preview.json").unlink()

            with self.assertRaisesRegex(BridgeArtifactManifestError, "missing bridge artifact"):
                validate_and_build_manifest(root, "b" * 40)

    def test_manifest_rejects_wrong_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_artifacts(root)
            payload = json.loads((root / "bridge-review.json").read_text())
            payload["kind"] = "wrong"
            write_json(root, "bridge-review.json", payload)

            with self.assertRaisesRegex(BridgeArtifactManifestError, "kind mismatch"):
                validate_and_build_manifest(root, "b" * 40)

    def test_manifest_rejects_enabled_effect_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_artifacts(root)
            payload = json.loads((root / "bridge-receipt.json").read_text())
            payload["dispatchAllowed"] = True
            write_json(root, "bridge-receipt.json", payload)

            with self.assertRaisesRegex(BridgeArtifactManifestError, "dispatchAllowed"):
                validate_and_build_manifest(root, "b" * 40)

    def test_manifest_requires_import_review_markers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_artifacts(root)
            payload = json.loads((root / "bridge-import-policy-review.json").read_text())
            payload["importReviewRequired"] = False
            write_json(root, "bridge-import-policy-review.json", payload)

            with self.assertRaisesRegex(BridgeArtifactManifestError, "import review"):
                validate_and_build_manifest(root, "b" * 40)


if __name__ == "__main__":
    unittest.main()
