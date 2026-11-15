"""Regression contract for the six archived Heimgewebe repositories (2026-11-15)."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ARCHIVED_CATALOG_NODES = {
    "repo:semantAH",
    "repo:plexer",
    "repo:leitstand",
    "repo:obsidian-bridge",
    "repo:alpha-lab",
}


class ArchivedRepositoryLifecycleTests(unittest.TestCase):
    def test_retired_from_active_catalog_without_losing_history(self) -> None:
        catalog = json.loads((ROOT / "registry/ecosystem/nodes.json").read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in catalog["nodes"]}
        for name in sorted(ARCHIVED_CATALOG_NODES):
            with self.subTest(node=name):
                lifecycle = nodes[name]["lifecycle"]
                self.assertEqual(lifecycle["state"], "archived")
                self.assertIn("https://github.com/heimgewebe/metarepo/pull/756", lifecycle["evidenceRefs"])
                self.assertTrue(nodes[name]["entrypoints"]["repository"].startswith("https://github.com/"))

    def test_sixth_repo_remains_historical_excluded_reference(self) -> None:
        scope = json.loads(
            (ROOT / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8")
        )
        entries = {entry["repository"]: entry for entry in scope["repositories"]}
        self.assertEqual(entries["heimgewebe/capacity-marketplace"]["classification"], "archived_excluded")
        self.assertIsNone(entries["heimgewebe/capacity-marketplace"]["node"])


if __name__ == "__main__":
    unittest.main()