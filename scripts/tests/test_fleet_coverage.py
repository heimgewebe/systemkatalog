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

from system_catalog_fleet import (  # noqa: E402
    FleetCoverageError,
    compare_with_source,
    load_coverage,
    parse_fleet_source,
    validate_coverage,
    validate_github_inventory,
)


class FleetCoverageTests(unittest.TestCase):
    def _repository_nodes(self, root: Path = ROOT) -> set[str]:
        nodes = json.loads(
            (root / "registry/ecosystem/nodes.json").read_text(encoding="utf-8")
        )["nodes"]
        return {item["id"] for item in nodes if item["kind"] == "repository"}

    def test_repository_coverage_is_complete(self) -> None:
        coverage = validate_coverage(ROOT, self._repository_nodes())
        self.assertEqual(len(coverage["repositories"]), 27)
        self.assertEqual(
            sum(
                item["membership"] in {"fleet", "related"}
                for item in coverage["repositories"]
            ),
            18,
        )
        self.assertEqual(coverage["sourceExclusions"][0]["name"], "vault-privat")

    def test_parser_and_comparison_accept_authority_shape(self) -> None:
        source_text = """---
static:
  include:
    - name: weltgewebe
      url: "https://github.com/heimgewebe/weltgewebe"
      status: related
    - name: vault-privat
      status: related
      fleet: false
repos:
  - name: metarepo
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repos.yml"
            path.write_text(source_text, encoding="utf-8")
            source = parse_fleet_source(path)
        self.assertEqual(
            source, ({"weltgewebe": "related", "metarepo": "fleet"}, {"vault-privat"})
        )

    def test_missing_fleet_repository_fails_closed(self) -> None:
        coverage = load_coverage(ROOT)
        source = (
            {
                **{
                    item["repository"].split("/", 1)[1]: item["membership"]
                    for item in coverage["repositories"]
                    if item["membership"] in {"fleet", "related"}
                },
                "new-repository": "fleet",
            },
            {item["name"] for item in coverage["sourceExclusions"]},
        )
        with self.assertRaisesRegex(FleetCoverageError, "missing=.*new-repository"):
            compare_with_source(coverage, source)

    def test_repository_node_without_mapping_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            shutil.copytree(
                ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            nodes = self._repository_nodes(target) | {"repo:unmapped"}
            with self.assertRaisesRegex(
                FleetCoverageError, "repository coverage mismatch"
            ):
                validate_coverage(target, nodes)

    def test_wrong_authority_owner_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            shutil.copytree(
                ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            path = target / "registry/ecosystem/fleet-coverage.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["membershipAuthority"]["repository"] = "heimgewebe/systemkatalog"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                FleetCoverageError, "membership authority mismatch"
            ):
                validate_coverage(target, self._repository_nodes(target))

    def test_github_inventory_shape_can_resolve_every_mapping(self) -> None:
        coverage = load_coverage(ROOT)
        inventory = [
            {"nameWithOwner": item["repository"], "isArchived": False}
            for item in coverage["repositories"]
        ]
        self.assertEqual(validate_github_inventory(coverage, inventory), 27)

    def test_missing_github_repository_fails_closed(self) -> None:
        coverage = load_coverage(ROOT)
        inventory = [
            {"nameWithOwner": item["repository"], "isArchived": False}
            for item in coverage["repositories"][1:]
        ]
        with self.assertRaisesRegex(FleetCoverageError, "GitHub reference drift"):
            validate_github_inventory(coverage, inventory)

    def test_non_array_github_inventory_fails_closed(self) -> None:
        with self.assertRaisesRegex(FleetCoverageError, "must be an array"):
            validate_github_inventory(load_coverage(ROOT), {})

    def test_unknown_top_level_fleet_section_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repos.yml"
            path.write_text("repos:\n  - name: metarepo\nunknown:\n  value: true\n", encoding="utf-8")
            with self.assertRaisesRegex(FleetCoverageError, "unsupported Fleet YAML"):
                parse_fleet_source(path)


if __name__ == "__main__":
    unittest.main()
