from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-project-cards.py"
SPEC = importlib.util.spec_from_file_location("project_cards_parser", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load validator")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ProjectCardParserTest(unittest.TestCase):
    def test_metadata_block_is_read(self) -> None:
        value = {"schema": "cabinet.project-card.v1", "id": "alpha"}
        text = "<!-- cabinet-project-card-v1\n" + json.dumps(value) + "\n-->"
        self.assertEqual(MODULE._load_metadata(text, "card"), value)

    def test_duplicate_metadata_blocks_fail(self) -> None:
        block = '<!-- cabinet-project-card-v1\n{"id":"alpha"}\n-->'
        with self.assertRaisesRegex(MODULE.ProjectCardError, "exactly one"):
            MODULE._load_metadata(block + "\n" + block, "card")

    def test_required_section_must_have_content(self) -> None:
        with self.assertRaisesRegex(MODULE.ProjectCardError, "empty"):
            MODULE._section_body("## Ziel\n\n## Quellen\ntext\n", "## Ziel")


if __name__ == "__main__":
    unittest.main()
