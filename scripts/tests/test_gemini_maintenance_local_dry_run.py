"""Tests for the local Gemini maintenance dry-run runner."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

from run_gemini_maintenance_local_dry_run import _model_response_from_stdout, build_prompt, main as local_main  # noqa: E402

DUMP_PERMISSION = "dump_generation_" + "permission"
AUTO_DISPATCH = "autonomous_" + "dispatch"
CABINET_GENERATES = "cabinet" + "Generates" + "Dumps"


def write_text(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def external_dump_registry() -> dict[str, object]:
    def source(source_id: str, family: str) -> dict[str, object]:
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


def make_repo(root: Path) -> None:
    files = {
        "AGENTS.md": "# Agents\n",
        "README.md": "# Cabinet\n",
        "docs/blueprints/cabinet-maintenance-radar-v0.md": "# Radar\n",
        "docs/blueprints/agent-routing-brief-v0.md": "# Routing\n",
        "docs/contracts/cabinet-frontier-v1.md": "# Frontier\n",
        "docs/contracts/cabinet-gemini-maintenance-scan-v1.md": "# Scan\n",
        "docs/contracts/cabinet-external-dump-sources-v1.md": "# External dumps\n",
        "docs/contracts/cabinet-maintenance-report-v1.md": "# Maintenance report\n",
        "scripts/write_cabinet_maintenance_report.py": "# fixture\n",
    }
    for relative_path, content in files.items():
        write_text(root / relative_path, content)
    write_json(root / "registry/ecosystem/nodes.json", {"nodes": [{"id": "repo:cabinet"}, {"id": "repo:bureau"}]})
    write_json(root / "registry/ecosystem/edges.json", {"edge_types": ["depends_on"], "edges": []})
    write_json(root / "registry/ecosystem/external-dump-sources.json", external_dump_registry())
    write_json(root / "docs/contracts/cabinet-external-dump-sources-v1.schema.json", {})
    write_json(root / "docs/contracts/cabinet-maintenance-report-v1.schema.json", {})
    write_json(
        root / "registry/ecosystem/bureau-bridge.json",
        {
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
        },
    )
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
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class LocalGeminiMaintenanceDryRunTests(unittest.TestCase):
    def test_prompt_is_read_only_and_local_packet_bound(self) -> None:
        prompt = build_prompt(Path("pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json"))
        self.assertIn("Read only this curated evidence packet", prompt)
        self.assertIn("CABINET-GEMINI-MAINT-V1-T004", prompt)
        self.assertIn("All effectFlags must be false", prompt)
        self.assertIn("Do not request repository writes", prompt)
        self.assertNotIn("GEMINI_API_KEY", prompt)

    def test_model_response_unwraps_gemini_json_wrapper(self) -> None:
        response = '{"schemaVersion": 1, "kind": "cabinet_gemini_maintenance_scan"}'
        wrapper = json.dumps({"response": response, "stats": {"models": {}}, "error": None})
        self.assertEqual(_model_response_from_stdout(wrapper), response)

    def test_model_response_keeps_plain_text_stdout(self) -> None:
        self.assertEqual(_model_response_from_stdout("plain model text"), "plain model text")

    def test_local_runner_dry_run_writes_reviewable_blocked_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = local_main([
                    "--repo-root",
                    str(root),
                    "--output-dir",
                    "pruefung/10 Laeufe",
                    "--dry-run",
                    "--allow-blocked",
                    "--json",
                ])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["scanStatus"], "blocked")
            for key in (
                "evidencePacket",
                "rawOutput",
                "scanOutput",
                "reviewOutput",
                "summaryOutput",
                "errorOutput",
                "wrapperOutput",
                "promptOutput",
            ):
                self.assertTrue(Path(payload[key]).is_file(), key)
            scan = json.loads(Path(payload["scanOutput"]).read_text(encoding="utf-8"))
            self.assertEqual(scan["status"], "blocked")
            self.assertTrue(all(value is False for value in scan["effectFlags"].values()))

    def test_local_runner_requires_gemini_binary_when_not_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = local_main([
                    "--repo-root",
                    str(root),
                    "--gemini-bin",
                    "definitely-not-a-real-gemini-binary",
                    "--json",
                ])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 1)
            self.assertFalse(payload["ok"])
            self.assertIn("Gemini CLI was not found", payload["error"])


if __name__ == "__main__":
    unittest.main()
