"""Tests for the Cabinet Gemini maintenance scan contract."""

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

from validate_gemini_maintenance_scan import (  # noqa: E402
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    FORBIDDEN_EFFECTS,
    KIND,
    SCHEMA_PATH,
    GeminiMaintenanceScanError,
    load_scans,
    main as validate_main,
    validate_scan,
)


def valid_scan() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "id": "gemini-scan:cabinet:2026-07-08T14-00-00Z",
        "createdAt": "2026-07-08T14:00:00Z",
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
            "bureauTask": "CABINET-GEMINI-MAINT-V1-T002",
            "mode": "manual_dry_run",
        },
        "findings": {
            "observed": [
                {
                    "id": "finding:observed:docs-boundary",
                    "title": "Observed evidence-bound finding",
                    "summary": "The finding is directly bound to the evidence packet.",
                    "severity": "low",
                    "confidence": "medium",
                    "evidenceRefs": ["evidence:AGENTS.md#L1-L10"],
                    "recommendedNextAction": "review_only",
                }
            ],
            "plausible": [
                {
                    "id": "finding:plausible:review-needed",
                    "title": "Plausible review need",
                    "summary": "The finding is plausible but not treated as claim truth.",
                    "severity": "info",
                    "confidence": "low",
                    "evidenceRefs": [],
                    "recommendedNextAction": "review_only",
                }
            ],
            "speculative": [],
        },
        "effectFlags": {field: False for field in EFFECT_FLAGS},
        "forbiddenEffects": list(FORBIDDEN_EFFECTS),
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


class GeminiMaintenanceScanContractTests(unittest.TestCase):
    def test_valid_scan_is_accepted_and_has_no_effects(self) -> None:
        scan = valid_scan()
        validate_scan(scan)
        self.assertEqual(scan["kind"], KIND)
        self.assertEqual(scan["contractVersion"], CONTRACT_VERSION)
        self.assertTrue(all(value is False for value in scan["effectFlags"].values()))
        self.assertEqual(set(scan["forbiddenEffects"]), set(FORBIDDEN_EFFECTS))
        self.assertEqual(set(scan["doesNotEstablish"]), set(DOES_NOT_ESTABLISH))

    def test_true_effect_flag_blocks_scan(self) -> None:
        scan = valid_scan()
        scan["effectFlags"]["taskCreated"] = True
        with self.assertRaisesRegex(GeminiMaintenanceScanError, "effectFlags"):
            validate_scan(scan)

    def test_observed_finding_without_evidence_ref_is_rejected(self) -> None:
        scan = valid_scan()
        scan["findings"]["observed"][0]["evidenceRefs"] = []
        with self.assertRaisesRegex(GeminiMaintenanceScanError, "observed.*evidenceRefs"):
            validate_scan(scan)

    def test_plausible_finding_may_have_empty_evidence_refs(self) -> None:
        scan = valid_scan()
        scan["findings"]["plausible"][0]["evidenceRefs"] = []
        validate_scan(scan)

    def test_missing_non_claim_blocks_scan(self) -> None:
        scan = valid_scan()
        scan["doesNotEstablish"] = ["claim_truth"]
        with self.assertRaisesRegex(GeminiMaintenanceScanError, "doesNotEstablish"):
            validate_scan(scan)

    def test_secret_request_flag_blocks_scan(self) -> None:
        scan = valid_scan()
        scan["effectFlags"]["secretRequested"] = True
        with self.assertRaisesRegex(GeminiMaintenanceScanError, "effectFlags"):
            validate_scan(scan)

    def test_load_scans_accepts_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gemini-scan.json"
            path.write_text(json.dumps(valid_scan(), sort_keys=True), encoding="utf-8")
            rows = load_scans(path)
        self.assertEqual(len(rows), 1)

    def test_load_scans_accepts_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gemini-scan.jsonl"
            path.write_text(json.dumps(valid_scan(), sort_keys=True) + "\n", encoding="utf-8")
            rows = load_scans(path)
        self.assertEqual(len(rows), 1)

    def test_validate_cli_reports_invalid_scan_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gemini-scan.json"
            scan = valid_scan()
            scan["source"]["inputRefs"] = ["AGENTS.md"]
            path.write_text(json.dumps(scan, sort_keys=True), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = validate_main(["--input", str(path), "--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("source.inputRefs", payload["error"])

    def test_schema_constants_match_validator(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["kind"]["const"], KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])
        self.assertEqual(set(properties["forbiddenEffects"]["items"]["enum"]), set(FORBIDDEN_EFFECTS))
        self.assertEqual(set(properties["doesNotEstablish"]["items"]["enum"]), set(DOES_NOT_ESTABLISH))


if __name__ == "__main__":
    unittest.main()
