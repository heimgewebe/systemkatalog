from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METAREPO_COMMIT = "08967276c276c0024ec027e926c2b9a93ab9f15d"
FLEET_SHA256 = "6fa4dfb2945a1461b8bf3ffabc48cdf3c477e4bb5c918a8cedc7c8ce758db8ac"


class HausKIRetirementTests(unittest.TestCase):
    def _load(self, relative: str):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_hauski_is_absent_from_current_catalog_truth(self) -> None:
        nodes = {item["id"] for item in self._load("registry/ecosystem/nodes.json")["nodes"]}
        coverage = {
            item["node"]
            for item in self._load("registry/ecosystem/fleet-coverage.v1.json")["repositories"]
        }
        scope = {
            item["name"]
            for item in self._load("registry/ecosystem/organization-scope.v1.json")["repositories"]
        }
        bindings = {
            item["system"]
            for item in self._load("registry/ecosystem/source-bindings.v1.json")["systems"]
        }
        resilience = {
            item["system"]
            for item in self._load("registry/ecosystem/resilience.v1.json")["systems"]
        }
        for current in (nodes, coverage, bindings, resilience):
            self.assertNotIn("repo:hausKI", current)
        self.assertNotIn("hausKI", scope)

    def test_fleet_authority_records_physical_removal(self) -> None:
        coverage = self._load("registry/ecosystem/fleet-coverage.v1.json")
        self.assertEqual(coverage["membershipAuthority"]["commit"], METAREPO_COMMIT)
        self.assertEqual(
            coverage["membershipAuthority"]["contentSha256"], FLEET_SHA256
        )
        self.assertEqual(coverage["sourceExclusions"], [])

    def test_semantah_no_longer_provides_an_active_hauski_layer(self) -> None:
        edges = self._load("registry/ecosystem/edges.json")["edges"]
        self.assertFalse(
            any(item["from"] == "repo:hausKI" or item["to"] == "repo:hausKI" for item in edges)
        )

    def test_retired_admission_policy_drops_hauski_identity(self) -> None:
        policy = self._load("policy/component-admission.v1.json")
        self.assertNotIn("repo:hausKI", policy["grandfatheredNodeIds"])


if __name__ == "__main__":
    unittest.main()
