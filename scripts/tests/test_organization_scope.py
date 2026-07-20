from __future__ import annotations

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

from system_catalog_fleet import validate_coverage  # noqa: E402
from system_catalog_scope import (  # noqa: E402
    OrganizationScopeError,
    load_scope,
    validate_github_inventory,
    validate_scope,
)


class OrganizationScopeTests(unittest.TestCase):
    def _repository_nodes(self, root: Path = ROOT) -> set[str]:
        nodes = json.loads(
            (root / "registry/ecosystem/nodes.json").read_text(encoding="utf-8")
        )["nodes"]
        return {item["id"] for item in nodes if item["type"] == "repository"}

    def _validate(self, root: Path = ROOT):
        nodes = self._repository_nodes(root)
        return validate_scope(root, nodes, validate_coverage(root, nodes))

    def test_all_organization_repositories_are_classified(self) -> None:
        scope = self._validate()
        self.assertEqual(len(scope["repositories"]), 35)
        self.assertEqual(
            sum(row["classification"] == "catalog" for row in scope["repositories"]),
            32,
        )
        self.assertEqual(
            {
                row["name"]
                for row in scope["repositories"]
                if row["classification"] == "archived_reference"
            },
            {"heimlern"},
        )
        self.assertEqual(
            {
                row["name"]
                for row in scope["repositories"]
                if row["classification"] == "excluded"
            },
            {"demo-repository", "vault-privat"},
        )

    def test_unclassified_snapshot_repository_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            shutil.copytree(
                ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            path = target / "registry/ecosystem/organization-scope.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["repositories"].pop()
            data["source"]["repositoryCount"] -= 1
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                OrganizationScopeError, "organization catalog coverage mismatch"
            ):
                self._validate(target)

    def test_exclusion_may_not_reference_catalog_node(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            shutil.copytree(
                ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            path = target / "registry/ecosystem/organization-scope.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            demo = next(row for row in data["repositories"] if row["name"] == "demo-repository")
            demo["node"] = "repo:demo-repository"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                OrganizationScopeError, "excluded node must be null"
            ):
                self._validate(target)

    def test_full_github_inventory_matches_snapshot(self) -> None:
        scope = load_scope(ROOT)
        inventory = [
            {
                "name": row["name"],
                "nameWithOwner": row["repository"],
                "visibility": row["visibility"].upper(),
                "isArchived": row["classification"] == "archived_reference",
                "isFork": False,
            }
            for row in scope["repositories"]
        ]
        self.assertEqual(validate_github_inventory(scope, inventory), 35)

    def test_public_github_drift_fails_closed(self) -> None:
        scope = load_scope(ROOT)
        inventory = [
            {
                "name": row["name"],
                "nameWithOwner": row["repository"],
                "visibility": row["visibility"].upper(),
                "isArchived": row["classification"] == "archived_reference",
                "isFork": False,
            }
            for row in scope["repositories"]
            if row["visibility"] == "public" and row["name"] != "demo-repository"
        ]
        with self.assertRaisesRegex(
            OrganizationScopeError, "missing=.*demo-repository"
        ):
            validate_github_inventory(scope, inventory, visibility="public")

    def test_archived_reference_mismatch_fails_closed(self) -> None:
        scope = load_scope(ROOT)
        inventory = [
            {
                "name": row["name"],
                "nameWithOwner": row["repository"],
                "visibility": row["visibility"].upper(),
                "isArchived": False,
                "isFork": False,
            }
            for row in scope["repositories"]
        ]
        with self.assertRaisesRegex(
            OrganizationScopeError, "identity or visibility drift: .*heimlern"
        ):
            validate_github_inventory(scope, inventory)


if __name__ == "__main__":
    unittest.main()
