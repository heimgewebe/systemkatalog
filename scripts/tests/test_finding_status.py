from __future__ import annotations

import unittest

import finding_model
from finding_fixture import base_finding


class FindingStatusTests(unittest.TestCase):
    def test_json_parser_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(finding_model.FindingError, "duplicate JSON key"):
            finding_model.parse_json_text('{"schema": 1, "schema": 2}', "fixture")

    def test_json_parser_rejects_nan(self) -> None:
        with self.assertRaisesRegex(finding_model.FindingError, "non-JSON numeric"):
            finding_model.parse_json_text('{"value": NaN}', "fixture")

    def test_hint_with_evidence_passes(self) -> None:
        validated = finding_model.validate_finding(base_finding())
        self.assertEqual(validated["status"], "hint")

    def test_hint_without_evidence_passes(self) -> None:
        validated = finding_model.validate_finding(base_finding(evidence=False))
        self.assertEqual(validated["evidence"], [])

    def test_confirmed_requires_evidence(self) -> None:
        value = base_finding(confirmed=True, evidence=False)
        with self.assertRaisesRegex(finding_model.FindingError, "at least one evidence"):
            finding_model.validate_finding(value)

    def test_confirmed_requires_human_declaration(self) -> None:
        value = base_finding(confirmed=True)
        value["confirmation"]["actor_type"] = "agent"  # type: ignore[index]
        with self.assertRaisesRegex(finding_model.FindingError, "must be human"):
            finding_model.validate_finding(value)

    def test_hint_cannot_carry_confirmation(self) -> None:
        value = base_finding()
        value["confirmation"] = {
            "actor_type": "human",
            "actor_id": "alex",
            "confirmed_at": "2026-06-28T00:01:00Z",
            "method": "human-review",
        }
        with self.assertRaisesRegex(finding_model.FindingError, "confirmation=null"):
            finding_model.validate_finding(value)


if __name__ == "__main__":
    unittest.main()
