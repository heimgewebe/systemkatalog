"""Contract tests for CAB-ECO-002 ecosystem graph generation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ecosystem_graph import (  # noqa: E402
    build_graph,
    main as graph_main,
    node_from_record,
)
from repository_inventory import RepositoryRecord  # noqa: E402


def sample_record(
    *,
    repository: str = "bureau",
    role: str | None = "Operative task orchestration.",
    relationship: str = "identisch",
    import_worktree: str = "clean:0",
) -> RepositoryRecord:
    return RepositoryRecord(
        repository=repository,
        role=role,
        origin="github.com:heimgewebe/bureau.git",
        default_branch="main",
        review_head="a" * 40,
        import_head="a" * 40,
        relationship=relationship,
        import_worktree=import_worktree,
        imported_at="2026-06-23T18:38:45.731368+00:00",
        source_path="werkstatt/20 Werkzeuge/Bureau/Repository Reference.md",
    )


class EcosystemGraphTests(unittest.TestCase):
    def test_node_from_record_uses_ecosystem_node_contract(self) -> None:
        node = node_from_record(sample_record())
        self.assertEqual(node["schemaVersion"], 1)
        self.assertEqual(node["kind"], "ecosystem_node")
        self.assertEqual(node["id"], "repo:bureau")
        self.assertEqual(node["nodeType"], "repository")
        self.assertEqual(node["status"], "observed")
        self.assertEqual(node["roles"], ["Operative task orchestration."])
        self.assertEqual(node["freshness"]["class"], "dated_snapshot")
        self.assertEqual(node["sources"][0]["type"], "cabinet")
        self.assertEqual(node["sources"][1]["type"], "git")

    def test_node_marks_drift_and_dirty_import_worktree_as_health_dimensions(self) -> None:
        node = node_from_record(
            sample_record(
                relationship="divergent oder rewritten/amended",
                import_worktree="dirty:6",
            )
        )
        self.assertIn("review_import_drift", node["healthDimensions"])
        self.assertIn("dirty_import_worktree", node["healthDimensions"])

    def test_build_graph_is_deterministic_and_sorted(self) -> None:
        graph = build_graph(
            [
                sample_record(repository="weltgewebe"),
                sample_record(repository="bureau"),
            ]
        )
        self.assertEqual(graph["schemaVersion"], 1)
        self.assertEqual(graph["kind"], "ecosystem_graph")
        self.assertEqual(graph["source"]["trackedReferences"], 2)
        self.assertEqual(
            [node["id"] for node in graph["nodes"]],
            ["repo:bureau", "repo:weltgewebe"],
        )
        self.assertIn("absence_of_drift", graph["source"]["doesNotClaim"])

    def test_generated_graph_file_is_valid_json(self) -> None:
        graph_path = ROOT / "steuerung/10 Lage/ecosystem-graph.json"
        with graph_path.open(encoding="utf-8") as handle:
            value: Any = json.load(handle)
        self.assertEqual(value["schemaVersion"], 1)
        self.assertEqual(value["kind"], "ecosystem_graph")
        self.assertGreaterEqual(len(value["nodes"]), 1)

    def test_check_mode_accepts_tracked_generated_artifacts(self) -> None:
        self.assertEqual(graph_main(["--repo-root", str(ROOT), "--check"]), 0)

    def test_output_path_may_not_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary) / "graph.json"
            self.assertEqual(
                graph_main(
                    [
                        "--repo-root",
                        str(ROOT),
                        "--output",
                        str(outside),
                    ]
                ),
                2,
            )


if __name__ == "__main__":
    unittest.main()
