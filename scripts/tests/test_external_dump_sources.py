"""Tests for the external dump source registry validator."""

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

from validate_external_dump_sources import (  # noqa: E402
    AUTO_DISPATCH,
    CONTRACT_PATH,
    SCHEMA_PATH,
    ExternalDumpSourcesError,
    validate_sources,
)

CABINET_GENERATES = "cabinetGenerates" + "Dumps"
DUMP_PERMISSION = "dump_generation_" + "permission"


def source(source_id: str, family: str) -> dict[str, Any]:
    return {
        "id": source_id,
        "artifactFamily": family,
        "producerOrgan": "repobrief_lenskit",
        "cadence": "on_repository_change_or_daily",
        "maxAgeHours": 48,
        "manifestPattern": f"external/{family}/{{repository}}/{{ref}}/manifest.json",
        "requiredManifestKind": f"{family}_bundle_manifest",
        "requiredArtifactSuffixes": ["_merge.agent_reading_pack.md", "_merge.md", "_merge.json"],
        "hashAlgorithm": "sha256",
        "freshnessBasis": "manifest_generated_at",
        "cabinetStorage": "external_reference_only",
        "observation": {
            "status": "unobserved",
            "latestManifestPath": "",
            "latestManifestGeneratedAt": "",
        },
        "doesNotEstablish": [
            "dump_freshness_truth",
            "claim_truth",
            "runtime_correctness",
            "semantic_correctness",
            "task_approval",
            DUMP_PERMISSION,
        ],
    }


def registry() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "cabinet_external_dump_sources",
        "contractVersion": "1",
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "mode": "external_dump_source_contract_registry",
        "updatedAt": "2026-07-05",
        CABINET_GENERATES: False,
        "sourceCount": 2,
        "sources": [source("external-dump:repobrief", "repobrief"), source("external-dump:lenskit", "lenskit")],
        "doesNotEstablish": [
            "dump_freshness_truth",
            "claim_truth",
            "runtime_correctness",
            "merge_readiness",
            "task_approval",
            AUTO_DISPATCH,
            DUMP_PERMISSION,
        ],
    }


def write_repo(root: Path, payload: dict[str, Any]) -> Path:
    (root / CONTRACT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / CONTRACT_PATH).write_text("# contract\n", encoding="utf-8")
    (root / SCHEMA_PATH).write_text("{}\n", encoding="utf-8")
    registry_path = root / "registry/ecosystem/external-dump-sources.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    return registry_path


class ExternalDumpSourceTests(unittest.TestCase):
    def test_valid_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry_path = write_repo(root, registry())
            result = validate_sources(root, registry_path)

        self.assertEqual(result["sourceCount"], 2)
        self.assertEqual({item["artifactFamily"] for item in result["sources"]}, {"repobrief", "lenskit"})

    def test_rejects_cabinet_producer_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = registry()
            payload[CABINET_GENERATES] = True
            registry_path = write_repo(root, payload)
            with self.assertRaisesRegex(ExternalDumpSourcesError, "cabinetGenerates"):
                validate_sources(root, registry_path)

    def test_rejects_duplicate_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = registry()
            payload["sources"][1]["id"] = payload["sources"][0]["id"]
            registry_path = write_repo(root, payload)
            with self.assertRaisesRegex(ExternalDumpSourcesError, "duplicate source id"):
                validate_sources(root, registry_path)

    def test_rejects_missing_family(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = registry()
            payload["sources"] = [payload["sources"][0]]
            payload["sourceCount"] = 1
            registry_path = write_repo(root, payload)
            with self.assertRaisesRegex(ExternalDumpSourcesError, "missing dump families"):
                validate_sources(root, registry_path)

    def test_unobserved_source_must_not_set_latest_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = registry()
            payload["sources"][0]["observation"]["latestManifestPath"] = "external/repobrief/x/main/manifest.json"
            registry_path = write_repo(root, payload)
            with self.assertRaisesRegex(ExternalDumpSourcesError, "unobserved state"):
                validate_sources(root, registry_path)

    def test_observed_source_requires_iso_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = registry()
            payload["sources"][0]["observation"] = {
                "status": "observed",
                "latestManifestPath": "external/repobrief/x/main/manifest.json",
                "latestManifestGeneratedAt": "not-a-date",
            }
            registry_path = write_repo(root, payload)
            with self.assertRaisesRegex(ExternalDumpSourcesError, "ISO timestamp"):
                validate_sources(root, registry_path)


if __name__ == "__main__":
    unittest.main()
