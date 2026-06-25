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
    live_head: str = "2" * 40,
    working_tree: str = "clean:0",
    role: str | None = "Testrolle",
) -> str:
    origin = f"github.com:heimgewebe/{repository}.git"
    canonical_path = f"/tmp/repos/{repository}"
    role_section = (
        f"\n## Kanonische Systemrolle\n\n> {role}\n" if role is not None else ""
    )
    return f"""# {repository} — Repository Reference

## Provenienz

| Feld | Wert |
|---|---|
| Import-Snapshot erfasst | `2026-06-23T18:38:45+00:00` |

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
| Erfasst | `2026-06-23T18:38:45+00:00` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{live_head}` |
| Working Tree | `{working_tree}` |
| Beziehung zum Review | **identisch** |

## Identität

| Feld | Wert |
|---|---|
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
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "ci.invalid"], check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_reference(self, relative: str, content: str, *, track: bool = True) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if track:
            subprocess.run(["git", "-C", str(self.root), "add", "--", relative], check=True)

    def commit(self) -> None:
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT_PATH), "--repo-root", str(self.root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_compact_role_and_hashes_are_deterministic(self) -> None:
        self.write_reference(
            "z/Repository Reference.md",
            reference_text("zulu", role="A deliberately long repository role that must be clipped visibly"),
        )
        self.write_reference("space dir/Repository Reference.md", reference_text("alpha"))
        self.commit()
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.root / "bestand/10 Repositories/index.md"
        before = output.read_bytes()
        text = before.decode("utf-8")
        self.assertLess(text.index("`alpha`"), text.index("`zulu`"))
        self.assertIn("| Repository | Rolle | Review | Live |", text)
        self.assertIn("`111111111111`", text)
        self.assertNotIn("`" + "1" * 40 + "`", text)
        self.assertIn("A deliberately long repository role that must be...", text)
        self.assertIn("space%20dir/Repository%20Reference.md", text)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(before, output.read_bytes())

    def test_check_and_tracked_only_discovery(self) -> None:
        self.write_reference("tracked/Repository Reference.md", reference_text("alpha"))
        self.write_reference("untracked/Repository Reference.md", reference_text("beta"), track=False)
        self.commit()
        self.assertEqual(self.run_cli().returncode, 0)
        checked = self.run_cli("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(encoding="utf-8")
        self.assertIn("`alpha`", text)
        self.assertNotIn("`beta`", text)

    def test_stale_index_is_reported_without_writing(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        self.commit()
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("stale\n", encoding="utf-8")
        before = output.read_bytes()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("repository inventory is stale", result.stderr)
        self.assertEqual(before, output.read_bytes())

    def test_optional_role_warns_but_builds(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha", role=None))
        self.commit()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("optional role missing", result.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(encoding="utf-8")
        self.assertIn("| `alpha` | — |", text)

    def test_unconsumed_sections_are_not_required(self) -> None:
        content = reference_text("alpha")
        self.assertNotIn("## Pflegevertrag", content)
        self.write_reference("room/Repository Reference.md", content)
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("missing required section", result.stderr)

    def test_duplicate_repository_identity_fails(self) -> None:
        self.write_reference("one/Repository Reference.md", reference_text("alpha"))
        self.write_reference("two/Repository Reference.md", reference_text("ALPHA"))
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate repository identity", result.stderr)

    def test_missing_identity_section_fails(self) -> None:
        content = reference_text("alpha").replace("## Identität", "## Other")
        self.write_reference("room/Repository Reference.md", content)
        self.commit()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing required section", result.stderr)

    def test_invalid_commit_fails(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha", review_head="abc"))
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
