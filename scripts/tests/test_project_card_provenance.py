from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-project-card-provenance.py"
SPEC = importlib.util.spec_from_file_location("project_card_provenance", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load provenance validator")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ProjectCardProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_tracked_index_identical_file_passes(self) -> None:
        source = self.root / "source.md"
        source.write_text("source\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "source.md"], check=True)
        MODULE._verify_index_identical(self.root, Path("source.md"))

    def test_untracked_file_fails(self) -> None:
        (self.root / "source.md").write_text("source\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.ProvenanceError, "ls-files"):
            MODULE._verify_index_identical(self.root, Path("source.md"))

    def test_working_tree_drift_fails(self) -> None:
        source = self.root / "source.md"
        source.write_text("indexed\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "source.md"], check=True)
        source.write_text("drifted\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.ProvenanceError, "differs from indexed"):
            MODULE._verify_index_identical(self.root, Path("source.md"))

    def test_tracked_symlink_fails(self) -> None:
        (self.root / "target.md").write_text("target\n", encoding="utf-8")
        (self.root / "source.md").symlink_to("target.md")
        subprocess.run(["git", "-C", str(self.root), "add", "source.md"], check=True)
        with self.assertRaisesRegex(MODULE.ProvenanceError, "regular Git blob"):
            MODULE._verify_index_identical(self.root, Path("source.md"))


if __name__ == "__main__":
    unittest.main()
