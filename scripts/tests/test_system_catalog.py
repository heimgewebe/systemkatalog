from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "system_catalog_validator", ROOT / "scripts/validate_system_catalog.py"
)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)

RENDERER_SPEC = importlib.util.spec_from_file_location(
    "system_catalog_renderer", ROOT / "scripts/render_system_catalog.py"
)
assert RENDERER_SPEC and RENDERER_SPEC.loader
RENDERER = importlib.util.module_from_spec(RENDERER_SPEC)
RENDERER_SPEC.loader.exec_module(RENDERER)


class SystemCatalogTests(unittest.TestCase):
    def test_catalog_contract_is_valid(self) -> None:
        self.assertEqual(
            VALIDATOR.validate(),
            {
                "status": "valid",
                "registrySystems": 26,
                "registryRelations": 38,
                "authorityDomains": 14,
                "exampleSystems": 5,
                "legacyDebtItems": 3,
                "externalAppRequired": False,
            },
        )

    def test_rendered_catalog_is_current(self) -> None:
        rendered = (ROOT / "rendered/system-catalog.md").read_text(encoding="utf-8")
        self.assertEqual(rendered, RENDERER.render_text())
        self.assertNotIn("runtime health:", rendered.lower())
        self.assertNotIn("merge ready", rendered.lower())
        self.assertNotIn("| heim-pc |", rendered)
        self.assertNotIn("| heimserver |", rendered)
        self.assertIn("[README.md](../README.md)", rendered)

    def test_external_app_is_optional_and_non_canonical(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        app = policy["externalCabinetApp"]
        self.assertFalse(app["required"])
        self.assertFalse(app["canonical"])
        self.assertFalse(app["runtimeAuthoritative"])
        self.assertFalse(app["shutdownAuthorized"])
        self.assertEqual(policy["publicProjection"]["excludedKinds"], ["runtime"])

    def test_example_rejects_operational_status_fields(self) -> None:
        policy = VALIDATOR._load(VALIDATOR.POLICY)
        example = copy.deepcopy(VALIDATOR._load(VALIDATOR.EXAMPLE))
        example["systems"][0]["runtimeHealth"] = "healthy"
        with self.assertRaisesRegex(ValueError, "prohibited operational fields"):
            VALIDATOR._validate_example(policy, example)

    def test_operational_domains_do_not_project_into_cabinet(self) -> None:
        authority = VALIDATOR._load(VALIDATOR.AUTHORITY)
        by_domain = {item["domain"]: item for item in authority["authorities"]}
        for domain in ("tasks_claims_completion", "branches_prs_reviews", "live_service_state"):
            self.assertNotIn("cabinet", by_domain[domain]["projections"])


if __name__ == "__main__":
    unittest.main()
