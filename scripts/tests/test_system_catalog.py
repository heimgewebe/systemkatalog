from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("system_catalog_validator", ROOT / "scripts/validate_system_catalog.py")
RENDERER = load_module("system_catalog_renderer", ROOT / "scripts/render_system_catalog.py")


class SystemCatalogTests(unittest.TestCase):
    def test_catalog_contract_is_valid(self) -> None:
        self.assertEqual(
            VALIDATOR.validate(),
            {
                "status": "valid",
                "registrySystems": 19,
                "registryRelations": 24,
                "stableClaims": 8,
                "authorityDomains": 14,
                "exampleSystems": 5,
                "maintainedCatalogSurfaces": 8,
                "legacyCompatibilitySurfaces": 10,
                "externalAppRequired": False,
            },
        )

    def test_rendered_catalog_is_current_and_status_free(self) -> None:
        rendered = (ROOT / "rendered/system-catalog.md").read_text(encoding="utf-8")
        self.assertEqual(rendered, RENDERER.render_text())
        for fragment in ("runtime health:", "merge ready", "| heim-pc |", "| heimserver |", "status: active"):
            self.assertNotIn(fragment, rendered.lower())
        self.assertIn("[README.md](../README.md)", rendered)
        self.assertIn("`stable`", rendered)

    def test_legacy_source_archives_are_hash_bound(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        archives = {item["path"]: item["sha256"] for item in policy["legacySourceArchives"]}
        self.assertEqual(
            archives["docs/archive/cabinet-era/ecosystem-dynamic-claims-v0.jsonl"],
            "297fc9e2c7f67513ce225a19b4d425992947133dab2934e888e92e4a28260784",
        )
        self.assertEqual(
            archives["docs/archive/cabinet-era/cabinet-role-boundary-v1.superseded.md"],
            "2cd05d4a03c71a1dabc53ac25d46f5ba0122419d4b30657c75d8bf758a2d2ed1",
        )

    def test_external_app_is_optional_noncanonical_and_not_shutdown_authorized(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        app = policy["externalCabinetApp"]
        self.assertFalse(app["required"])
        self.assertFalse(app["canonical"])
        self.assertFalse(app["runtimeAuthoritative"])
        self.assertFalse(app["shutdownAuthorized"])

    def test_canonical_inputs_reject_operational_fields(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        nodes = copy.deepcopy(VALIDATOR._load(VALIDATOR.NODES))
        nodes["nodes"][0]["runtimeHealth"] = "healthy"
        with self.assertRaisesRegex(ValueError, "prohibited operational fields"):
            VALIDATOR._validate_no_operational_fields(policy, "nodes", nodes)

    def test_runtime_and_provider_agents_are_not_catalog_nodes(self) -> None:
        nodes = VALIDATOR._load(VALIDATOR.NODES)["nodes"]
        ids = {item["id"] for item in nodes}
        self.assertFalse(any(item.startswith("runtime:") for item in ids))
        self.assertFalse(any(item.startswith("agent:") for item in ids))

    def test_operational_domains_do_not_project_into_cabinet(self) -> None:
        authority = VALIDATOR._load(VALIDATOR.AUTHORITY)
        by_domain = {item["domain"]: item for item in authority["authorities"]}
        for domain in ("tasks_claims_completion", "branches_prs_reviews", "live_service_state"):
            self.assertNotIn("cabinet", by_domain[domain]["projections"])

    def test_exactly_one_authority_matrix_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self._copy_catalog_bundle(Path(temporary))
            duplicate = target / "registry/ecosystem/competing-authority.json"
            duplicate.write_text((target / VALIDATOR.AUTHORITY_REL).read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one maintained authority matrix"):
                VALIDATOR.validate(target)

    def test_competing_authority_matrix_outside_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self._copy_catalog_bundle(Path(temporary))
            duplicate = target / "docs/competing-authority.json"
            duplicate.parent.mkdir(parents=True, exist_ok=True)
            duplicate.write_text((target / VALIDATOR.AUTHORITY_REL).read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one maintained authority matrix"):
                VALIDATOR.validate(target)

    def test_manual_authority_assignments_outside_matrix_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self._copy_catalog_bundle(Path(temporary))
            manual = target / "policy/manual-authority.json"
            manual.write_text(json.dumps({"kind": "other", "authorities": [{"domain": "runtime", "owner": "cabinet"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manual authority assignments"):
                VALIDATOR.validate(target)

    def test_legacy_automation_is_manual_only(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        automation = policy["legacyAutomationPolicy"]
        self.assertFalse(automation["scheduledExecution"])
        self.assertFalse(automation["automaticPushOrPullRequestExecution"])
        self.assertFalse(automation["automaticDispatch"])
        self.assertFalse(automation["automaticMutation"])
        VALIDATOR._validate_legacy_automation(ROOT, policy)

    def test_bridge_probe_uses_isolated_legacy_adapter(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        adapter = policy["legacyAutomationPolicy"]["bridgeProbeAdapter"]
        self.assertEqual(adapter, "scripts/prepare_legacy_bridge_probe.py")
        self.assertIn(adapter, policy["legacyCompatibilitySurfaces"])
        workflow_path = policy["legacyAutomationPolicy"]["bridgeProbeWorkflow"]
        self.assertEqual(workflow_path, ".github/workflows/cabinet-bridge-probe.yml")
        workflow = (ROOT / workflow_path).read_text(encoding="utf-8")
        self.assertIn(f"python3 {adapter} --output bridge-probe-sandbox", workflow)
        self.assertIn("--bridge-policy bridge-probe-sandbox/registry/ecosystem/bureau-bridge.json", workflow)
        self.assertIn("set -o pipefail", workflow)

    def test_catalog_bundle_validates_and_renders_without_app_or_runtime_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self._copy_catalog_bundle(Path(temporary))
            self.assertFalse((target / ".cabinet").exists())
            self.assertFalse((target / "rooms").exists())
            with patch.dict(os.environ, {"CABINET_DATA_DIR": str(target / "missing-private-data")}, clear=False):
                result = VALIDATOR.validate(target)
                rendered = RENDERER.render_text(target)
            self.assertEqual(result["status"], "valid")
            self.assertIn("# Heimgewebe-Systemkatalog", rendered)
            self.assertNotIn("missing-private-data", rendered)

    def _copy_catalog_bundle(self, target: Path) -> Path:
        policy = json.loads((ROOT / VALIDATOR.POLICY_REL).read_text(encoding="utf-8"))
        relatives = {
            str(VALIDATOR.POLICY_REL),
            str(VALIDATOR.SCHEMA_REL),
            str(VALIDATOR.EXAMPLE_REL),
            str(VALIDATOR.NODES_REL),
            str(VALIDATOR.EDGES_REL),
            str(VALIDATOR.CLAIMS_REL),
            str(VALIDATOR.AUTHORITY_REL),
            str(VALIDATOR.VIEW_REL),
            "README.md",
            "AGENTS.md",
            "scripts/validate_system_catalog.py",
            "scripts/render_ecosystem_registry_map.py",
        }
        relatives.update(policy["maintainedCatalogSurfaces"])
        relatives.update(policy["legacyCompatibilitySurfaces"])
        relatives.update(policy["legacyAutomationPolicy"]["manualCompatibilityWorkflows"])
        relatives.add(policy["legacyAutomationPolicy"]["compatibilityValidationWorkflow"])
        relatives.add(policy["legacyAutomationPolicy"]["bridgeProbeWorkflow"])
        for relative in sorted(relatives):
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return target


if __name__ == "__main__":
    unittest.main()
