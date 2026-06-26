from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-snapshot-review.py"


def reference_text(repository: str) -> str:
    timestamp = "2026-06-23T18:38:45+00:00"
    origin = f"github.com:heimgewebe/{repository}.git"
    path = f"/home/alex/repos/{repository}"
    head = "1" * 40
    return f"""# {repository} — Repository Reference

## Provenienz

| Feld | Wert |
|---|---|
| Import-Snapshot erfasst | `{timestamp}` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `{repository}` |
| Pfad | `{path}` |
| Origin | `{origin}` |
| HEAD | `{head}` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `{timestamp}` |
| Pfad | `{path}` |
| Origin | `{origin}` |
| HEAD | `{head}` |
| Working Tree | `clean:0` |
| Beziehung zum Review | **identisch** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `{path}` |
| Remote | `{origin}` |
| Default-Branch | `main` |

## Kanonische Systemrolle

> Testrolle
"""


class SnapshotReviewIoHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        self.relative = "refs/alpha/Repository Reference.md"
        self.reference = self.root / self.relative
        self.reference.parent.mkdir(parents=True)
        self.reference.write_text(reference_text("alpha"), encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", self.relative],
            check=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @property
    def review_output(self) -> Path:
        return self.root / "pruefung/10 Laeufe/repository-snapshot-review-v1.md"

    @property
    def lage_output(self) -> Path:
        return self.root / "steuerung/10 Lage/repository-snapshots-v1.md"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT_PATH), "--repo-root", str(self.root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )

    def test_write_mode_rejects_unstaged_reference_drift(self) -> None:
        self.reference.write_text(reference_text("beta"), encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("tracked reference differs from git index", result.stderr)
        self.assertFalse(self.review_output.exists())
        self.assertFalse(self.lage_output.exists())

    def test_identical_output_paths_are_rejected(self) -> None:
        result = self.run_cli(
            "--review-output",
            "same.md",
            "--lage-output",
            "same.md",
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("outputs must be distinct", result.stderr)
        self.assertFalse((self.root / "same.md").exists())

    def test_reference_cannot_be_used_as_output(self) -> None:
        before = self.reference.read_bytes()
        result = self.run_cli("--review-output", self.relative)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("collides with a Repository Reference", result.stderr)
        self.assertEqual(before, self.reference.read_bytes())

    def test_other_tracked_input_cannot_be_used_as_output(self) -> None:
        tracked = self.root / "tracked.md"
        tracked.write_text("tracked input\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", "tracked.md"],
            check=True,
        )
        result = self.run_cli("--review-output", "tracked.md")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("may not overwrite a tracked input", result.stderr)
        self.assertEqual(tracked.read_text(encoding="utf-8"), "tracked input\n")

    def test_stale_lage_is_reported_without_rewriting(self) -> None:
        self.assertEqual(self.run_cli().returncode, 0)
        self.lage_output.write_text("stale\n", encoding="utf-8")
        before = self.lage_output.read_bytes()
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 1, checked.stderr)
        self.assertIn("steuerung/10 Lage", checked.stderr)
        self.assertEqual(before, self.lage_output.read_bytes())

    def test_missing_review_is_reported(self) -> None:
        self.assertEqual(self.run_cli().returncode, 0)
        self.review_output.unlink()
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 1, checked.stderr)
        self.assertIn("pruefung/10 Laeufe", checked.stderr)


if __name__ == "__main__":
    unittest.main()
