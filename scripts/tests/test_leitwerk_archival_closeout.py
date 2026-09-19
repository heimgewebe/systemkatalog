import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FINAL_LEITWERK = "1449145af543b78c0d3813942f1d6d95ddb33c4a"
FINAL_METAREPO = "df3063d846d6751e668b65ec8e64a4fc34474401"
FLEET_SHA256 = "4fc8803f7acc91eb1967cf325eb25638328e31dffdca49e35aeea17f2bee8ce9"
CURRENT_METAREPO = "bb32f569ca35bdfdc9d956b31709c86cd83eb685"
CURRENT_FLEET_SHA256 = "a089df0e8f45d4a4c73da3517a0cebe1644bf3a83bb0e8460c08924b512379dc"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class LeitwerkArchivalCloseoutTests(unittest.TestCase):
    def test_closeout_binds_historical_github_migration_and_fleet_authority(self) -> None:
        audit = load("docs/audits/leitwerk-archival-closeout-2026-07-29.v1.json")
        self.assertEqual(audit["decision"], "archived_reference")
        self.assertIs(audit["github_readback"]["archived"], True)
        self.assertEqual(audit["github_readback"]["main_commit"], FINAL_LEITWERK)
        self.assertEqual(
            audit["migration"]["merge_commit"],
            "74ce9202952d00b0d2fef0587255c92a9cd05dee",
        )
        fleet = audit["fleet_registration"]
        self.assertEqual(fleet["pull_request"], 668)
        self.assertEqual(fleet["merge_commit"], FINAL_METAREPO)
        self.assertEqual(fleet["source_content_sha256"], FLEET_SHA256)
        self.assertEqual(fleet["classification"], "archived-reference")
        self.assertIs(fleet["fleet"], False)
        self.assertEqual(fleet["active_fleet_count"], 18)

    def test_leitwerk_is_absent_from_current_catalog_truth(self) -> None:
        nodes = {item["id"] for item in load("registry/ecosystem/nodes.json")["nodes"]}
        coverage = {
            item["node"]
            for item in load("registry/ecosystem/fleet-coverage.v1.json")["repositories"]
        }
        scope = {
            item["name"]
            for item in load("registry/ecosystem/organization-scope.v1.json")["repositories"]
        }
        bindings = {
            item["system"]
            for item in load("registry/ecosystem/source-bindings.v1.json")["systems"]
        }
        resilience = {
            item["system"]
            for item in load("registry/ecosystem/resilience.v1.json")["systems"]
        }
        for current in (nodes, coverage, bindings, resilience):
            self.assertNotIn("repo:leitwerk", current)
        self.assertNotIn("leitwerk", scope)
        edges = load("registry/ecosystem/edges.json")["edges"]
        self.assertFalse(
            any(edge["from"] == "repo:leitwerk" or edge["to"] == "repo:leitwerk" for edge in edges)
        )

    def test_current_fleet_authority_has_no_leitwerk_exclusion(self) -> None:
        coverage = load("registry/ecosystem/fleet-coverage.v1.json")
        self.assertEqual(coverage["membershipAuthority"]["commit"], CURRENT_METAREPO)
        self.assertEqual(
            coverage["membershipAuthority"]["contentSha256"], CURRENT_FLEET_SHA256
        )
        self.assertEqual(coverage["sourceExclusions"], [])

    def test_historical_admission_baseline_preserves_leitwerk_identity(self) -> None:
        policy = load("policy/component-admission.v1.json")
        self.assertIn("repo:leitwerk", policy["grandfatheredNodeIds"])


if __name__ == "__main__":
    unittest.main()
