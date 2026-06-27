from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-project-cards.py"
SPEC = importlib.util.spec_from_file_location("project_cards", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load validator")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ROOT = Path(__file__).resolve().parents[2]


class RepositoryProjectCardsTest(unittest.TestCase):
    def test_cards_pass(self) -> None:
        cards = MODULE.validate_project_cards(ROOT)
        self.assertEqual(
            {item["title"] for item in cards},
            {"Heimgewebe", "Weltgewebe"},
        )


if __name__ == "__main__":
    unittest.main()
