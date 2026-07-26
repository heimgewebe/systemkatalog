from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from system_catalog_admissions import ComponentAdmissionError, validate_component_admissions


class ComponentAdmissionTests(unittest.TestCase):
    def _root(self, *, grandfathered=None, admissions=None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "policy").mkdir()
        (root / "registry/ecosystem").mkdir(parents=True)
        grandfathered_values = grandfathered or []
        baseline_payload = json.dumps(sorted(grandfathered_values), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        policy = {
            "schemaVersion": 1,
            "kind": "system_catalog_component_admission_policy",
            "owner": "repo:systemkatalog",
            "role": "admission_gate_for_new_durable_components",
            "inScopeNodeTypes": ["repository", "service", "background_process", "operator_surface"],
            "admissionClasses": ["replace", "reduce", "enable", "experimental"],
            "grandfatheredNodeIds": grandfathered_values,
            "grandfatheredBaselineSha256": hashlib.sha256(baseline_payload).hexdigest(),
            "requiredAdmissionFields": [
                "componentId",
                "componentKind",
                "admissionClass",
                "purpose",
                "consumers",
                "truthAuthority",
                "operatingDependencies",
                "maintenanceBurden",
                "reviewOrRetirementPath",
                "source",
                "doesNotEstablish",
            ],
            "experimentalRequiredFields": ["successCriterion", "reviewBy"],
            "authorityBoundary": {
                "stableSemantics": "Systemkatalog",
                "taskPriorityAndCloseout": "Bureau",
                "runtimeAndExecution": "source systems and Grabowski",
                "doesNotEstablish": ["runtime status"],
            },
        }
        registry = {
            "schemaVersion": 1,
            "kind": "system_catalog_component_admissions",
            "owner": "repo:systemkatalog",
            "policy": "policy/component-admission.v1.json",
            "admissions": admissions or [],
            "doesNotEstablish": ["runtime status"],
        }
        (root / "policy/component-admission.v1.json").write_text(
            json.dumps(policy), encoding="utf-8"
        )
        (root / "registry/ecosystem/component-admissions.v1.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        return root


    @staticmethod
    def _validate(root, nodes):
        policy = json.loads((root / "policy/component-admission.v1.json").read_text(encoding="utf-8"))
        return validate_component_admissions(
            root,
            nodes,
            expected_grandfathered_sha256=policy["grandfatheredBaselineSha256"],
        )

    @staticmethod
    def _node(component_id="repo:new", kind="repository", purpose="New durable component"):
        return {
            "id": component_id,
            "name": "New",
            "type": kind,
            "purpose": purpose,
            "lifecycle": {
                "state": "active",
                "reviewedAt": "2026-07-26",
                "evidenceRefs": ["test:fixture"],
            },
            "notResponsibleFor": [],
            "truthOwnership": [],
            "entrypoints": {"repository": "https://example.invalid/new"},
        }

    @staticmethod
    def _admission(admission_class="enable", **overrides):
        value = {
            "componentId": "repo:new",
            "componentKind": "repository",
            "admissionClass": admission_class,
            "purpose": "New durable component",
            "consumers": ["operator"],
            "truthAuthority": "none: component owns no canonical truth domain",
            "operatingDependencies": [],
            "maintenanceBurden": "repository maintenance and CI",
            "reviewOrRetirementPath": "review on consumer removal; archive when unused",
            "source": {"kind": "bureau_task", "ref": "HEIMGEWEBE-RESILIENZ-V1-T016"},
            "doesNotEstablish": ["runtime status", "task authority"],
        }
        if admission_class == "experimental":
            value["successCriterion"] = "one named consumer uses the component successfully"
            value["reviewBy"] = "2030-01-01"
        value.update(overrides)
        return value

    def test_grandfathers_pre_existing_component(self):
        root = self._root(grandfathered=["repo:new"])
        result = self._validate(root, [self._node()])
        self.assertEqual(result["grandfatheredComponentsPresent"], 1)
        self.assertEqual(result["admittedComponents"], 0)

    def test_rejects_grandfathered_baseline_expansion_without_contract_change(self):
        root = self._root(grandfathered=["repo:new"])
        with self.assertRaisesRegex(
            ComponentAdmissionError,
            "grandfathered baseline expansion or replacement requires an explicit contract change",
        ):
            validate_component_admissions(root, [self._node()])

    def test_accepts_enable_admission(self):
        root = self._root(admissions=[self._admission()])
        result = self._validate(root, [self._node()])
        self.assertEqual(result["admittedComponents"], 1)

    def test_accepts_experimental_admission(self):
        root = self._root(admissions=[self._admission("experimental")])
        result = self._validate(root, [self._node()])
        self.assertEqual(result["admittedComponents"], 1)

    def test_rejects_new_component_without_admission(self):
        root = self._root()
        with self.assertRaisesRegex(ComponentAdmissionError, "lack admission evidence"):
            self._validate(root, [self._node()])

    def test_rejects_missing_consumer_or_truth_authority(self):
        for field, replacement in (("consumers", []), ("truthAuthority", "")):
            with self.subTest(field=field):
                root = self._root(admissions=[self._admission(**{field: replacement})])
                with self.assertRaises(ComponentAdmissionError):
                    self._validate(root, [self._node()])

    def test_rejects_incomplete_experimental_admission(self):
        admission = self._admission("experimental")
        admission.pop("successCriterion")
        root = self._root(admissions=[admission])
        with self.assertRaisesRegex(ComponentAdmissionError, "fields mismatch"):
            self._validate(root, [self._node()])

    def test_rejects_expired_experimental_admission(self):
        root = self._root(admissions=[self._admission("experimental", reviewBy="2020-01-01")])
        with self.assertRaisesRegex(ComponentAdmissionError, "reviewBy is expired"):
            self._validate(root, [self._node()])


if __name__ == "__main__":
    unittest.main()
