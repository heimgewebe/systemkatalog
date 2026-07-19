import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "docs/audits/repository-lifecycle-classification-2026-07-19.v1.json"
MARKDOWN_PATH = ROOT / "docs/audits/repository-lifecycle-classification-2026-07-19.md"
INDEX_PATH = ROOT / "index.md"


def _audit() -> dict:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


class RepositoryLifecycleClassificationTests(unittest.TestCase):
    def test_repository_lifecycle_audit_shape_and_scope(self) -> None:
        audit = _audit()
        self.assertEqual(audit["schema_version"], 1)
        self.assertEqual(audit["authority"], "diagnostic_only")
        self.assertEqual(
            audit["organization"],
            {
                "repository_count": 35,
                "archived_repository_count": 0,
                "deep_review_repository_count": 5,
            },
        )
        expected = {
            "heimgewebe/heimlern",
            "heimgewebe/heimgeist",
            "heimgewebe/agent-control-surface",
            "heimgewebe/leitwerk",
            "heimgewebe/semantAH",
        }
        self.assertEqual(
            {item["repository"] for item in audit["classifications"]}, expected
        )

    def test_every_classification_binds_consumers_runtime_and_migration_gates(
        self,
    ) -> None:
        allowed_decisions = {
            "archive_candidate",
            "retain_during_consumer_migration",
            "keep_active",
        }
        for item in _audit()["classifications"]:
            with self.subTest(repository=item["repository"]):
                self.assertIn(item["lifecycle_decision"], allowed_decisions)
                self.assertTrue(item["consumer_evidence"])
                for evidence in item["consumer_evidence"]:
                    self.assertIn("source_ref", evidence)
                    self.assertTrue(
                        evidence["source_ref"].startswith(("repo.", "file:"))
                    )
                self.assertEqual(
                    item["runtime_evidence"]["scope"],
                    "heim-pc user session at observed_at",
                )
                self.assertIn("systemd_user_units", item["runtime_evidence"])
                self.assertIn("processes", item["runtime_evidence"])
                self.assertTrue(item["migration_preconditions"])
                self.assertEqual(len(item["last_main_commit"]), 40)
                self.assertEqual(item["open_pull_requests"], 0)

    def test_archive_candidates_have_resource_specific_followups(self) -> None:
        audit = _audit()
        archive_candidates = {
            item["repository"]: item["follow_up_task"]
            for item in audit["classifications"]
            if item["lifecycle_decision"] == "archive_candidate"
        }
        self.assertEqual(
            archive_candidates,
            {
                "heimgewebe/heimlern": "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T036",
                "heimgewebe/leitwerk": "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T037",
            },
        )

    def test_non_archive_candidates_do_not_create_duplicate_work(self) -> None:
        audit = _audit()
        by_repo = {item["repository"]: item for item in audit["classifications"]}
        for repo in (
            "heimgewebe/heimgeist",
            "heimgewebe/agent-control-surface",
            "heimgewebe/semantAH",
        ):
            with self.subTest(repository=repo):
                self.assertIsNone(by_repo[repo]["follow_up_task"])
                self.assertEqual(
                    by_repo[repo]["covered_by_existing_task"],
                    "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T034",
                )

    def test_dependabot_queue_is_not_repository_retirement_evidence(self) -> None:
        queue = _audit()["dependabot_queue"]
        self.assertIs(queue["does_not_establish_repository_retirement"], True)
        counts = {
            item["repository"]: item.get("open_stale_pr_count")
            for item in queue["repositories"]
            if "open_stale_pr_count" in item
        }
        self.assertEqual(
            counts,
            {
                "heimgewebe/hausKI": 15,
                "heimgewebe/hausKI-audio": 7,
            },
        )
        self.assertEqual(
            queue["follow_up_task"],
            "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T038",
        )

    def test_human_audit_and_index_expose_decisions(self) -> None:
        markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
        index = INDEX_PATH.read_text(encoding="utf-8")
        for task_id in (
            "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T036",
            "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T037",
            "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T038",
        ):
            self.assertIn(task_id, markdown)
        self.assertIn("Repository-Lifecycle-Audit 2026-07-19", index)


if __name__ == "__main__":
    unittest.main()
