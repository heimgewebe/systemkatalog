from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("authority", ROOT / "scripts/validate_ecosystem_authority.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EcosystemAuthorityTests(unittest.TestCase):
    def test_authority_and_usage_contracts_are_valid(self) -> None:
        result = MODULE.validate()
        self.assertEqual(result, {"status": "valid", "authorityDomains": 14, "surfaces": 9})

    def test_single_canonical_map_is_registry_derived(self) -> None:
        matrix = MODULE._load(MODULE.MATRIX)
        self.assertEqual(matrix["canonicalMap"], "rendered/ecosystem-registry-map.mmd")
        self.assertTrue(all(view["authoritative"] is False for view in matrix["specializedViews"]))

    def test_unreachable_remote_is_not_reported_absent(self) -> None:
        usage = MODULE._load(MODULE.USAGE)
        heimserver = next(item for item in usage["hosts"] if item["id"] == "heimserver")
        self.assertEqual(heimserver["status"], "unknown_unreachable")


if __name__ == "__main__":
    unittest.main()
