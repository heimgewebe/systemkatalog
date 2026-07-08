"""Contract tests for the manual Gemini maintenance dry-run path."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

from extract_gemini_maintenance_scan import _blocked_scan, main as extract_main  # noqa: E402
from validate_gemini_maintenance_scan import EFFECT_FLAGS, validate_scan  # noqa: E402

WORKFLOW = ROOT / ".github/workflows/gemini-maintenance-dry-run.yml"
MANIFEST = ROOT / "policy/gemini-maintenance-execution-manifest.v1.json"
GEMINI_CLI_NPM_VERSION = "0.51.0-nightly.20260707.g15a9429b6"


def read_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def valid_scan() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "cabinet_gemini_maintenance_scan",
        "contractVersion": "1",
        "contractPath": "docs/contracts/cabinet-gemini-maintenance-scan-v1.md",
        "schemaPath": "docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json",
        "id": "gemini-scan:cabinet:2026-07-08T17-00-00Z",
        "createdAt": "2026-07-08T17:00:00Z",
        "status": "completed",
        "source": {
            "repository": "heimgewebe/cabinet",
            "commit": "a" * 40,
            "executionManifestRef": "policy/gemini-maintenance-execution-manifest.v1.json",
            "evidenceManifestRef": "pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json",
            "inputRefs": ["evidence:AGENTS.md"],
        },
        "lane": {
            "id": "cabinet-gemini-maintenance",
            "bureauTask": "CABINET-GEMINI-MAINT-V1-T004",
            "mode": "manual_dry_run",
        },
        "findings": {
            "observed": [
                {
                    "id": "finding:observed:fixture",
                    "title": "Fixture finding",
                    "summary": "Directly evidenced fixture finding.",
                    "severity": "info",
                    "confidence": "high",
                    "evidenceRefs": ["evidence:AGENTS.md"],
                    "recommendedNextAction": "review_only",
                }
            ],
            "plausible": [],
            "speculative": [],
        },
        "effectFlags": {flag: False for flag in EFFECT_FLAGS},
        "forbiddenEffects": [
            "issue_creation",
            "pr_creation",
            "comment_creation",
            "bureau_task_creation",
            "queue_mutation",
            "grabowski_dispatch",
            "merge_or_push",
            "runtime_mutation",
            "secret_request",
            "dump_generation",
            "cleanup_action",
        ],
        "doesNotEstablish": [
            "task_approval",
            "claim_truth",
            "merge_readiness",
            "runtime_correctness",
            "bureau_import",
            "autonomous_dispatch",
            "bureau_task_created",
            "schedule_approval",
            "gemini_schedulability",
        ],
    }


class GeminiMaintenanceDryRunWorkflowTests(unittest.TestCase):
    def test_workflow_is_manual_only_and_read_only(self) -> None:
        workflow = read_workflow()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("issue_comment:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        forbidden_fragments = [
            "contents: write",
            "issues: write",
            "pull-requests: write",
            "actions: write",
            "id-token: write",
            "gh pr",
            "gh issue",
            "git push",
        ]
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, workflow)

    def test_workflow_pins_boundaries_and_artifacts(self) -> None:
        workflow = read_workflow()
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("google-github-actions/run-gemini-cli@f77273f4c914e4bf38440cf36a0369cb64a37489", workflow)
        self.assertIn(f"gemini_cli_version: {GEMINI_CLI_NPM_VERSION}", workflow)
        self.assertNotIn(f"gemini_cli_version: v{GEMINI_CLI_NPM_VERSION}", workflow)
        self.assertIn("gemini_debug: 'false'", workflow)
        self.assertIn("upload_artifacts: 'false'", workflow)
        self.assertIn('"coreTools":["ReadFileTool"]', workflow)
        self.assertIn('"enableRecursiveFileSearch":false', workflow)
        self.assertIn('"telemetry":{"enabled":false,"logPrompts":false}', workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("gemini-maintenance-dry-run-scan.json", workflow)
        self.assertIn("CABINET-GEMINI-MAINT-V1-T004", workflow)

    def test_execution_manifest_matches_workflow_boundary(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "manual-dry-run-enabled")
        self.assertEqual(manifest["bureau_task_lineage"], "CABINET-GEMINI-MAINT-V1-T004")
        self.assertEqual(manifest["gemini_cli"]["initial_candidate_npm_version"], GEMINI_CLI_NPM_VERSION)
        self.assertIn("leading v tag refs are forbidden", manifest["gemini_cli"]["version_policy"])
        self.assertEqual(manifest["trigger_policy"]["schedule"], "forbidden until reviewed dry run succeeds")
        self.assertEqual(manifest["permissions_policy"]["contents"], "read")
        self.assertEqual(manifest["permissions_policy"]["issues"], "none")
        self.assertFalse(manifest["permissions_policy"]["checkout_persist_credentials"])
        self.assertFalse(manifest["dry_run_gate"]["may_create_schedule"])

    def test_extract_valid_scan_from_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = root / "summary.txt"
            error = root / "error.txt"
            raw = root / "raw.json"
            scan_output = root / "scan.json"
            summary.write_text(json.dumps(valid_scan()), encoding="utf-8")
            error.write_text("", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = extract_main([
                    "--summary-input",
                    str(summary),
                    "--error-input",
                    str(error),
                    "--raw-output",
                    str(raw),
                    "--scan-output",
                    str(scan_output),
                    "--source-commit",
                    "a" * 40,
                    "--json",
                ])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(json.loads(scan_output.read_text(encoding="utf-8"))["status"], "completed")

    def test_extract_invalid_summary_writes_blocked_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = root / "summary.txt"
            raw = root / "raw.json"
            scan_output = root / "scan.json"
            summary.write_text("not json", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = extract_main([
                    "--summary-input",
                    str(summary),
                    "--raw-output",
                    str(raw),
                    "--scan-output",
                    str(scan_output),
                    "--source-commit",
                    "b" * 40,
                    "--json",
                ])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 2)
            self.assertFalse(payload["ok"])
            blocked = json.loads(scan_output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertTrue(all(value is False for value in blocked["effectFlags"].values()))

    def test_extract_invalid_scan_with_empty_summary_writes_blocked_scan(self) -> None:
        broken = valid_scan()
        broken["findings"]["plausible"] = [
            {
                "id": "finding:plausible:empty-summary",
                "title": "Empty summary",
                "summary": "",
                "severity": "unknown",
                "confidence": "medium",
                "evidenceRefs": [],
                "recommendedNextAction": "review_only",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = root / "summary.txt"
            raw = root / "raw.json"
            scan_output = root / "scan.json"
            summary.write_text(json.dumps(broken), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = extract_main([
                    "--summary-input",
                    str(summary),
                    "--raw-output",
                    str(raw),
                    "--scan-output",
                    str(scan_output),
                    "--source-commit",
                    "a" * 40,
                    "--json",
                ])
            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 2)
            self.assertFalse(payload["ok"])
            blocked = json.loads(scan_output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertTrue(blocked["findings"]["plausible"][0]["summary"].strip())
            validate_scan(blocked)

    def test_blocked_scan_normalizes_empty_reason(self) -> None:
        blocked = _blocked_scan(
            created_at="2026-07-08T17:00:00Z",
            source_commit="c" * 40,
            evidence_manifest_ref="pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json",
            reason="  \n\t  ",
        )
        self.assertTrue(blocked["findings"]["plausible"][0]["summary"].strip())
        validate_scan(blocked)


if __name__ == "__main__":
    unittest.main()
