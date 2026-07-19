import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure scripts can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.apply_catalog_proposal import apply_proposal


def create_workspace(root):
    registry_dir = root / "registry" / "ecosystem"
    registry_dir.mkdir(parents=True)

    bindings = {
        "schemaVersion": 1,
        "observedAt": "2026-07-19T10:00:00Z",
        "systems": [
            {
                "system": "repo:systemkatalog",
                "source": {
                    "repository": "heimgewebe/systemkatalog",
                    "commit": "1111111111111111111111111111111111111111",
                    "locator": {
                        "kind": "file",
                        "path": "README.md",
                        "contentSha256": "2222222222222222222222222222222222222222222222222222222222222222",
                    },
                },
                "reviewedAt": "2020-01-01T00:00:00Z",
            }
        ],
    }

    bindings_path = registry_dir / "source-bindings.v1.json"
    bindings_path.write_text(json.dumps(bindings))


def create_report_review(root, report_data, review_data):
    report_path = root / "report.json"
    review_path = root / "review.json"

    report_bytes = json.dumps(report_data).encode("utf-8")
    report_path.write_bytes(report_bytes)
    report_sha = hashlib.sha256(report_bytes).hexdigest()

    if review_data is not None:
        if "reportSha256" not in review_data or review_data["reportSha256"] == "AUTO":
            review_data["reportSha256"] = report_sha
        review_bytes = json.dumps(review_data).encode("utf-8")
        review_path.write_bytes(review_bytes)
        review_sha = hashlib.sha256(review_bytes).hexdigest()
    else:
        review_sha = None

    return report_path, review_path, report_sha, review_sha


def valid_report():
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_drift_report",
        "generatedAt": "2026-07-20T10:00:00Z",
        "materialDrift": True,
        "changeCount": 1,
        "changes": [
            {
                "kind": "primary_source_changed",
                "system": "repo:systemkatalog",
                "repository": "heimgewebe/systemkatalog",
                "locatorKind": "file",
                "path": "README.md",
                "boundCommit": "1111111111111111111111111111111111111111",
                "boundSha256": "2222222222222222222222222222222222222222222222222222222222222222",
                "observedCommit": "3333333333333333333333333333333333333333",
                "observedSha256": "4444444444444444444444444444444444444444444444444444444444444444",
            }
        ],
        "bureauCandidate": {},
        "proposal": {},
        "doesNotEstablish": ["semantic_change", "merge", "deploy", "claim_truth"],
    }


def valid_review():
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_source_binding_review",
        "decision": "approved_source_binding_refresh",
        "reviewedAt": "2026-07-20T11:00:00Z",
        "reportSha256": "AUTO",
        "approvedChanges": [
            {
                "repository": "heimgewebe/systemkatalog",
                "system": "repo:systemkatalog",
                "locatorKind": "file",
                "path": "README.md",
                "boundCommit": "1111111111111111111111111111111111111111",
                "boundSha256": "2222222222222222222222222222222222222222222222222222222222222222",
                "observedCommit": "3333333333333333333333333333333333333333",
                "observedSha256": "4444444444444444444444444444444444444444444444444444444444444444",
            }
        ],
        "doesNotEstablish": ["semantic_change", "merge", "deploy", "claim_truth"],
    }


class ApplyCatalogProposalTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary_directory.name)
        create_workspace(self.workspace)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_success_explicit_write(self):
        rep, rev, rep_sha, rev_sha = create_report_review(
            self.workspace, valid_report(), valid_review()
        )
        self.assertEqual(
            apply_proposal(self.workspace, rep, rev, rep_sha, rev_sha, True), 0
        )
        bindings = json.loads(
            (self.workspace / "registry/ecosystem/source-bindings.v1.json").read_text()
        )
        system = bindings["systems"][0]
        self.assertEqual(
            system["source"]["commit"], "3333333333333333333333333333333333333333"
        )
        self.assertEqual(system["reviewedAt"], "2026-07-20T11:00:00Z")
        self.assertEqual(bindings["observedAt"], "2026-07-20T10:00:00Z")

    def test_default_dry_run(self):
        rep, rev, rep_sha, rev_sha = create_report_review(
            self.workspace, valid_report(), valid_review()
        )
        self.assertEqual(
            apply_proposal(self.workspace, rep, rev, rep_sha, rev_sha, False), 0
        )
        bindings = json.loads(
            (self.workspace / "registry/ecosystem/source-bindings.v1.json").read_text()
        )
        system = bindings["systems"][0]
        self.assertEqual(
            system["source"]["commit"], "1111111111111111111111111111111111111111"
        )
        self.assertEqual(bindings["observedAt"], "2026-07-19T10:00:00Z")

    def test_stale_binding(self):
        report = valid_report()
        report["changes"][0]["boundCommit"] = "9999999999999999999999999999999999999999"
        self.assert_rejected(report, valid_review())

    def test_tampered_report_hash_mismatch(self):
        rep, rev, rep_sha, rev_sha = create_report_review(
            self.workspace, valid_report(), valid_review()
        )
        rep.write_text(json.dumps({"kind": "system_catalog_drift_report", "changes": []}))
        self.assertEqual(
            apply_proposal(self.workspace, rep, rev, rep_sha, rev_sha, True), 1
        )

    def test_tampered_review_hash_mismatch(self):
        rep, rev, rep_sha, rev_sha = create_report_review(
            self.workspace, valid_report(), valid_review()
        )
        rev.write_text(json.dumps({"kind": "tampered"}))
        self.assertEqual(
            apply_proposal(self.workspace, rep, rev, rep_sha, rev_sha, True), 1
        )

    def test_tampered_review_unknown_field(self):
        review = valid_review()
        review["evil"] = "field"
        self.assert_rejected(valid_report(), review)

    def test_report_unknown_field(self):
        report = valid_report()
        report["evil"] = "field"
        self.assert_rejected(report, valid_review())

    def test_malformed_hash(self):
        review = valid_review()
        review["approvedChanges"][0]["observedCommit"] = "not-a-hash"
        self.assert_rejected(valid_report(), review)

    def test_duplicate_report_changes(self):
        report = valid_report()
        report["changes"].append(report["changes"][0].copy())
        report["changeCount"] = 2
        self.assert_rejected(report, valid_review())

    def test_extra_review_change(self):
        review = valid_review()
        extra_change = review["approvedChanges"][0].copy()
        extra_change["system"] = "repo:other"
        review["approvedChanges"].append(extra_change)
        self.assert_rejected(valid_report(), review)

    def test_unsupported_kind(self):
        report = valid_report()
        report["changes"][0]["kind"] = "unsupported_kind"
        self.assert_rejected(report, valid_review())

    def test_wrong_change_count(self):
        report = valid_report()
        report["changeCount"] = 99
        self.assert_rejected(report, valid_review())

    def test_missing_does_not_establish(self):
        review = valid_review()
        review["doesNotEstablish"] = ["semantic_change"]
        self.assert_rejected(valid_report(), review)

    def test_locator_mismatch(self):
        review = valid_review()
        review["approvedChanges"][0]["locatorKind"] = "json_pointer"
        self.assert_rejected(valid_report(), review)

    def test_repository_mismatch(self):
        review = valid_review()
        review["approvedChanges"][0]["repository"] = "wrong/repo"
        self.assert_rejected(valid_report(), review)

    def test_partial_effect_free_on_error(self):
        report = valid_report()
        report["changes"][0]["observedSha256"] = "wrong-hash"
        self.assert_rejected(report, valid_review())
        bindings = json.loads(
            (self.workspace / "registry/ecosystem/source-bindings.v1.json").read_text()
        )
        system = bindings["systems"][0]
        self.assertEqual(
            system["source"]["commit"], "1111111111111111111111111111111111111111"
        )

    def assert_rejected(self, report, review):
        rep, rev, rep_sha, rev_sha = create_report_review(
            self.workspace, report, review
        )
        self.assertEqual(
            apply_proposal(self.workspace, rep, rev, rep_sha, rev_sha, True), 1
        )


if __name__ == "__main__":
    unittest.main()
