from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-snapshot-review.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "snapshot_review_model_hardening_under_test",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load snapshot review generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def record(module, relationship: str, *, imported_at: str = "2026-06-23T18:38:45+00:00", relationship_verification: str | None = None):
    return module.RepositoryRecord(
        repository="alpha",
        role="Testrolle",
        origin="github.com:heimgewebe/alpha.git",
        default_branch="main",
        review_head="1" * 40,
        import_head="2" * 40,
        relationship=relationship,
        import_worktree="clean:0",
        imported_at=imported_at,
        source_path="refs/alpha/Repository Reference.md",
        relationship_verification=relationship_verification,
    )


class SnapshotReviewModelHardeningTests(unittest.TestCase):
    def test_negated_relationship_words_remain_generic_claims(self) -> None:
        module = load_generator()
        for relationship in (
            "nicht divergent",
            "enthält den Reviewstand nicht",
            "anderer gespeicherter Stand",
        ):
            with self.subTest(relationship=relationship):
                assessment = module.assess_record(record(module, relationship))
                self.assertEqual(
                    assessment.relationship_class,
                    "snapshot-relationship-claimed",
                )
                self.assertEqual(assessment.evidence_status, "reference-claim")
                self.assertEqual(assessment.priority, 3)

    def test_live_verified_divergence_becomes_routine(self) -> None:
        module = load_generator()
        assessment = module.assess_record(
            record(module, "divergent oder rewritten/amended", relationship_verification="live-verified")
        )
        self.assertEqual(assessment.priority, 4)
        self.assertEqual(assessment.reason_code, "routine")

    def test_exact_relationship_value_is_whitespace_normalized(self) -> None:
        module = load_generator()
        assessment = module.assess_record(
            record(module, "  LIVE-STAND   ENTHÄLT REVIEW-STAND  ")
        )
        self.assertEqual(
            assessment.relationship_class,
            "snapshot-review-contained",
        )
        self.assertEqual(assessment.priority, 4)
        self.assertEqual(assessment.reason_code, "routine")


    def test_generic_nonidentical_relationship_remains_candidate(self) -> None:
        module = load_generator()
        assessment = module.assess_record(
            record(module, "anderer gespeicherter Stand")
        )
        self.assertEqual(assessment.priority, 3)
        self.assertEqual(assessment.reason_code, "verify-nonidentical")

    def test_detailed_review_keeps_full_commit_ids(self) -> None:
        module = load_generator()
        item = module.assess_record(
            record(module, "Live-Stand enthält Review-Stand")
        )
        review = module.render_review([item])
        self.assertIn("`" + "1" * 40 + "`", review)
        self.assertIn("`" + "2" * 40 + "`", review)
        self.assertIn("indexidentische Reference-Bytes", review)

    def test_multiple_snapshot_times_are_sorted(self) -> None:
        module = load_generator()
        later = module.assess_record(
            record(
                module,
                "Live-Stand enthält Review-Stand",
                imported_at="2026-06-24T00:00:00+00:00",
            )
        )
        earlier = module.assess_record(
            record(
                module,
                "Live-Stand enthält Review-Stand",
                imported_at="2026-06-22T00:00:00+00:00",
            )
        )
        review = module.render_review([later, earlier])
        self.assertLess(
            review.index("`2026-06-22T00:00:00+00:00`"),
            review.index("`2026-06-24T00:00:00+00:00`"),
        )


if __name__ == "__main__":
    unittest.main()
