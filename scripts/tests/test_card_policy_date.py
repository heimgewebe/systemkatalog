from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "card_policy_v1.py"
SPEC = importlib.util.spec_from_file_location("card_policy_date", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load policy")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CardPolicyDateTest(unittest.TestCase):
    def test_same_day_passes(self) -> None:
        cards = [{"id": "alpha", "reviewed_at": "2026-06-28", "sources": ["source.md"]}]
        MODULE.validate_policy(cards, today=date(2026, 6, 28))

    def test_later_day_fails(self) -> None:
        cards = [{"id": "alpha", "reviewed_at": "2026-06-29", "sources": ["source.md"]}]
        with self.assertRaises(MODULE.CardPolicyError):
            MODULE.validate_policy(cards, today=date(2026, 6, 28))


if __name__ == "__main__":
    unittest.main()
