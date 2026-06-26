from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-snapshot-review.py"


def load_review_module():
    spec = importlib.util.spec_from_file_location(
        "repository_snapshot_review_under_test", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository snapshot review generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def reference_text(
    repository: str,
    *,
    review_head: str = "1" * 40,
    import_head: str | None = None,
    relationship: str = "identisch",
    working_tree: str = "clean:0",
    imported_at: str = "2026-06-23T18:38:45+00:00",
) -> str:
    if import_head is None:
        import_head = review_head
    origin = f"github.com:heimgewebe/{repository}.git"
    canonical_path = f"/home/alex/repos/{repository}"
    return f"""# {repository} — Repository Reference

## Provenienz

| Feld | Wert |
|---|---|
| Import-Snapshot erfasst | `{imported_at}` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `{repository}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{review_head}` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `{imported_at}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{import_head}` |
| Working Tree | `{working_tree}` |
| Beziehung zum Review | **{relationship}** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `{canonical_path}` |
| Remote | `{origin}` |
| Default-Branch | `main` |

## Kanonische Systemrolle

> Testrolle
"""


class RepositorySnapshotReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @property
    def review_output(self) -> Path:
        return self.root / "pruefung/10 Laeufe/repository-snapshot-review-v1.md"

    @property
    def lage_output(self) -> Path:
        return self.root / "steuerung/10 Lage/repository-snapshots-v1.md"

    def write_reference(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "--", relative], check=True)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT_PATH), "--repo-root", str(self.root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )

    def seed_classification_matrix(self) -> None:
        self.write_reference(
            "refs/alpha/Repository Reference.md",
            reference_text("alpha"),
        )
        self.write_reference(
            "refs/beta/Repository Reference.md",
            reference_text("beta", working_tree="dirty:3"),
        )
        self.write_reference(
            "refs/gamma/Repository Reference.md",
            reference_text(
                "gamma",
                import_head="2" * 40,
                relationship="Live-Stand enthält Review-Stand",
            ),
        )
        self.write_reference(
            "refs/delta/Repository Reference.md",
            reference_text(
                "delta",
                import_head="3" * 40,
                relationship="divergent oder rewritten/amended",
            ),
        )

    def test_generates_deterministic_review_and_lage(self) -> None:
        self.seed_classification_matrix()

        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        review_before = self.review_output.read_bytes()
        lage_before = self.lage_output.read_bytes()
        review = review_before.decode("utf-8")
        lage = lage_before.decode("utf-8")

        self.assertIn("`snapshot-identical`", review)
        self.assertIn("`snapshot-dirty-at-import`", review)
        self.assertIn("`snapshot-review-contained`", review)
        self.assertIn("`snapshot-divergence-claimed`", review)
        self.assertIn("keine heutigen Repositoryzustände", review)
        self.assertIn("Aktueller Zustand der Quell-Repositories: **unbekannt**", lage)

        delta = lage.index("`delta`")
        beta = lage.index("`beta`")
        gamma = lage.index("`gamma`")
        alpha = lage.index("`alpha`")
        self.assertLess(delta, beta)
        self.assertLess(beta, gamma)
        self.assertLess(gamma, alpha)

        second = self.run_cli()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(review_before, self.review_output.read_bytes())
        self.assertEqual(lage_before, self.lage_output.read_bytes())

        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_check_mode_reports_stale_output_without_rewriting(self) -> None:
        self.write_reference(
            "refs/alpha/Repository Reference.md", reference_text("alpha")
        )
        self.assertEqual(self.run_cli().returncode, 0)
        self.review_output.write_text("stale\n", encoding="utf-8")
        before = self.review_output.read_bytes()

        checked = self.run_cli("--check")

        self.assertEqual(checked.returncode, 1, checked.stderr)
        self.assertIn("repository snapshot review is stale", checked.stderr)
        self.assertEqual(before, self.review_output.read_bytes())

    def test_check_mode_rejects_reference_drift_from_git_index(self) -> None:
        relative = "refs/alpha/Repository Reference.md"
        self.write_reference(relative, reference_text("alpha"))
        self.assertEqual(self.run_cli().returncode, 0)
        (self.root / relative).write_text(reference_text("beta"), encoding="utf-8")

        checked = self.run_cli("--check")

        self.assertEqual(checked.returncode, 2, checked.stderr)
        self.assertIn("tracked reference differs from git index", checked.stderr)

    def test_unknown_nonidentical_relationship_remains_a_claim(self) -> None:
        module = load_review_module()
        record = module.RepositoryRecord(
            repository="alpha",
            role="Testrolle",
            origin="github.com:heimgewebe/alpha.git",
            default_branch="main",
            review_head="1" * 40,
            import_head="2" * 40,
            relationship="anderer gespeicherter Stand",
            import_worktree="clean:0",
            imported_at="2026-06-23T18:38:45+00:00",
            source_path="refs/alpha/Repository Reference.md",
        )

        assessment = module.assess_record(record)

        self.assertEqual(
            assessment.relationship_class, "snapshot-relationship-claimed"
        )
        self.assertEqual(assessment.priority, 3)
        self.assertIn("reference-claim", assessment.evidence_status)

    def test_output_paths_must_remain_inside_repository(self) -> None:
        self.write_reference(
            "refs/alpha/Repository Reference.md", reference_text("alpha")
        )
        outside = self.root.parent / f"{self.root.name}-outside-review.md"
        outside.unlink(missing_ok=True)
        try:
            result = self.run_cli("--review-output", str(outside))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("output path escapes repository", result.stderr)
            self.assertFalse(outside.exists())
        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
