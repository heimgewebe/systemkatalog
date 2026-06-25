from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"


def load_generator_module():
    spec = importlib.util.spec_from_file_location(
        "build_repository_index_under_test", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
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

    def make_external_dir(self) -> Path:
        directory = tempfile.TemporaryDirectory(dir=self.root.parent)
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def assert_outside_repository(self, path: Path) -> None:
        root = self.root.resolve()
        resolved = path.resolve()
        self.assertNotEqual(resolved, root)
        self.assertNotIn(root, resolved.parents)

    def write_sentinel_index(self) -> tuple[Path, bytes]:
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"sentinel index\n")
        return output, output.read_bytes()

    def assert_inventory_output_unchanged(self, output: Path, before: bytes) -> None:
        self.assertEqual(before, output.read_bytes())
        self.assertEqual([], list(output.parent.glob(f".{output.name}.*.tmp")))

    def assert_parent_path_error(
        self, result: subprocess.CompletedProcess[str], component: str
    ) -> None:
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("parent path component", result.stderr)
        self.assertIn(repr(component), result.stderr)

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

    def test_symlinked_reference_is_rejected_by_git_mode(self) -> None:
        target = self.root / "room/target.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(reference_text("alpha"), encoding="utf-8")
        link = self.root / "room/Repository Reference.md"
        link.symlink_to(target.name)
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", "room/Repository Reference.md"],
            check=True,
        )
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("git mode 100644", result.stderr)
        self.assertIn("found mode 120000", result.stderr)

    def test_check_mode_rejects_reference_drift_from_git_index(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        built = self.run_cli()
        self.assertEqual(built.returncode, 0, built.stderr)

        reference = self.root / "room/Repository Reference.md"
        reference.write_text(reference_text("beta"), encoding="utf-8")
        checked = self.run_cli("--check")

        self.assertEqual(checked.returncode, 2, checked.stderr)
        self.assertIn(
            "room/Repository Reference.md: tracked reference differs from git index",
            checked.stderr,
        )
        self.assertNotIn("repository inventory is stale", checked.stderr)

    def test_write_mode_uses_current_regular_worktree_reference(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        reference = self.root / "room/Repository Reference.md"
        reference.write_text(reference_text("beta"), encoding="utf-8")

        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`beta`", text)
        self.assertNotIn("`alpha`", text)

        drifted = self.run_cli("--check")
        self.assertEqual(drifted.returncode, 2, drifted.stderr)
        self.assertIn("tracked reference differs from git index", drifted.stderr)

        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", "room/Repository Reference.md"],
            check=True,
        )
        synced = self.run_cli("--check")
        self.assertEqual(synced.returncode, 0, synced.stderr)

    def test_worktree_symlink_is_rejected_even_when_index_mode_is_regular(
        self,
    ) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("indexed"))
        target = self.root.parent / f"{self.root.name}-symlink-target.md"
        target.write_text(reference_text("symlinked"), encoding="utf-8")
        reference = self.root / "room/Repository Reference.md"
        reference.unlink()
        reference.symlink_to(target)
        try:
            written = self.run_cli()
            checked = self.run_cli("--check")
        finally:
            target.unlink(missing_ok=True)

        for result in (written, checked):
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("regular file, not a symlink", result.stderr)
            self.assertNotIn("symlinked", result.stdout)
            self.assertNotIn("symlinked", result.stderr)
        self.assertFalse((self.root / "bestand/10 Repositories/index.md").exists())

    def test_parent_directory_symlink_with_different_content_is_rejected(
        self,
    ) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        output, before = self.write_sentinel_index()
        external = self.make_external_dir()
        external_reference = external / "Repository Reference.md"
        external_reference.write_text(reference_text("beta"), encoding="utf-8")
        self.assert_outside_repository(external_reference)

        shutil.rmtree(self.root / "room")
        (self.root / "room").symlink_to(external, target_is_directory=True)

        written = self.run_cli()
        checked = self.run_cli("--check")

        for result in (written, checked):
            self.assert_parent_path_error(result, "room")
            self.assertNotIn("beta", result.stdout)
            self.assertNotIn("beta", result.stderr)
        self.assert_inventory_output_unchanged(output, before)

    def test_parent_directory_symlink_with_index_identical_content_is_rejected(
        self,
    ) -> None:
        source_path = "room/Repository Reference.md"
        self.write_reference(source_path, reference_text("alpha"))
        raw_entry = subprocess.check_output(
            ["git", "-C", str(self.root), "ls-files", "-s", "--", source_path],
            text=True,
        )
        object_id = raw_entry.split()[1]
        indexed_content = subprocess.check_output(
            ["git", "-C", str(self.root), "cat-file", "blob", object_id]
        )
        external = self.make_external_dir()
        external_reference = external / "Repository Reference.md"
        external_reference.write_bytes(indexed_content)
        self.assert_outside_repository(external_reference)

        shutil.rmtree(self.root / "room")
        (self.root / "room").symlink_to(external, target_is_directory=True)

        written = self.run_cli()
        checked = self.run_cli("--check")

        for result in (written, checked):
            self.assert_parent_path_error(result, "room")
            self.assertNotIn("Repository inventory: PASS", result.stdout)
        self.assertFalse((self.root / "bestand/10 Repositories/index.md").exists())

    def test_nested_parent_directory_symlink_is_rejected(self) -> None:
        source_path = "one/two/three/Repository Reference.md"
        self.write_reference(source_path, reference_text("alpha"))
        output, before = self.write_sentinel_index()
        external = self.make_external_dir()
        external_reference = external / "three/Repository Reference.md"
        external_reference.parent.mkdir(parents=True)
        external_reference.write_text(reference_text("beta"), encoding="utf-8")
        self.assert_outside_repository(external_reference)

        shutil.rmtree(self.root / "one/two")
        (self.root / "one/two").symlink_to(external, target_is_directory=True)

        written = self.run_cli()
        checked = self.run_cli("--check")

        for result in (written, checked):
            self.assert_parent_path_error(result, "two")
            self.assertNotIn("beta", result.stdout)
            self.assertNotIn("beta", result.stderr)
        self.assert_inventory_output_unchanged(output, before)

    def test_nested_regular_reference_path_still_builds_and_checks(self) -> None:
        source_path = "one/two/three/Repository Reference.md"
        self.write_reference(source_path, reference_text("alpha"))

        written = self.run_cli()
        checked = self.run_cli("--check")

        self.assertEqual(written.returncode, 0, written.stderr)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        text = (self.root / "bestand/10 Repositories/index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`alpha`", text)
        self.assertIn(f"`{source_path}`", text)

    def test_parent_path_component_regular_file_is_rejected(self) -> None:
        source_path = "one/two/three/Repository Reference.md"
        self.write_reference(source_path, reference_text("alpha"))
        output, before = self.write_sentinel_index()
        shutil.rmtree(self.root / "one/two")
        (self.root / "one/two").write_text("not a directory\n", encoding="utf-8")

        written = self.run_cli()
        checked = self.run_cli("--check")

        for result in (written, checked):
            self.assert_parent_path_error(result, "two")
        self.assert_inventory_output_unchanged(output, before)

    def test_parent_path_failure_closes_directory_descriptors(self) -> None:
        proc_fds = Path("/proc/self/fd")
        if not proc_fds.is_dir():
            self.skipTest("/proc/self/fd is required for descriptor counting")

        source_path = "one/two/three/Repository Reference.md"
        self.write_reference(source_path, reference_text("alpha"))
        external = self.make_external_dir()
        (external / "three").mkdir()
        (external / "three/Repository Reference.md").write_text(
            reference_text("beta"), encoding="utf-8"
        )
        shutil.rmtree(self.root / "one/two")
        (self.root / "one/two").symlink_to(external, target_is_directory=True)
        generator = load_generator_module()

        before = len(list(proc_fds.iterdir()))
        for _ in range(5):
            with self.assertRaises(generator.InventoryError):
                generator.read_worktree_reference(self.root, source_path)
        after = len(list(proc_fds.iterdir()))

        self.assertEqual(before, after)

    def test_reference_path_components_reject_unsafe_paths(self) -> None:
        generator = load_generator_module()

        for source_path in (
            "",
            "/absolute/Repository Reference.md",
            ".",
            "..",
            "room//Repository Reference.md",
            "room/./Repository Reference.md",
            "room/../Repository Reference.md",
            "room/",
        ):
            with self.subTest(source_path=source_path):
                with self.assertRaises(generator.InventoryError):
                    generator._reference_path_components(source_path)

    def test_missing_worktree_reference_is_rejected(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        (self.root / "room/Repository Reference.md").unlink()

        written = self.run_cli()
        checked = self.run_cli("--check")

        for result in (written, checked):
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("tracked reference missing from working tree", result.stderr)

    def test_existing_output_is_written_with_repository_file_mode(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("stale\n", encoding="utf-8")
        os.chmod(output, 0o644)

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.stat().st_mode & 0o777, 0o644)

    def test_new_output_is_written_with_repository_file_mode(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        output = self.root / "bestand/10 Repositories/index.md"
        self.assertFalse(output.exists())

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.stat().st_mode & 0o777, 0o644)

    def test_atomic_write_removes_temporary_file_after_replace_error(self) -> None:
        generator = load_generator_module()
        output = self.root / "index.md"

        with mock.patch.object(generator.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                generator._atomic_write(output, "content\n")

        self.assertFalse(output.exists())
        self.assertEqual([], list(self.root.glob(".index.md.*.tmp")))

    def test_output_path_must_remain_inside_repository(self) -> None:
        self.write_reference("room/Repository Reference.md", reference_text("alpha"))
        outside = self.root.parent / f"{self.root.name}-outside-index.md"
        outside.unlink(missing_ok=True)
        try:
            result = self.run_cli("--output", str(outside))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("output path escapes repository", result.stderr)
            self.assertFalse(outside.exists())
        finally:
            outside.unlink(missing_ok=True)

    def test_repository_validator_rejects_stale_inventory(self) -> None:
        source_repo = SCRIPT_PATH.parents[1]
        validator = source_repo / "scripts/ci/validate-repository.sh"
        if not validator.is_file() or not (source_repo / ".git").exists():
            self.skipTest("full repository checkout required")

        clone = self.root / "integration-repo"
        head = subprocess.check_output(
            ["git", "-C", str(source_repo), "rev-parse", "HEAD"], text=True
        ).strip()
        subprocess.run(
            ["git", "clone", "--no-hardlinks", "--quiet", str(source_repo), str(clone)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone), "checkout", "--quiet", "--detach", head],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone), "config", "user.name", "Cabinet Inventory Test"],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", str(clone), "config", "user.email",
                "cabinet-inventory-test@example.invalid",
            ],
            check=True,
        )

        raw = subprocess.check_output(
            [
                "git", "-C", str(clone), "ls-files", "-z", "--",
                ":(glob)**/Repository Reference.md",
            ]
        )
        references = [item.decode("utf-8") for item in raw.split(b"\0") if item]
        self.assertTrue(references)
        reference = clone / references[0]
        text = reference.read_text(encoding="utf-8")
        provenance_match = re.search(
            r"(?m)^\| Import-Snapshot erfasst \| `([^`]+)` \|$",
            text,
        )
        live_match = re.search(
            r"(?m)^\| Erfasst \| `([^`]+)` \|$",
            text,
        )
        self.assertIsNotNone(provenance_match)
        self.assertIsNotNone(live_match)
        assert provenance_match is not None
        assert live_match is not None

        old = provenance_match.group(1)
        self.assertEqual(live_match.group(1), old)
        new = (
            datetime.fromisoformat(old.replace("Z", "+00:00"))
            + timedelta(seconds=1)
        ).isoformat()

        updated = text.replace(
            f"| Import-Snapshot erfasst | `{old}` |",
            f"| Import-Snapshot erfasst | `{new}` |",
            1,
        )
        updated = updated.replace(
            f"| Erfasst | `{old}` |",
            f"| Erfasst | `{new}` |",
            1,
        )
        self.assertNotEqual(updated, text)
        reference.write_text(updated, encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(clone), "add", "--", references[0]], check=True
        )
        subprocess.run(
            ["git", "-C", str(clone), "commit", "-qm", "make inventory stale"],
            check=True,
        )

        result = subprocess.run(
            [str(clone / "scripts/ci/validate-repository.sh")],
            cwd=clone,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("repository inventory is stale", result.stdout)


if __name__ == "__main__":
    unittest.main()
