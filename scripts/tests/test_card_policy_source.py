from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "card_policy_v1.py"
SPEC = importlib.util.spec_from_file_location("card_policy_source", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load policy")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CardPolicySourceTest(unittest.TestCase):
    def test_summary_folder_fails(self) -> None:
        blocked = (MODULE.PROJECT_DIR / "alpha.md").as_posix()
        cards = [{"id": "alpha", "reviewed_at": "2026-06-27", "sources": [blocked]}]
        with self.assertRaises(MODULE.CardPolicyError):
            MODULE.validate_policy(cards, today=date(2026, 6, 28))


if __name__ == "__main__":
    unittest.main()
