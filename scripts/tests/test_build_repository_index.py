from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"


def reference_text(
    repository: str,
    *,
    review_head: str = "1" * 40,
    import_head: str | None = None,
    role: str | None = "Testrolle",
    relationship: str = "identisch",
    working_tree: str = "clean:0",
    imported_at: str = "2026-06-23T18:38:45+00:00",
    captured_at: str | None = None,
    separator: str = "|---|---|",
) -> str:
    if import_head is None:
        import_head = review_head
    if captured_at is None:
        captured_at = imported_at
    origin = f"github.com:heimgewebe/{repository}.git"
    canonical_path = f"fixtures/{repository}"
    role_section = (
        f"\n## Kanonische Systemrolle\n\n> {role}\n" if role is not None else ""
    )
    return f"""# {repository} — Repository Reference

## Provenienz

| Feld | Wert |
{separator}
| Import-Snapshot erfasst | `{imported_at}` |

## Geprüfter Review-Snapshot

| Feld | Wert |
{separator}
| Repository | `{repository}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{review_head}` |

## Live-Snapshot beim Import

| Feld | Wert |
{separator}
| Erfasst | `{captured_at}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{import_head}` |
| Working Tree | `{working_tree}` |
| Beziehung zum Review | **{relationship}** |

## Identität

| Feld | Wert |
{separator}
| Kanonischer Pfad | `{canonical_path}` |
| Remote | `{origin}` |
| Default-Branch | `main` |
{role_section}
"""


class RepositoryInventoryCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_reference(self, relative: str, content: str, *, track: bool = True) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if track:
            subprocess.run(["git", "-C", str(self.root), "add", "--", relative], check=True)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT_PATH), "--repo-root", str(self.root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def assert_contract_error(self, content: str, expected: str) -> None:
        self.write_reference("room/Repository Reference.md", content)
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(expected, result.stderr)

    def test_role_excerpt_hashes_and_snapshot_time_are_deterministic(self) -> None:
        long_role = "A deliberately long repository role that remains fully visible"
        self.write_reference(
            "z/Repository Reference.md", reference_text("zulu", role=long_role)
        )
        self.write_reference("space dir/Repository Reference.md", reference_text("alpha"))
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.root / "bestand/10 Repositories/index.md"
        before = output.read_bytes()
        text = before.decode("utf-8")
        self.assertLess(text.index("`alpha`"), text.index("`zulu`"))
        self.assertIn(
            "| Repository | Rollen-Auszug | Review-HEAD | Import-HEAD |", text
        )
        self.assertIn("datierte Import-Snapshots", text)
        self.assertIn("`2026-06-23T18:38:45+00:00`", text)
        self.assertIn("`111111111111`", text)
        self.assertNotIn("`" + "1" * 40 + "`", text)
        self.assertIn("A deliberately long repository role ...", text)
        self.assertNotIn(long_role, text)
        self.assertIn("`space dir/Repository Reference.md`", text)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(before, output.read_bytes())

    def test_tracked_only_and_check_mode(self) -> None:
        self.write_reference("tracked/Repository Reference.md", reference_text("alpha"))
        self.write_reference(
            "untracked/Repository Reference.md", reference_text("beta"), track=False
        )
        self.assertEqual(self.run_cli().returncode, 0)
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`alpha`", text)
        self.assertNotIn("`beta`", text)

    def test_optional_role_warns_but_builds(self) -> None:
        self.write_reference(
            "room/Repository Reference.md", reference_text("alpha", role=None)
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("optional role missing", result.stderr)

    def test_unconsumed_sections_are_not_required(self) -> None:
        content = reference_text("alpha")
        self.assertNotIn("## Pflegevertrag", content)
        self.write_reference("room/Repository Reference.md", content)
        built = self.run_cli()
        self.assertEqual(built.returncode, 0, built.stderr)
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_duplicate_repository_identity_fails(self) -> None:
        self.write_reference("one/Repository Reference.md", reference_text("alpha"))
        self.write_reference("two/Repository Reference.md", reference_text("ALPHA"))
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate repository identity", result.stderr)

    def test_missing_required_section_fails(self) -> None:
        content = reference_text("alpha").replace("## Identität", "## Other")
        self.assert_contract_error(content, "missing required section")

    def test_stale_index_is_not_rewritten(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("stale\n", encoding="utf-8")
        before = output.read_bytes()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(before, output.read_bytes())

    def test_no_references_is_a_contract_error(self) -> None:
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no tracked Repository Reference.md files found", result.stderr)

    def test_identical_relationship_requires_identical_heads(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", import_head="2" * 40),
            "relationship 'identisch' contradicts differing HEADs",
        )

    def test_divergent_relationship_rejects_identical_heads(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", relationship="divergent oder rewritten/amended"),
            "divergent relationship contradicts identical HEADs",
        )

    def test_clean_worktree_requires_zero_changes(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", working_tree="clean:5"),
            "contradictory import Working Tree value",
        )

    def test_dirty_worktree_requires_at_least_one_change(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", working_tree="dirty:0"),
            "contradictory import Working Tree value",
        )

    def test_import_timestamp_requires_timezone(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", imported_at="2026-06-23T18:38:45"),
            "import timestamp must include a timezone",
        )

    def test_import_timestamps_must_match(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", captured_at="2026-06-23T18:39:45+00:00"),
            "contradictory import timestamps",
        )

    def test_malformed_table_separator_fails(self) -> None:
        self.assert_contract_error(
            reference_text("alpha", separator="|:|:|"),
            "malformed table separator",
        )


if __name__ == "__main__":
    unittest.main()
