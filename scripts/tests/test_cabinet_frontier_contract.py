"""Tests for the Cabinet Frontier contract and producer."""

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

from validate_cabinet_frontier import (  # noqa: E402
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    FORBIDDEN_EFFECTS,
    KIND,
    SCHEMA_PATH,
    CabinetFrontierError,
    load_candidates,
    main as validate_main,
    validate_candidate,
)
from write_cabinet_frontier import (  # noqa: E402
    build_frontier_candidates,
    candidate_from_bureau_candidate,
    main as write_main,
)


def maintenance_report() -> dict[str, Any]:
    return {
        "source": {
            "repository": "heimgewebe/heimgewebe-katalog",
            "commit": "a" * 40,
        },
        "summary": {
            "status": "pass",
        },
        "bureauCandidates": [
            {
                "id": "claim:cabinet-qa-radar-cab-qa-001-v0",
                "status": "evidenced",
                "evidence": ["docs/contracts/cabinet-maintenance-report-v1.md"],
                "expiresAtOrRefreshHint": "2026-08-04",
                "nextAction": "run_cabinet_maintenance_report_before_bureau_task_creation",
                "responsibleOrgan": "cabinet",
            }
        ],
    }


def signals() -> list[dict[str, Any]]:
    return [
        {
            "id": "signal:local_git:cabinet:maintenance-report:status:pass:aaaaaaaaaaaa",
            "kind": "cabinet_ecosystem_signal",
        }
    ]


def valid_candidate() -> dict[str, Any]:
    return candidate_from_bureau_candidate(
        maintenance_report()["bureauCandidates"][0],
        report=maintenance_report(),
        signals=signals(),
        created_at="2026-07-08T04:00:00Z",
    )


class CabinetFrontierContractTests(unittest.TestCase):
    def test_candidate_from_bureau_candidate_is_valid_and_has_no_effects(self) -> None:
        candidate = valid_candidate()
        validate_candidate(candidate)
        self.assertEqual(candidate["kind"], KIND)
        self.assertEqual(candidate["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(candidate["contractPath"], CONTRACT_PATH)
        self.assertEqual(candidate["schemaPath"], SCHEMA_PATH)
        self.assertEqual(set(candidate["forbiddenEffects"]), set(FORBIDDEN_EFFECTS))
        self.assertTrue(all(value is False for value in candidate["effectFlags"].values()))
        self.assertEqual(set(candidate["doesNotEstablish"]), set(DOES_NOT_ESTABLISH))

    def test_build_frontier_candidates_translates_report_candidates(self) -> None:
        rows = build_frontier_candidates(maintenance_report(), signals(), created_at="2026-07-08T04:00:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target"]["repository"], "heimgewebe/heimgewebe-katalog")
        self.assertEqual(rows[0]["proposal"]["priorityHint"], "later")

    def test_effect_flag_true_blocks_candidate(self) -> None:
        candidate = valid_candidate()
        candidate["effectFlags"]["taskCreationAllowed"] = True
        with self.assertRaisesRegex(CabinetFrontierError, "effectFlags"):
            validate_candidate(candidate)

    def test_missing_acceptance_blocks_candidate(self) -> None:
        candidate = valid_candidate()
        candidate["acceptance"] = []
        with self.assertRaisesRegex(CabinetFrontierError, "acceptance"):
            validate_candidate(candidate)

    def test_load_candidates_accepts_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frontier.jsonl"
            path.write_text(json.dumps(valid_candidate(), sort_keys=True) + "\n", encoding="utf-8")
            rows = load_candidates(path)
        self.assertEqual(len(rows), 1)

    def test_validate_cli_reports_invalid_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frontier.jsonl"
            candidate = valid_candidate()
            candidate["doesNotEstablish"] = ["claim_truth"]
            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = validate_main(["--input", str(path), "--json"])
        self.assertEqual(rc, 1)
        self.assertFalse(json.loads(stdout.getvalue())["ok"])

    def test_validate_cli_reports_non_string_list_items_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frontier.jsonl"
            candidate = valid_candidate()
            candidate["forbiddenEffects"] = ["bureau_task_creation", {"bad": "item"}]
            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc = validate_main(["--input", str(path), "--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("forbiddenEffects item 2", payload["error"])

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

    def test_writer_check_does_not_write_output(self) -> None:
        output = ROOT / "pruefung/10 Laeufe/test-cabinet-frontier-check.jsonl"
        output.unlink(missing_ok=True)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = write_main([
                "--repo-root",
                str(ROOT),
                "--output",
                str(output.relative_to(ROOT)),
                "--check",
                "--created-at",
                "2026-07-08T04:00:00Z",
            ])
        self.assertEqual(rc, 0)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
