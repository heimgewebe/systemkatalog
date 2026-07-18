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
    def test_system_query_returns_source_binding_and_resilience(self) -> None:
        result = query(ROOT, "system", "grabowski")
        self.assertEqual(result["result"]["system"]["id"], "repo:grabowski")
        self.assertEqual(result["result"]["sourceBinding"]["system"], "repo:grabowski")
        self.assertEqual(result["result"]["resilience"]["criticality"], "foundational")
        self.assertIn("registry/ecosystem/resilience.v1.json", result["sourcePaths"])
        self.assertEqual(result["catalogRepository"], "heimgewebe/systemkatalog")

    def test_repository_query_exposes_target_criticality(self) -> None:
        result = query(ROOT, "repository", "weltgewebe")
        self.assertEqual(result["result"]["resilience"]["criticality"], "essential")

    def test_truth_owner_uses_authority_matrix_and_node_truth_ownership(self) -> None:
        result = query(ROOT, "truth-owner", "agent_routing")
        self.assertEqual(result["result"]["authority"]["owner"], "grabowski")
        self.assertEqual(result["result"]["ownerSystem"]["id"], "repo:grabowski")
        self.assertEqual(result["result"]["ownerResilience"]["criticality"], "foundational")

    def test_relations_preserve_source_bindings_and_add_optional_resilience(self) -> None:
        result = query(ROOT, "relations", "grabowski")
        relations = result["result"]["relations"]
        self.assertTrue(relations)
        self.assertTrue(all(item["sourceBinding"]["relation"] == {
            "from": item["relation"]["from"],
            "to": item["relation"]["to"],
            "type": item["relation"]["type"],
        } for item in relations))
        chronik = next(item for item in relations if item["relation"]["to"] == "repo:chronik")
        self.assertEqual(chronik["resilience"]["coupling"], "asynchronous-durable")
        self.assertEqual(chronik["resilience"]["failurePolicy"], "queue")
        self.assertEqual(chronik["resilience"]["recoveryModeRef"], "chronik-durable-outbox")

    def test_failure_domain_query_returns_affected_systems_and_recovery_modes(self) -> None:
        result = query(ROOT, "failure-domain", "host:heim-pc")
        self.assertIn("repo:grabowski", result["result"]["systems"])
        self.assertIn("grabowski-release-rollback", result["result"]["recoveryModes"])

    def test_recovery_mode_query_preserves_epistemic_limits(self) -> None:
        result = query(ROOT, "recovery-mode", "grabowski-release-rollback")
        self.assertEqual(result["result"]["independence"], "same-failure-domain")
        self.assertIn("automatic rollback authority", result["result"]["doesNotEstablish"])

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
