from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH_SHA = "322655285b520d04363e48487ae64d57264de573"
ARCH_PATH = "architecture/weltgewebe-os.md"
ARCH_URL = f"https://github.com/heimgewebe/weltgewebe/blob/{ARCH_SHA}/{ARCH_PATH}"


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class WeltgewebeOsCatalogTests(unittest.TestCase):
    def test_roles_truths_and_boundaries_are_explicit(self) -> None:
        nodes = {item["id"]: item for item in load("registry/ecosystem/nodes.json")["nodes"]}
        required = {
            "repo:weltgewebe",
            "concept:weltgewebe-os",
            "concept:gewebezelle",
            "concept:weltgewebe-platform-target",
            "concept:weltgewebe-federation-planes",
            "concept:gewebezelle-betreiberrolle",
        }
        self.assertTrue(required <= set(nodes))
        self.assertEqual(nodes["repo:weltgewebe"]["entrypoints"]["targetArchitecture"], ARCH_URL)
        self.assertEqual(nodes["repo:weltgewebe"]["truthOwnership"], ["weltgewebe_target_architecture"])
        self.assertEqual(nodes["concept:gewebezelle"]["truthOwnership"], ["weltgewebe_cell_domain_truth"])
        platform = nodes["concept:weltgewebe-platform-target"]
        self.assertEqual(platform["lifecycle"]["state"], "transition")
        self.assertIn("claiming that Kubernetes production operation is already proven", platform["notResponsibleFor"])
        federation = nodes["concept:weltgewebe-federation-planes"]
        self.assertIn("claims that public cell federation is already operational", federation["notResponsibleFor"])

    def test_authority_and_relations_do_not_create_shadow_status(self) -> None:
        authorities = {item["domain"]: item for item in load("registry/ecosystem/authority-matrix.v1.json")["authorities"]}
        self.assertEqual(authorities["weltgewebe_target_architecture"]["owner"], "weltgewebe")
        self.assertEqual(authorities["weltgewebe_cell_domain_truth"]["owner"], "gewebezelle")
        edges = {(e["from"], e["to"], e["type"]): e for e in load("registry/ecosystem/edges.json")["edges"]}
        self.assertIn(("repo:weltgewebe", "concept:weltgewebe-os", "provides"), edges)
        self.assertIn(("repo:grabowski", "concept:weltgewebe-platform-target", "operates_on"), edges)
        self.assertEqual(edges[("concept:gewebezelle", "concept:weltgewebe-federation-planes", "operates_on")]["stability"], "bounded")
        rendered = json.dumps([load("registry/ecosystem/nodes.json"), load("registry/ecosystem/authority-matrix.v1.json")]).lower()
        for forbidden in ("runtimehealth", "taskstatus", "mergeable", "clusterhealth"):
            self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    unittest.main()
