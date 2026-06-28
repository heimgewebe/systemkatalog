from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import finding_model
from finding_fixture import CLI, base_finding


class FindingCatalogTests(unittest.TestCase):
    def test_empty_directory_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.md").write_text("# Befunde\n", encoding="utf-8")
            self.assertEqual(CLI.validate_directory(root), [])

    def test_duplicate_fingerprint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = base_finding()
            (root / "a.json").write_text(json.dumps(value), encoding="utf-8")
            (root / "b.json").write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(
                finding_model.FindingError,
                "duplicate finding fingerprint",
            ):
                CLI.validate_directory(root)

    def test_unexpected_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "notes.txt").write_text("no\n", encoding="utf-8")
            with self.assertRaisesRegex(finding_model.FindingError, "unexpected"):
                CLI.validate_directory(root)


if __name__ == "__main__":
    unittest.main()
