from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from system_catalog_resilience import validate_resilience  # noqa: E402


class SystemCatalogResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = json.loads((ROOT / "registry/ecosystem/nodes.json").read_text())["nodes"]
        self.edges = json.loads((ROOT / "registry/ecosystem/edges.json").read_text())["edges"]
        self.document = json.loads((ROOT / "registry/ecosystem/resilience.v1.json").read_text())

    def _root(self, document: dict) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "registry/ecosystem").mkdir(parents=True)
        (root / "docs/audits").mkdir(parents=True)
        shutil.copy(ROOT / "registry/ecosystem/authority-matrix.v1.json", root / "registry/ecosystem/authority-matrix.v1.json")
        shutil.copy(ROOT / "registry/ecosystem/edges.json", root / "registry/ecosystem/edges.json")
        shutil.copy(ROOT / "docs/audits/heimgewebe-resilience-gap-matrix-v1.md", root / "docs/audits/heimgewebe-resilience-gap-matrix-v1.md")
        (root / "registry/ecosystem/resilience.v1.json").write_text(json.dumps(document))
        return temp, root

    def test_current_registry_validates_and_covers_all_systems(self) -> None:
        result = validate_resilience(ROOT, self.nodes, self.edges)
        self.assertEqual({item["system"] for item in result["systems"]}, {item["id"] for item in self.nodes})
        self.assertEqual(result["defaultCriticality"], "unknown")

    def test_schema_is_bound_to_registry_contract(self) -> None:
        schema = json.loads((ROOT / "catalog/resilience.schema.v1.json").read_text())
        self.assertEqual(schema["properties"]["criticalityClasses"]["const"], self.document["criticalityClasses"])
        self.assertEqual(schema["properties"]["couplingClasses"]["const"], self.document["couplingClasses"])
        self.assertEqual(schema["properties"]["failurePolicies"]["const"], self.document["failurePolicies"])
        self.assertEqual(schema["properties"]["authorityDirections"]["const"], self.document["authorityDirections"])
        self.assertEqual(
            schema["properties"]["recoveryIndependenceClasses"]["const"],
            self.document["recoveryIndependenceClasses"],
        )
        self.assertEqual(
            schema["$defs"]["systemResilience"]["properties"]["criticality"]["enum"],
            self.document["criticalityClasses"],
        )
        self.assertEqual(
            schema["$defs"]["relationResilience"]["properties"]["coupling"]["enum"],
            self.document["couplingClasses"],
        )
        self.assertEqual(
            schema["$defs"]["recoveryMode"]["properties"]["independence"]["enum"],
            self.document["recoveryIndependenceClasses"],
        )
        self.assertEqual(set(schema["required"]), set(self.document))

    def test_missing_system_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["systems"].pop()
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "system coverage mismatch"):
            validate_resilience(root, self.nodes, self.edges)

    def test_critical_system_requires_recovery_or_explicit_single_path_risk(self) -> None:
        document = copy.deepcopy(self.document)
        item = next(value for value in document["systems"] if value["system"] == "repo:systemkatalog")
        item["recoveryModeRefs"] = []
        item["acceptedSinglePathRisks"] = []
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "critical system requires"):
            validate_resilience(root, self.nodes, self.edges)

    def test_target_owned_relation_rejects_authority_reversal(self) -> None:
        document = copy.deepcopy(self.document)
        item = next(
            value for value in document["relations"]
            if value["relation"] == {
                "from": "repo:grabowski", "to": "service:github", "type": "operates_on"
            }
        )
        item["authorityDirection"] = "from-to"
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "target-owned relation"):
            validate_resilience(root, self.nodes, self.edges)

    def test_unknown_failure_domain_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["systems"][0]["failureDomains"].append("host:not-catalogued")
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "unknown failure domain"):
            validate_resilience(root, self.nodes, self.edges)

    def test_unknown_relation_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["relations"][0]["relation"]["type"] = "invented"
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "relation is unknown"):
            validate_resilience(root, self.nodes, self.edges)

    def test_fallback_without_recovery_mode_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["relations"][0]["failurePolicy"] = "fallback"
        document["relations"][0]["recoveryModeRef"] = None
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "fallback requires"):
            validate_resilience(root, self.nodes, self.edges)

    def test_independent_mode_cannot_hide_shared_domain(self) -> None:
        document = copy.deepcopy(self.document)
        document["recoveryModes"][0]["independence"] = "independent"
        self.assertTrue(document["recoveryModes"][0]["sharedFailureDomains"])
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "independent mode cannot"):
            validate_resilience(root, self.nodes, self.edges)

    def test_missing_evidence_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["systems"][0]["evidence"] = ["docs/missing.md"]
        temp, root = self._root(document)
        with temp, self.assertRaisesRegex(ValueError, "evidence missing"):
            validate_resilience(root, self.nodes, self.edges)


if __name__ == "__main__":
    unittest.main()
