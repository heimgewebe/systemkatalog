"""Tests for the Gemini maintenance evidence packet generator."""

from __future__ import annotations

import contextlib
import io
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

from write_gemini_maintenance_evidence_packet import (  # noqa: E402
    CONTRACT_PATH,
    CONTRACT_VERSION,
    CURATED_INPUTS,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    GENERATOR_PATH,
    KIND,
    MAINTENANCE_REPORT_REF,
    SCHEMA_PATH,
    EvidencePacketError,
    build_packet,
    main as packet_main,
    validate_packet,
)

DUMP_PERMISSION = "dump_generation_" + "permission"
AUTO_DISPATCH = "autonomous_" + "dispatch"
CABINET_GENERATES = "cabinet" + "Generates" + "Dumps"
KEY_FIXTURE = ("-" * 5) + "BEGIN " + "PRIV" + "ATE " + "KEY" + ("-" * 5) + "\nredacted\n"


def write_text(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def external_dump_registry() -> dict[str, Any]:
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
                "status": "observed",
                "latestManifestPath": f"external/{family}/cabinet/main/manifest.json",
                "latestManifestGeneratedAt": "2026-07-05T00:00:00Z",
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

    return {
        "schemaVersion": 1,
        "kind": "cabinet_external_dump_sources",
        "contractVersion": "1",
        "contractPath": "docs/contracts/cabinet-external-dump-sources-v1.md",
        "schemaPath": "docs/contracts/cabinet-external-dump-sources-v1.schema.json",
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


def make_repo(root: Path, *, agents_content: str = "# Agents\n") -> None:
    for relative_path, role, media_type in CURATED_INPUTS:
        if relative_path == "AGENTS.md":
            write_text(root / relative_path, agents_content)
        elif media_type == "application/json":
            write_json(root / relative_path, {"fixture": relative_path, "role": role})
        else:
            write_text(root / relative_path, f"# {role}\n")

    write_json(root / "registry/ecosystem/nodes.json", {"nodes": [{"id": "repo:cabinet"}, {"id": "repo:bureau"}]})
    write_json(root / "registry/ecosystem/edges.json", {"edge_types": ["depends_on"], "edges": []})
    write_json(root / "registry/ecosystem/external-dump-sources.json", external_dump_registry())

    write_text(root / "docs/contracts/cabinet-external-dump-sources-v1.md")
    write_json(root / "docs/contracts/cabinet-external-dump-sources-v1.schema.json", {})
    write_text(root / "docs/contracts/cabinet-maintenance-report-v1.md")
    write_json(root / "docs/contracts/cabinet-maintenance-report-v1.schema.json", {})
    write_text(root / "scripts/write_cabinet_maintenance_report.py")

    bridge = {
        "allowed_sources": [
            "registry/ecosystem/claims.jsonl",
            "registry/ecosystem/nodes.json",
            "registry/ecosystem/edges.json",
            "docs/contracts/cabinet-maintenance-report-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.schema.json",
            "scripts/write_cabinet_maintenance_report.py",
        ],
        "admissible_candidate_statuses": ["evidenced", "approved", "draft_decision_with_explicit_human_release"],
        "blocked_statuses": ["plausible", "speculative", "expired", "contradicted", "unverified"],
    }
    write_json(root / "registry/ecosystem/bureau-bridge.json", bridge)

    claim = {
        "id": "claim:cabinet-gemini-maintenance-fixture",
        "subject": "repo:cabinet",
        "predicate": "maintenance_role",
        "object": "read_only_gemini_scout_input",
        "status": "evidenced",
        "confidence": 0.8,
        "evidence": [
            "docs/contracts/cabinet-maintenance-report-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.schema.json",
            "scripts/write_cabinet_maintenance_report.py",
        ],
        "expires_at": "2026-08-04",
        "expires_at_or_refresh_hint": "2026-08-04 or earlier when the curated packet changes",
        "next_action": "build_curated_gemini_evidence_packet",
        "responsible_organ": "cabinet",
    }
    legacy_claims = json.dumps(claim, sort_keys=True) + "\n"
    (root / "registry/ecosystem/claims.jsonl").write_text(legacy_claims, encoding="utf-8")
    write_text(root / "docs/archive/cabinet-era/ecosystem-dynamic-claims-v0.jsonl", legacy_claims)


class GeminiMaintenanceEvidencePacketTests(unittest.TestCase):
    def test_build_packet_contains_exact_allowlist_and_generated_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            packet = build_packet(root, source_commit="a" * 40, generated_at="2026-07-05T00:00:00Z")

        self.assertEqual(packet["kind"], KIND)
        self.assertEqual(packet["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(packet["contractPath"], CONTRACT_PATH)
        self.assertEqual(packet["schemaPath"], SCHEMA_PATH)
        self.assertEqual(packet["generator"], GENERATOR_PATH)
        self.assertEqual(packet["summary"]["sourceFileCount"], len(CURATED_INPUTS))
        self.assertEqual(packet["summary"]["generatedEntryCount"], 1)
        self.assertEqual(packet["inputPolicy"]["allowedRepoPaths"], [path for path, _role, _media in CURATED_INPUTS])
        self.assertFalse(packet["inputPolicy"]["fullRepositoryCrawlAllowed"])
        self.assertTrue(all(value is False for value in packet["effectFlags"].values()))
        self.assertEqual(set(packet["doesNotEstablish"]), set(DOES_NOT_ESTABLISH))
        report_entry = next(entry for entry in packet["entries"] if entry["ref"] == MAINTENANCE_REPORT_REF)
        report = json.loads(report_entry["content"])
        self.assertEqual(report["source"]["commit"], "a" * 40)
        self.assertEqual(report["summary"], packet["maintenanceReport"]["summary"])

    def test_missing_curated_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            (root / "README.md").unlink()
            with self.assertRaisesRegex(EvidencePacketError, "missing curated input"):
                build_packet(root, source_commit="b" * 40, generated_at="2026-07-05T00:00:00Z")

    def test_key_marker_in_curated_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, agents_content=KEY_FIXTURE)
            with self.assertRaisesRegex(EvidencePacketError, "key marker"):
                build_packet(root, source_commit="c" * 40, generated_at="2026-07-05T00:00:00Z")

    def test_true_effect_flag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            packet = build_packet(root, source_commit="d" * 40, generated_at="2026-07-05T00:00:00Z")
        packet["effectFlags"]["scheduleAllowed"] = True
        with self.assertRaisesRegex(EvidencePacketError, "effectFlags"):
            validate_packet(packet)

    def test_forbidden_entry_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            packet = build_packet(root, source_commit="e" * 40, generated_at="2026-07-05T00:00:00Z")
        first = next(entry for entry in packet["entries"] if entry["ref"] == "evidence:AGENTS.md")
        first["path"] = ".agents/private.txt"
        with self.assertRaisesRegex(EvidencePacketError, "forbidden|binding"):
            validate_packet(packet)

    def test_cli_validates_existing_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            packet = build_packet(root, source_commit="f" * 40, generated_at="2026-07-05T00:00:00Z")
            packet_path = root / "packet.json"
            packet_path.write_text(json.dumps(packet, sort_keys=True), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = packet_main(["--validate", str(packet_path), "--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["kind"], KIND)

    def test_schema_constants_match_generator(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["kind"]["const"], KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        self.assertEqual(properties["generator"]["const"], GENERATOR_PATH)
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])


if __name__ == "__main__":
    unittest.main()
