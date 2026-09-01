from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO_ID = "repo:heim-pc-dashboard-chatgpt-app"
SERVICE_ID = "service:heim-pc-chatgpt-dashboard"
REPOSITORY = "heimgewebe/heim-pc-dashboard-chatgpt-app"


def load(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class HeimPcChatgptDashboardIdentityTests(unittest.TestCase):
    def test_repository_is_private_implementation_identity_without_truth_authority(self) -> None:
        nodes = {node["id"]: node for node in load("registry/ecosystem/nodes.json")["nodes"]}
        self.assertIn(REPO_ID, nodes)
        self.assertIn(SERVICE_ID, nodes)
        repository = nodes[REPO_ID]
        service = nodes[SERVICE_ID]

        self.assertEqual(repository["type"], "repository")
        self.assertEqual(repository["truthOwnership"], [])
        self.assertEqual(service["truthOwnership"], [])
        self.assertEqual(
            repository["entrypoints"]["repository"],
            "https://github.com/heimgewebe/heim-pc-dashboard-chatgpt-app",
        )
        self.assertNotEqual(REPO_ID, SERVICE_ID)
        for forbidden in (
            "task authorization or prioritization",
            "claim or dispatch authority",
            "runtime mutation or execution",
            "general operator display ownership",
        ):
            self.assertIn(forbidden, repository["notResponsibleFor"])

    def test_catalog_binds_repository_to_service_without_conflating_leitstand(self) -> None:
        edges = load("registry/ecosystem/edges.json")["edges"]
        implementation = [
            edge
            for edge in edges
            if edge["from"] == REPO_ID
            and edge["to"] == SERVICE_ID
            and edge["type"] == "implements"
        ]
        self.assertEqual(len(implementation), 1)
        self.assertIn("grants no task", implementation[0]["meaning"])

        service_boundaries = [
            edge
            for edge in edges
            if edge["from"] == SERVICE_ID
            and edge["to"] == "repo:leitstand"
            and edge["type"] == "scope_boundary"
        ]
        self.assertEqual(len(service_boundaries), 1)

    def test_private_repository_metadata_and_admission_are_explicit(self) -> None:
        scope = load("registry/ecosystem/organization-scope.v1.json")["repositories"]
        row = next(item for item in scope if item["repository"] == REPOSITORY)
        self.assertEqual(row["visibility"], "private")
        self.assertEqual(row["classification"], "catalog")
        self.assertEqual(row["node"], REPO_ID)

        systems = load("registry/ecosystem/source-bindings.v1.json")["systems"]
        binding = next(item for item in systems if item["system"] == REPO_ID)
        self.assertEqual(binding["source"]["repository"], REPOSITORY)
        self.assertEqual(binding["source"]["commit"], "redacted")
        self.assertEqual(binding["source"]["locator"]["kind"], "private_repository_metadata")
        self.assertEqual(binding["method"], "private_repository_metadata_projection")

        admissions = load("registry/ecosystem/component-admissions.v1.json")["admissions"]
        admission = next(item for item in admissions if item["componentId"] == REPO_ID)
        self.assertEqual(admission["componentKind"], "repository")
        self.assertEqual(admission["admissionClass"], "enable")
        self.assertTrue(admission["truthAuthority"].startswith("none:"))

    def test_boundary_document_names_all_three_roles(self) -> None:
        boundary = (ROOT / "docs/architecture/heim-pc-chatgpt-dashboard-boundary.md").read_text(encoding="utf-8")
        self.assertIn("`repo:heim-pc-dashboard-chatgpt-app`", boundary)
        self.assertIn("`service:heim-pc-chatgpt-dashboard`", boundary)
        self.assertIn("`repo:leitstand`", boundary)
        self.assertIn("keine zusätzliche Wahrheits-, Prioritäts-, Claim-, Dispatch- oder Ausführungsautorität", boundary)


if __name__ == "__main__":
    unittest.main()
