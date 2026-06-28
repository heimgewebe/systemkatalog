from __future__ import annotations

import copy
import unittest

import finding_model
from finding_fixture import base_finding


class FindingEvidenceTests(unittest.TestCase):
    def test_fingerprint_rejects_identity_drift(self) -> None:
        value = base_finding()
        value["subject"]["id"] = "infra"  # type: ignore[index]
        with self.assertRaisesRegex(finding_model.FindingError, "fingerprint mismatch"):
            finding_model.validate_finding(value)

    def test_fingerprint_stays_stable_for_volatile_changes(self) -> None:
        first = base_finding()
        second = copy.deepcopy(first)
        second["severity"] = "high"
        second["confidence"] = "medium"
        second["summary"] = "Updated wording"
        second["observation"] = {
            "expected": "branch",
            "actual": "detached at another commit",
        }
        second["observed_at"] = "2026-06-28T01:00:00Z"
        second["evidence"] = []
        self.assertEqual(
            finding_model.compute_fingerprint(first),
            finding_model.compute_fingerprint(second),
        )

    def test_fingerprint_changes_for_expectation_identity(self) -> None:
        first = base_finding()
        second = copy.deepcopy(first)
        second["expectation_code"] = "repository-head-equals-main"
        self.assertNotEqual(
            finding_model.compute_fingerprint(first),
            finding_model.compute_fingerprint(second),
        )

    def test_git_commit_evidence_requires_git_oid(self) -> None:
        value = base_finding()
        item = value["evidence"][0]  # type: ignore[index]
        item["type"] = "git_commit"
        with self.assertRaisesRegex(finding_model.FindingError, "must be git-oid"):
            finding_model.validate_finding(value)

    def test_runtime_evidence_requires_sha256(self) -> None:
        value = base_finding()
        item = value["evidence"][0]  # type: ignore[index]
        item["type"] = "runtime_output"
        item["digest"] = {"algorithm": "git-oid", "value": "a" * 40}
        with self.assertRaisesRegex(finding_model.FindingError, "must be sha256"):
            finding_model.validate_finding(value)

    def test_evidence_requires_canonical_sort_order(self) -> None:
        value = base_finding()
        first = value["evidence"][0]  # type: ignore[index]
        second = copy.deepcopy(first)
        second["source"] = "aaa"
        value["evidence"] = [first, second]
        with self.assertRaisesRegex(finding_model.FindingError, "canonical sort order"):
            finding_model.validate_finding(value)

    def test_duplicate_evidence_fails(self) -> None:
        value = base_finding()
        item = value["evidence"][0]  # type: ignore[index]
        value["evidence"] = [item, item]
        with self.assertRaisesRegex(finding_model.FindingError, "duplicates"):
            finding_model.validate_finding(value)

    def test_timestamp_requires_canonical_utc(self) -> None:
        value = base_finding()
        value["observed_at"] = "2026-06-28T02:00:00+02:00"
        with self.assertRaisesRegex(finding_model.FindingError, "Z suffix"):
            finding_model.validate_finding(value)

    def test_confirmation_cannot_precede_evidence(self) -> None:
        value = base_finding(confirmed=True)
        value["confirmation"]["confirmed_at"] = "2026-06-27T23:59:59Z"  # type: ignore[index]
        with self.assertRaisesRegex(finding_model.FindingError, "precedes observed_at"):
            finding_model.validate_finding(value)

    def test_path_scope_rejects_parent_component(self) -> None:
        value = base_finding()
        value["scope"] = {"kind": "path", "value": "../secrets"}
        with self.assertRaisesRegex(finding_model.FindingError, "invalid identifier"):
            finding_model.compute_fingerprint(value)


if __name__ == "__main__":
    unittest.main()
