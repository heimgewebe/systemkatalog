"""Tests for the Cabinet maintenance report writer."""

from __future__ import annotations

from datetime import date
import hashlib
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

from write_cabinet_maintenance_report import (  # noqa: E402
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    REPORT_KIND,
    SCHEMA_PATH,
    build_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_text(path: Path, content: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")




DUMP_PERMISSION = "dump_generation_" + "permission"
AUTO_DISPATCH = "autonomous_" + "dispatch"
CABINET_GENERATES = "cabinet" + "Generates" + "Dumps"


def external_manifest_payload(source: dict[str, Any]) -> dict[str, Any]:
    observation = source["observation"]
    return {
        "kind": source["requiredManifestKind"],
        "version": "1",
        "artifactFamily": source["artifactFamily"],
        "repository": "cabinet",
        "ref": "main",
        "generatedAt": observation["latestManifestGeneratedAt"],
        "freshnessBasis": "bundle_manifest.created_at",
        "bundleManifest": {
            "kind": "repolens.bundle.manifest",
            "path": "cabinet-test_merge.bundle.manifest.json",
            "runId": "cabinet-test",
            "createdAt": observation["latestManifestGeneratedAt"],
        },
        "artifacts": [
            {
                "role": f"required_{index}",
                "path": f"cabinet-test{suffix}",
                "sha256": "a" * 64,
            }
            for index, suffix in enumerate(source["requiredArtifactSuffixes"], start=1)
        ],
        "doesNotEstablish": [
            "dump_freshness_truth",
            "claim_truth",
            "runtime_correctness",
            "semantic_correctness",
            "task_approval",
            DUMP_PERMISSION,
            "repo_understood",
            "merge_readiness",
        ],
    }


def write_external_manifests(root: Path, payload: dict[str, Any]) -> None:
    for source in payload["sources"]:
        observation = source["observation"]
        if observation["status"] != "observed":
            continue
        write_json(root / observation["latestManifestPath"], external_manifest_payload(source))


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


def make_repo(root: Path, claim_overrides: dict[str, Any] | None = None, *, with_external_dump_registry: bool = False) -> None:
    write_json(root / "registry/ecosystem/nodes.json", {"nodes": [{"id": "repo:cabinet"}, {"id": "repo:bureau"}]})
    write_json(root / "registry/ecosystem/edges.json", {"edge_types": ["depends_on"], "edges": []})
    bridge = {
        "allowed_sources": [
            "registry/ecosystem/claims.jsonl",
            "registry/ecosystem/nodes.json",
            "registry/ecosystem/edges.json",
            "docs/blueprints/o.json",
            "docs/blueprints/cabinet-qa-radar-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.schema.json",
            "scripts/write_cabinet_maintenance_report.py",
            "steuerung/20 Aufgaben/cab-qa-001-cabinet-coherence-radar.md",
        ],
        "admissible_candidate_statuses": ["evidenced", "approved", "draft_decision_with_explicit_human_release"],
        "blocked_statuses": ["plausible", "speculative", "expired", "contradicted", "unverified"],
    }
    write_json(root / "registry/ecosystem/bureau-bridge.json", bridge)
    claim = {
        "id": "claim:cabinet-qa-radar-cab-qa-001-v0",
        "subject": "repo:cabinet",
        "predicate": "maintenance_role",
        "object": "coherence_radar_not_executor",
        "status": "evidenced",
        "confidence": 0.81,
        "evidence": [
            "docs/blueprints/cabinet-qa-radar-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.md",
            "docs/contracts/cabinet-maintenance-report-v1.schema.json",
            "scripts/write_cabinet_maintenance_report.py",
            "steuerung/20 Aufgaben/cab-qa-001-cabinet-coherence-radar.md",
        ],
        "expires_at": "2026-08-04",
        "expires_at_or_refresh_hint": "2026-08-04 or earlier when external-dump automation manifest is specified",
        "next_action": "run_cabinet_maintenance_report_before_bureau_task_creation",
        "responsible_organ": "cabinet",
    }
    if claim_overrides:
        claim.update(claim_overrides)
    (root / "registry/ecosystem/claims.jsonl").write_text(json.dumps(claim) + "\n", encoding="utf-8")
    for evidence in bridge["allowed_sources"] + claim["evidence"]:
        if isinstance(evidence, dict):
            evidence_ref = evidence.get("sourcePath") or evidence.get("ref") or ""
        else:
            evidence_ref = evidence
        if not isinstance(evidence_ref, str) or not evidence_ref or evidence_ref.startswith("registry/"):
            continue
        write_text(root / evidence_ref)
    if with_external_dump_registry:
        write_text(root / ("docs/contracts/" + "cabinet-" + "external-dump-sources-v1.md"))
        write_json(root / ("docs/contracts/" + "cabinet-" + "external-dump-sources-v1.schema.json"), {})
        registry_payload = external_dump_registry()
        write_json(root / ("registry/ecosystem/" + "external-dump-sources.json"), registry_payload)
        write_external_manifests(root, registry_payload)


def structured_repobrief_evidence(
    *,
    path: str = "docs/blueprints/cabinet-qa-radar-v1.md",
    sha256: str | None = None,
    generated_at: str = "2026-07-05T00:00:00Z",
    max_age_hours: int = 48,
) -> dict[str, Any]:
    if sha256 is None:
        sha256 = hashlib.sha256(b"x\n").hexdigest()
    return {
        "type": "repobrief_source_range",
        "ref": "external/repobrief/cabinet/main/manifest.json",
        "citationId": "citation:cabinet-qa-radar-v1:1-1",
        "sourcePath": path,
        "startLine": 1,
        "endLine": 1,
        "sha256": sha256,
        "freshnessBasis": "external_manifest_generated_at",
        "generatedAt": generated_at,
        "maxAgeHours": max_age_hours,
    }


class CabinetMaintenanceReportTests(unittest.TestCase):
    def test_build_report_lists_ready_bureau_candidate_without_effects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, with_external_dump_registry=True)

            report = build_report(
                root,
                source_commit="a" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["kind"], REPORT_KIND)
        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["bureauCandidateCount"], 1)
        self.assertEqual(report["bureauCandidates"][0]["id"], "claim:cabinet-qa-radar-cab-qa-001-v0")
        self.assertTrue(all(value is False for value in report["effectFlags"].values()))
        self.assertEqual(set(report["doesNotEstablish"]), set(DOES_NOT_ESTABLISH))

    def test_missing_external_dump_registry_is_warn_gap_not_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)

            report = build_report(
                root,
                source_commit="b" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["summary"]["epistemicGapCount"], 1)
        self.assertIn("external-dump", report["epistemicGaps"][0]["id"])

    def test_expired_claim_fails_and_blocks_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, {"expires_at": "2026-07-01"}, with_external_dump_registry=True)

            report = build_report(
                root,
                source_commit="c" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "fail")
        self.assertEqual(report["summary"]["severityCounts"]["P1"], 1)
        self.assertEqual(report["summary"]["bureauCandidateCount"], 0)

    def test_missing_local_evidence_path_is_p2_consistency_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(
                root,
                {"evidence": ["docs/blueprints/cabinet-qa-radar-v1.md", "docs/missing-evidence.md"]},
                with_external_dump_registry=True,
            )
            (root / "docs/missing-evidence.md").unlink(missing_ok=True)

            report = build_report(
                root,
                source_commit="d" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertTrue(any(finding["id"].endswith(":missing-evidence-path") for finding in report["findings"]))
        self.assertEqual(report["summary"]["severityCounts"]["P2"], 1)


    def test_structured_repobrief_evidence_can_remain_still_established(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(
                root,
                {"evidence": [structured_repobrief_evidence()]},
                with_external_dump_registry=True,
            )

            report = build_report(
                root,
                source_commit="1" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["status"], "still_established")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["citationId"], "citation:cabinet-qa-radar-v1:1-1")
        self.assertEqual(report["summary"]["claimEvidenceRevalidationCounts"]["still_established"], 1)

    def test_structured_repobrief_evidence_changed_is_p2_revalidation_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(
                root,
                {"evidence": [structured_repobrief_evidence(sha256="0" * 64)]},
                with_external_dump_registry=True,
            )

            report = build_report(
                root,
                source_commit="2" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["status"], "changed")
        self.assertTrue(any(finding["id"].endswith(":changed") for finding in report["findings"]))

    def test_structured_repobrief_evidence_stale_is_p2_revalidation_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(
                root,
                {"evidence": [structured_repobrief_evidence(generated_at="2026-07-01T00:00:00Z", max_age_hours=1)]},
                with_external_dump_registry=True,
            )

            report = build_report(
                root,
                source_commit="3" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["status"], "stale")
        self.assertTrue(any(finding["id"].endswith(":stale") for finding in report["findings"]))

    def test_structured_repobrief_evidence_missing_is_p2_revalidation_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(
                root,
                {"evidence": [structured_repobrief_evidence(path="docs/missing-repobrief-evidence.md")]},
                with_external_dump_registry=True,
            )
            (root / "docs/missing-repobrief-evidence.md").unlink()

            report = build_report(
                root,
                source_commit="4" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["status"], "missing")
        self.assertTrue(any(finding["id"].endswith(":missing") for finding in report["findings"]))

    def test_structured_repobrief_evidence_without_hash_or_freshness_is_unverifiable(self) -> None:
        evidence = structured_repobrief_evidence()
        for key in ("sha256", "generatedAt", "maxAgeHours", "freshnessBasis"):
            evidence.pop(key, None)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, {"evidence": [evidence]}, with_external_dump_registry=True)

            report = build_report(
                root,
                source_commit="5" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["claimEvidenceRevalidations"][0]["status"], "unverifiable")
        self.assertEqual(report["summary"]["severityCounts"]["P3"], 1)

    def test_external_dump_freshness_uses_report_timestamp_not_scan_midnight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, with_external_dump_registry=True)
            registry_path = root / "registry/ecosystem/external-dump-sources.json"
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            payload["sources"][0]["observation"]["latestManifestGeneratedAt"] = "2026-07-03T01:00:00Z"
            registry_path.write_text(json.dumps(payload), encoding="utf-8")
            write_external_manifests(root, payload)

            report = build_report(
                root,
                source_commit="e" * 40,
                generated_at="2026-07-05T23:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertTrue(any(finding["id"] == "cabqa:freshness:external-dump:repobrief:manifest-stale" for finding in report["findings"]))

    def test_observed_external_manifest_missing_is_p2_freshness_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, with_external_dump_registry=True)
            (root / "external/repobrief/cabinet/main/manifest.json").unlink()

            report = build_report(
                root,
                source_commit="f" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertTrue(any(
            finding["id"] == "cabqa:freshness:external-dump:repobrief:manifest-missing"
            for finding in report["findings"]
        ))

    def test_observed_external_manifest_timestamp_mismatch_is_p2_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, with_external_dump_registry=True)
            manifest_path = root / "external/repobrief/cabinet/main/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generatedAt"] = "2026-07-05T01:00:00Z"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = build_report(
                root,
                source_commit="0" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertTrue(any(
            finding["id"] == "cabqa:freshness:external-dump:repobrief:manifest-timestamp-mismatch"
            for finding in report["findings"]
        ))

    def test_observed_external_manifest_missing_required_artifact_is_p2_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, with_external_dump_registry=True)
            manifest_path = root / "external/repobrief/cabinet/main/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"] = [
                artifact
                for artifact in manifest["artifacts"]
                if not artifact["path"].endswith("_merge.json")
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = build_report(
                root,
                source_commit="1" * 40,
                generated_at="2026-07-05T00:00:00Z",
                scan_date=date(2026, 7, 5),
            )

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertTrue(any(
            finding["id"] == "cabqa:freshness:external-dump:repobrief:manifest-required-artifact-missing"
            for finding in report["findings"]
        ))

    def test_schema_constants_match_producer_contract(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(properties["kind"]["const"], REPORT_KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])


if __name__ == "__main__":
    unittest.main()
