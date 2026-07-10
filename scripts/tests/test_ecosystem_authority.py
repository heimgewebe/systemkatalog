from __future__ import annotations

import copy
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
        self.assertEqual(
            result,
            {
                "status": "valid",
                "authorityDomains": 14,
                "surfaces": 9,
                "publicRuntimeDetails": "redacted",
                "coverageLocations": 4,
            },
        )

    def test_single_canonical_map_is_registry_derived(self) -> None:
        matrix = MODULE._load(MODULE.MATRIX)
        self.assertEqual(matrix["canonicalMap"], "rendered/ecosystem-registry-map.mmd")
        self.assertTrue(all(view["authoritative"] is False for view in matrix["specializedViews"]))

    def test_public_usage_snapshot_is_explicitly_redacted(self) -> None:
        usage = MODULE._load(MODULE.USAGE)
        self.assertEqual(usage["visibility"], "public_redacted_summary")
        self.assertTrue(usage["privateEvidence"]["storedOutsideRepository"])
        self.assertTrue(usage["privateEvidence"]["publicDetailsRedacted"])
        MODULE._validate_public_usage(usage)

    def test_private_runtime_keys_fail_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["hosts"] = [{"id": "private-host"}]
        with self.assertRaisesRegex(ValueError, "private runtime keys"):
            MODULE._validate_public_usage(usage)

    def test_private_runtime_values_fail_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["surfaces"][0]["usageSignal"] = "observed sensitive.service"
        with self.assertRaisesRegex(ValueError, "private runtime values"):
            MODULE._validate_public_usage(usage)


if __name__ == "__main__":
    unittest.main()
