from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"
REPO_ROOT = SCRIPT_PATH.parents[1]
REFERENCE_PATHSPEC = ":(glob)**/Repository Reference.md"


def reference_text(repository: str) -> str:
    timestamp = "2026-06-23T18:38:45+00:00"
    origin = f"github.com:heimgewebe/{repository}.git"
    canonical_path = f"fixtures/{repository}"
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
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{head}` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `{timestamp}` |
| Pfad | `{canonical_path}` |
| Origin | `{origin}` |
| HEAD | `{head}` |
| Working Tree | `clean:0` |
| Beziehung zum Review | **identisch** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `{canonical_path}` |
| Remote | `{origin}` |
| Default-Branch | `main` |

## Kanonische Systemrolle

> Testrolle
"""


def load_generator_module():
    spec = importlib.util.spec_from_file_location(
        "repository_inventory_followup_under_test", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository inventory generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class RepositoryInventoryHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_generator(
        self, repo_root: Path, *args: str, timeout: float = 10
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(SCRIPT_PATH),
                "--repo-root",
                str(repo_root),
                *args,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )

    def test_fifo_reference_is_rejected_without_blocking(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("os.mkfifo is required for the FIFO counterexample")

        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.root)],
            check=True,
        )
        source_path = "room/Repository Reference.md"
        reference = self.root / source_path
        reference.parent.mkdir(parents=True)
        reference.write_text(reference_text("alpha"), encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", source_path],
            check=True,
        )

        output = self.root / "bestand/10 Repositories/index.md"
        output.parent.mkdir(parents=True)
        output.write_bytes(b"sentinel index\n")
        before = output.read_bytes()

        reference.unlink()
        os.mkfifo(reference)

        written = self.run_generator(self.root)
        checked = self.run_generator(self.root, "--check")

        for result in (written, checked):
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(
                "tracked reference working tree path must be a regular file",
                result.stderr,
            )
        self.assertEqual(before, output.read_bytes())
        self.assertEqual([], list(output.parent.glob(f".{output.name}.*.tmp")))

    def test_stale_inventory_proof_uses_current_worktree_snapshot(self) -> None:
        validator = REPO_ROOT / "scripts/ci/validate-repository.sh"
        if not validator.is_file() or not (REPO_ROOT / ".git").exists():
            self.skipTest("full repository checkout required")

        clone = self.root / "integration-repo"
        head = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        subprocess.run(
            ["git", "clone", "--no-hardlinks", "--quiet", str(REPO_ROOT), str(clone)],
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
                "git",
                "-C",
                str(clone),
                "config",
                "user.email",
                "cabinet-inventory-test@example.invalid",
            ],
            check=True,
        )

        current_worktree_patch = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "diff", "--binary", "HEAD", "--"]
        )
        if current_worktree_patch:
            subprocess.run(
                ["git", "-C", str(clone), "apply", "--binary", "--index", "-"],
                input=current_worktree_patch,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(clone),
                    "commit",
                    "-qm",
                    "test current repository worktree",
                ],
                check=True,
            )

        baseline = subprocess.run(
            [str(clone / "scripts/ci/validate-repository.sh")],
            cwd=clone,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
        self.assertEqual(baseline.returncode, 0, baseline.stdout)

        raw = subprocess.check_output(
            [
                "git",
                "-C",
                str(clone),
                "ls-files",
                "-z",
                "--",
                REFERENCE_PATHSPEC,
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
        ).replace(
            f"| Erfasst | `{old}` |",
            f"| Erfasst | `{new}` |",
            1,
        )
        self.assertNotEqual(updated, text)
        reference.write_text(updated, encoding="utf-8")

        subprocess.run(
            ["git", "-C", str(clone), "add", "--", references[0]],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone), "commit", "-qm", "make inventory stale"],
            check=True,
        )

        stale = subprocess.run(
            [str(clone / "scripts/ci/validate-repository.sh")],
            cwd=clone,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
        self.assertNotEqual(stale.returncode, 0, stale.stdout)
        self.assertIn("repository inventory is stale", stale.stdout)

    def test_escaped_table_pipes_and_backslash_parity(self) -> None:
        module = load_generator_module()
        source = "room/Repository Reference.md"

        self.assertEqual(
            module._split_table_cells(
                r"| Feld | enthält A\|B |", source, "Test", "row"
            ),
            ["Feld", "enthält A|B"],
        )
        self.assertEqual(
            module._split_table_cells(
                r"| Feld | a\\\|b |", source, "Test", "row"
            ),
            ["Feld", r"a\\|b"],
        )
        for raw in ("| Feld | enthält A | B |", r"| Feld | a\\|b |"):
            with self.assertRaisesRegex(module.InventoryError, "malformed table row"):
                module._split_table_cells(raw, source, "Test", "row")

    def test_parse_reference_accepts_escaped_pipe_and_inline_code(self) -> None:
        module = load_generator_module()
        text = reference_text("alpha")
        text = text.replace(
            "| Beziehung zum Review | **identisch** |",
            r"| Beziehung zum Review | **enthält A\|B** |",
        ).replace("`fixtures/alpha`", r"`fixtures/a\|b`")

        record = module.parse_reference(
            "room/Repository Reference.md", text.encode("utf-8")
        )
        self.assertEqual(record.relationship, "enthält A|B")

    def test_deep_path_closes_superseded_parent_descriptors(self) -> None:
        module = load_generator_module()
        implementation = module._implementation
        relative = "one/two/three/four/Repository Reference.md"
        target = self.root / relative
        target.parent.mkdir(parents=True)
        expected = reference_text("alpha").encode("utf-8")
        target.write_bytes(expected)

        opened: list[int] = []
        original_root = implementation._open_root_directory
        original_parent = implementation._open_parent_directory

        def tracked_root(repo_root: Path) -> int:
            descriptor = original_root(repo_root)
            opened.append(descriptor)
            return descriptor

        def tracked_parent(
            source_path: str, component: str, directory_fd: int
        ) -> int:
            for superseded in opened[:-1]:
                with self.assertRaises(OSError):
                    os.fstat(superseded)
            os.fstat(directory_fd)
            descriptor = original_parent(source_path, component, directory_fd)
            opened.append(descriptor)
            return descriptor

        with mock.patch.object(
            implementation, "_open_root_directory", side_effect=tracked_root
        ), mock.patch.object(
            implementation, "_open_parent_directory", side_effect=tracked_parent
        ):
            self.assertEqual(module.read_worktree_reference(self.root, relative), expected)

        for descriptor in opened:
            with self.assertRaises(OSError):
                os.fstat(descriptor)


if __name__ == "__main__":
    unittest.main()
