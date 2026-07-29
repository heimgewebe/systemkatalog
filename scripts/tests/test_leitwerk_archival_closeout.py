import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FINAL_LEITWERK = "1449145af543b78c0d3813942f1d6d95ddb33c4a"
FINAL_METAREPO = "df3063d846d6751e668b65ec8e64a4fc34474401"
FLEET_SHA256 = "4fc8803f7acc91eb1967cf325eb25638328e31dffdca49e35aeea17f2bee8ce9"
README_SHA256 = "192c8ebb41e0af26792696e677758bbdfc5b5466148980265ff3677fbf6bf012"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class LeitwerkArchivalCloseoutTests(unittest.TestCase):
    def test_closeout_binds_github_migration_and_fleet_authority(self) -> None:
        audit = load("docs/audits/leitwerk-archival-closeout-2026-07-29.v1.json")
        self.assertEqual(audit["decision"], "archived_reference")
        self.assertIs(audit["github_readback"]["archived"], True)
        self.assertEqual(audit["github_readback"]["main_commit"], FINAL_LEITWERK)
        self.assertEqual(audit["migration"]["merge_commit"], "74ce9202952d00b0d2fef0587255c92a9cd05dee")
        fleet = audit["fleet_registration"]
        self.assertEqual(fleet["pull_request"], 668)
        self.assertEqual(fleet["merge_commit"], FINAL_METAREPO)
        self.assertEqual(fleet["source_content_sha256"], FLEET_SHA256)
        self.assertEqual(fleet["classification"], "archived-reference")
        self.assertIs(fleet["fleet"], False)
        self.assertEqual(fleet["active_fleet_count"], 18)

    def test_catalog_node_is_archived_and_owns_no_truth(self) -> None:
        nodes = load("registry/ecosystem/nodes.json")["nodes"]
        node = next(item for item in nodes if item["id"] == "repo:leitwerk")
        self.assertEqual(node["lifecycle"]["state"], "archived")
        self.assertEqual(node["truthOwnership"], [])
        self.assertIn("active contract or policy authority", node["notResponsibleFor"])
        self.assertIn("https://github.com/heimgewebe/metarepo/pull/668", node["lifecycle"]["evidenceRefs"])
        self.assertIn(FINAL_LEITWERK, node["entrypoints"]["readme"])

    def test_fleet_coverage_uses_exact_archived_reference_authority(self) -> None:
        coverage = load("registry/ecosystem/fleet-coverage.v1.json")
        self.assertEqual(coverage["membershipAuthority"]["commit"], FINAL_METAREPO)
        self.assertEqual(coverage["membershipAuthority"]["contentSha256"], FLEET_SHA256)
        entry = next(item for item in coverage["repositories"] if item["node"] == "repo:leitwerk")
        self.assertEqual(entry["membership"], "archived-reference")

    def test_source_binding_is_final_commit_and_readme_digest(self) -> None:
        bindings = load("registry/ecosystem/source-bindings.v1.json")["systems"]
        binding = next(item for item in bindings if item["system"] == "repo:leitwerk")
        self.assertEqual(binding["source"]["commit"], FINAL_LEITWERK)
        self.assertEqual(binding["source"]["locator"]["path"], "README.md")
        self.assertEqual(binding["source"]["locator"]["contentSha256"], README_SHA256)
        self.assertLessEqual(binding["uncertainty"], 0.01)

    def test_scope_resilience_and_relations_preserve_non_authority(self) -> None:
        scope = load("registry/ecosystem/organization-scope.v1.json")["repositories"]
        entry = next(item for item in scope if item["name"] == "leitwerk")
        self.assertEqual(entry["classification"], "archived_reference")

        resilience = load("registry/ecosystem/resilience.v1.json")["systems"]
        item = next(entry for entry in resilience if entry["system"] == "repo:leitwerk")
        self.assertEqual(item["criticality"], "optional")

        edges = [
            edge for edge in load("registry/ecosystem/edges.json")["edges"]
            if edge["from"] == "repo:leitwerk"
        ]
        self.assertTrue(edges)
        self.assertTrue(all(edge["type"] == "scope_boundary" for edge in edges))
        self.assertTrue(all("inherits no Leitwerk authority" in edge["meaning"] for edge in edges))


if __name__ == "__main__":
    unittest.main()
