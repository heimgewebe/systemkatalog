from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"
SPEC = importlib.util.spec_from_file_location("build_repository_index", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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


class RepositoryInventoryTests(unittest.TestCase):
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

    def test_parses_valid_reference(self) -> None:
        relative = "room/Repository Reference.md"
        self.write_reference(relative, reference_text("alpha"))
        record = MODULE.parse_reference(self.root, relative)
        self.assertEqual(record.repository, "alpha")
        self.assertEqual(record.origin, "github.com:heimgewebe/alpha.git")
        self.assertEqual(record.relationship, "identisch")

    def test_discovery_uses_only_tracked_references(self) -> None:
        self.write_reference("tracked/Repository Reference.md", reference_text("alpha"))
        self.write_reference(
            "untracked/Repository Reference.md", reference_text("beta"), track=False
        )
        paths = MODULE.tracked_reference_paths(self.root)
        self.assertEqual(paths, ["tracked/Repository Reference.md"])

    def test_duplicate_repository_identity_fails(self) -> None:
        self.write_reference("one/Repository Reference.md", reference_text("alpha"))
        self.write_reference("two/Repository Reference.md", reference_text("ALPHA"))
        with self.assertRaisesRegex(MODULE.InventoryError, "duplicate repository identity"):
            MODULE.load_records(self.root)

    def test_missing_required_section_fails(self) -> None:
        relative = "room/Repository Reference.md"
        content = reference_text("alpha").replace("## Pflegevertrag", "## Other")
        self.write_reference(relative, content)
        with self.assertRaisesRegex(MODULE.InventoryError, "missing required section"):
            MODULE.parse_reference(self.root, relative)

    def test_missing_required_field_fails(self) -> None:
        relative = "room/Repository Reference.md"
        content = reference_text("alpha").replace("| Repository | `alpha` |\n", "")
        self.write_reference(relative, content)
        with self.assertRaisesRegex(MODULE.InventoryError, "required field"):
            MODULE.parse_reference(self.root, relative)

    def test_contradictory_origin_fails(self) -> None:
        relative = "room/Repository Reference.md"
        content = reference_text("alpha").replace(
            "| Remote | `github.com:heimgewebe/alpha.git` |",
            "| Remote | `github.com:other/alpha.git` |",
        )
        self.write_reference(relative, content)
        with self.assertRaisesRegex(MODULE.InventoryError, "contradictory repository origin"):
            MODULE.parse_reference(self.root, relative)

    def test_invalid_commit_fails(self) -> None:
        relative = "room/Repository Reference.md"
        self.write_reference(relative, reference_text("alpha", review_head="abc"))
        with self.assertRaisesRegex(MODULE.InventoryError, "invalid review HEAD"):
            MODULE.parse_reference(self.root, relative)

    def test_invalid_working_tree_fails(self) -> None:
        relative = "room/Repository Reference.md"
        self.write_reference(relative, reference_text("alpha", working_tree="unknown"))
        with self.assertRaisesRegex(MODULE.InventoryError, "invalid live Working Tree"):
            MODULE.parse_reference(self.root, relative)

    def test_render_is_deterministic_and_sorted(self) -> None:
        first = MODULE.RepositoryRecord(
            repository="Zulu",
            origin="github.com:heimgewebe/zulu.git",
            default_branch="main",
            review_head="1" * 40,
            live_head="2" * 40,
            relationship="identisch",
            working_tree="clean:0",
            imported_at="2026-06-23T18:38:45+00:00",
            source_path="z/Repository Reference.md",
        )
        second = MODULE.RepositoryRecord(
            repository="Äther",
            origin="github.com:heimgewebe/aether.git",
            default_branch="main",
            review_head="3" * 40,
            live_head="4" * 40,
            relationship="identisch",
            working_tree="clean:0",
            imported_at="2026-06-23T18:38:45+00:00",
            source_path="space dir/Repository Reference.md",
        )
        records = sorted(
            [first, second],
            key=lambda record: (record.repository.casefold(), record.repository),
        )
        one = MODULE.render_index(records, Path("bestand/10 Repositories/index.md"))
        two = MODULE.render_index(records, Path("bestand/10 Repositories/index.md"))
        self.assertEqual(one, two)
        self.assertTrue(one.endswith("\n"))
        self.assertIn("space%20dir/Repository%20Reference.md", one)
        self.assertNotIn(str(self.root), one)

    def test_default_write_is_idempotent_and_check_passes(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        self.commit()
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.root / "bestand/10 Repositories/index.md"
        first_bytes = output.read_bytes()
        second = self.run_cli()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(output.read_bytes(), first_bytes)
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_check_detects_stale_output_without_writing(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        self.commit()
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("stale\n", encoding="utf-8")
        before = output.read_bytes()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("repository inventory is stale", result.stderr)
        self.assertEqual(output.read_bytes(), before)

    def test_no_references_is_a_contract_error(self) -> None:
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no tracked Repository Reference.md files found", result.stderr)


if __name__ == "__main__":
    unittest.main()
