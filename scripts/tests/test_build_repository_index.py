from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"


def reference_text(
    repository: str,
    *,
    origin: str | None = None,
    review_head: str = "1" * 40,
    live_head: str = "2" * 40,
    working_tree: str = "clean:0",
    relationship: str = "identisch",
    imported_at: str = "2026-06-23T18:38:45+00:00",
    canonical_path: str | None = None,
    default_branch: str = "main",
) -> str:
    origin = origin or f"github.com:heimgewebe/{repository}.git"
    canonical_path = canonical_path or f"/home/alex/repos/{repository}"
    return f"""# {repository} — Repository Reference

> **Git bleibt die Source of Truth.**

## Provenienz

| Feld | Wert |
|---|---|
| Registry-ID | `registry` |
| Import-Snapshot erfasst | `{imported_at}` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `{repository}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| Branch | `main` |
| HEAD | `{review_head}` |
| Working Tree | `{working_tree}` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `{imported_at}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| Branch | `main` |
| HEAD | `{live_head}` |
| Working Tree | `{working_tree}` |
| Beziehung zum Review | **{relationship}** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `{canonical_path}` |
| Remote | `{origin}` |
| Default-Branch | `{default_branch}` |

## Kanonische Systemrolle

> Testrolle

## Belegter Zweck

> Testzweck

## Abgrenzung

- Test

## Import-Gate

**READY**

## Pflegevertrag

- Git bleibt kanonisch.
"""


class RepositoryInventoryCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.root)], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "config",
                "user.email",
                "test@example.invalid",
            ],
            check=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_reference(self, relative: str, content: str, *, track: bool = True) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if track:
            subprocess.run(
                ["git", "-C", str(self.root), "add", "--", relative], check=True
            )
        return path

    def commit(self) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True
        )

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(SCRIPT_PATH),
                "--repo-root",
                str(self.root),
                *args,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_generates_sorted_deterministic_index(self) -> None:
        self.write_reference(
            "z/Repository Reference.md", reference_text("zulu")
        )
        self.write_reference(
            "space dir/Repository Reference.md", reference_text("alpha")
        )
        self.commit()
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.root / "bestand/10 Repositories/index.md"
        first_bytes = output.read_bytes()
        text = first_bytes.decode("utf-8")
        self.assertLess(text.index("`alpha`"), text.index("`zulu`"))
        self.assertIn("space%20dir/Repository%20Reference.md", text)
        self.assertTrue(text.endswith("\n"))
        second = self.run_cli()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first_bytes, output.read_bytes())

    def test_check_passes_for_current_index(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        self.commit()
        self.assertEqual(self.run_cli().returncode, 0)
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_check_detects_stale_index_without_writing(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        self.commit()
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("stale\n", encoding="utf-8")
        before = output.read_bytes()
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("repository inventory is stale", checked.stderr)
        self.assertEqual(before, output.read_bytes())

    def test_untracked_reference_is_ignored(self) -> None:
        self.write_reference("tracked/Repository Reference.md", reference_text("alpha"))
        self.write_reference(
            "untracked/Repository Reference.md", reference_text("beta"), track=False
        )
        self.commit()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`alpha`", text)
        self.assertNotIn("`beta`", text)
        self.assertIn("Tracked references: **1**", text)

    def test_duplicate_repository_identity_fails(self) -> None:
        self.write_reference("one/Repository Reference.md", reference_text("alpha"))
        self.write_reference("two/Repository Reference.md", reference_text("ALPHA"))
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate repository identity", result.stderr)

    def test_missing_required_section_fails(self) -> None:
        content = reference_text("alpha").replace("## Pflegevertrag", "## Other")
        self.write_reference("room/Repository Reference.md", content)
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing required section", result.stderr)

    def test_missing_required_field_fails(self) -> None:
        content = reference_text("alpha").replace("| Repository | `alpha` |\n", "")
        self.write_reference("room/Repository Reference.md", content)
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("required field", result.stderr)

    def test_contradictory_origin_fails(self) -> None:
        content = reference_text("alpha").replace(
            "| Remote | `github.com:heimgewebe/alpha.git` |",
            "| Remote | `github.com:other/alpha.git` |",
        )
        self.write_reference("room/Repository Reference.md", content)
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("contradictory repository origin", result.stderr)

    def test_invalid_commit_and_working_tree_fail(self) -> None:
        self.write_reference(
            "room/Repository Reference.md",
            reference_text("alpha", review_head="abc", working_tree="unknown"),
        )
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid review HEAD", result.stderr)

    def test_no_references_is_a_contract_error(self) -> None:
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no tracked Repository Reference.md files found", result.stderr)


if __name__ == "__main__":
    unittest.main()
