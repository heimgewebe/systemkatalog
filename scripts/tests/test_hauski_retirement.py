from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HAUSKI_COMMIT = "a265afce24b6f7106c524da71ddd87ab51ba2e7c"
HAUSKI_EVIDENCE_SHA256 = "42f5ded06265155f5d2d199673ecb4a8495b3cfa14b4d8ac939891093a0dc84a"
METAREPO_COMMIT = "6a9d37b9b8a558fae74d3087fbfe5a3a72dd0d37"


class HausKIRetirementTests(unittest.TestCase):
    def _load(self, relative: str):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_hauski_is_retired_without_current_truth_ownership(self) -> None:
        nodes = self._load("registry/ecosystem/nodes.json")["nodes"]
        hauski = next(item for item in nodes if item["id"] == "repo:hausKI")
        self.assertEqual(hauski["lifecycle"]["state"], "retired")
        self.assertEqual(hauski["truthOwnership"], [])
        self.assertIn("current operator execution or routing", hauski["notResponsibleFor"])
        self.assertIn("active Fleet membership or deployment", hauski["notResponsibleFor"])

    def test_hauski_is_archived_reference_in_fleet_coverage(self) -> None:
        coverage = self._load("registry/ecosystem/fleet-coverage.v1.json")
        self.assertEqual(coverage["membershipAuthority"]["commit"], METAREPO_COMMIT)
        hauski = next(
            item for item in coverage["repositories"] if item["node"] == "repo:hausKI"
        )
        self.assertEqual(hauski["membership"], "archived-reference")
        self.assertIn("hausKI", {item["name"] for item in coverage["sourceExclusions"]})

    def test_semantah_no_longer_provides_an_active_hauski_layer(self) -> None:
        edges = self._load("registry/ecosystem/edges.json")["edges"]
        self.assertFalse(
            any(
                item["from"] == "repo:semantAH"
                and item["to"] == "repo:hausKI"
                and item["type"] == "provides"
                for item in edges
            )
        )

    def test_scope_is_archived_reference_after_github_archive_bit_is_true(self) -> None:
        scope = self._load("registry/ecosystem/organization-scope.v1.json")["repositories"]
        hauski = next(item for item in scope if item["repository"] == "heimgewebe/hausKI")
        self.assertEqual(hauski["classification"], "archived_reference")
        self.assertIn("GitHub repository is archived", hauski["reason"])

    def test_source_binding_points_to_exact_retirement_evidence(self) -> None:
        bindings = self._load("registry/ecosystem/source-bindings.v1.json")["systems"]
        hauski = next(item for item in bindings if item["system"] == "repo:hausKI")
        self.assertEqual(hauski["source"]["commit"], HAUSKI_COMMIT)
        locator = hauski["source"]["locator"]
        self.assertEqual(locator["path"], "docs/archive-readiness.v1.json")
        self.assertEqual(locator["contentSha256"], HAUSKI_EVIDENCE_SHA256)


if __name__ == "__main__":
    unittest.main()
