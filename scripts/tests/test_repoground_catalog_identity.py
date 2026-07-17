from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOGROUND_COMMIT = "991a8b5e77cae333e3106a09ddfdde7739fe8d27"
REPOGROUND_README_SHA256 = "51508d263ab92ccfb71e6672df36c47b41da64073097983c3a90dd4d2c123ac6"


def _load(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class RepoGroundCatalogIdentityTests(unittest.TestCase):
    def test_repoground_is_the_only_active_product_identity(self) -> None:
        nodes = _load("registry/ecosystem/nodes.json")["nodes"]
        by_id = {node["id"]: node for node in nodes}

        self.assertIn("repo:repoground", by_id)
        self.assertNotIn("repo:lenskit", by_id)
        self.assertNotIn("concept:repobrief", by_id)
        repoground = by_id["repo:repoground"]
        self.assertEqual(repoground["name"], "RepoGround")
        self.assertEqual(
            repoground["entrypoints"]["repository"],
            "https://github.com/heimgewebe/repoground",
        )
        self.assertEqual(repoground["truthOwnership"], ["repository_context_citations"])

    def test_repoground_provides_context_directly(self) -> None:
        edges = _load("registry/ecosystem/edges.json")["edges"]
        keys = {(edge["from"], edge["to"], edge["type"]) for edge in edges}

        self.assertIn(("repo:repoground", "repo:systemkatalog", "provides"), keys)
        self.assertNotIn(("repo:lenskit", "concept:repobrief", "implements"), keys)
        self.assertNotIn(("concept:repobrief", "repo:systemkatalog", "provides"), keys)

    def test_authority_scope_and_fleet_use_repoground(self) -> None:
        authority = _load("registry/ecosystem/authority-matrix.v1.json")
        context = next(
            item for item in authority["authorities"]
            if item["domain"] == "repository_context_citations"
        )
        self.assertEqual(context["owner"], "repoground")
        self.assertEqual(context["projections"], ["repoground", "systemkatalog"])

        scope = _load("registry/ecosystem/organization-scope.v1.json")
        rows = {item["name"]: item for item in scope["repositories"]}
        self.assertIn("repoground", rows)
        self.assertNotIn("lenskit", rows)
        self.assertEqual(rows["repoground"]["repository"], "heimgewebe/repoground")
        self.assertEqual(rows["repoground"]["node"], "repo:repoground")

        coverage = _load("registry/ecosystem/fleet-coverage.v1.json")
        repositories = {item["repository"]: item for item in coverage["repositories"]}
        self.assertIn("heimgewebe/repoground", repositories)
        self.assertNotIn("heimgewebe/lenskit", repositories)
        self.assertEqual(repositories["heimgewebe/repoground"]["node"], "repo:repoground")

    def test_source_binding_is_commit_and_content_bound(self) -> None:
        bindings = _load("registry/ecosystem/source-bindings.v1.json")
        systems = {item["system"]: item for item in bindings["systems"]}

        self.assertIn("repo:repoground", systems)
        self.assertNotIn("repo:lenskit", systems)
        self.assertNotIn("concept:repobrief", systems)
        source = systems["repo:repoground"]["source"]
        self.assertEqual(source["repository"], "heimgewebe/repoground")
        self.assertEqual(source["commit"], REPOGROUND_COMMIT)
        self.assertEqual(source["locator"]["path"], "README.md")
        self.assertEqual(
            source["locator"]["contentSha256"],
            REPOGROUND_README_SHA256,
        )

    def test_policy_and_rendered_surfaces_have_no_active_lenskit_url(self) -> None:
        policy = _load("policy/system-catalog.v1.json")
        entrypoints = {item["id"]: item for item in policy["entrypoints"]}
        self.assertIn("repoground", entrypoints)
        self.assertNotIn("repobrief_lenskit", entrypoints)
        self.assertEqual(
            entrypoints["repoground"]["target"],
            "https://github.com/heimgewebe/repoground",
        )

        for relative_path in (
            "rendered/system-catalog.md",
            "rendered/ecosystem-registry-map.mmd",
        ):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("RepoGround", text, relative_path)
            self.assertNotIn("heimgewebe/lenskit", text, relative_path)
            self.assertNotIn("repo:lenskit", text, relative_path)
            self.assertNotIn("concept:repobrief", text, relative_path)


if __name__ == "__main__":
    unittest.main()
