from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from systemkatalog_query import query  # noqa: E402


class SystemkatalogQueryTests(unittest.TestCase):
    def test_system_query_returns_source_binding(self) -> None:
        result = query(ROOT, "system", "grabowski")
        self.assertEqual(result["result"]["system"]["id"], "repo:grabowski")
        self.assertEqual(result["result"]["sourceBinding"]["system"], "repo:grabowski")
        self.assertEqual(result["catalogRepository"], "heimgewebe/systemkatalog")

    def test_truth_owner_uses_authority_matrix_and_node_truth_ownership(self) -> None:
        result = query(ROOT, "truth-owner", "agent_routing")
        self.assertEqual(result["result"]["authority"]["owner"], "grabowski")
        self.assertEqual(result["result"]["ownerSystem"]["id"], "repo:grabowski")

    def test_relations_include_binding_for_each_relation(self) -> None:
        result = query(ROOT, "relations", "systemkatalog")
        relations = result["result"]["relations"]
        self.assertTrue(relations)
        self.assertTrue(all(item["sourceBinding"]["relation"] == {
            "from": item["relation"]["from"],
            "to": item["relation"]["to"],
            "type": item["relation"]["type"],
        } for item in relations))

    def test_unknown_query_fails_with_machine_readable_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "systemkatalog_query.py"), "system", "does-not-exist"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "system_catalog_query_error")


if __name__ == "__main__":
    unittest.main()
