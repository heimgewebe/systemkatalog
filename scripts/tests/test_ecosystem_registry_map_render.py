"""Tests for the registry-derived Mermaid ecosystem projection."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from render_ecosystem_registry_map import (  # noqa: E402
    RegistryMapError,
    main as render_main,
    mermaid_id,
    render_mermaid,
)


class EcosystemRegistryMapRenderTests(unittest.TestCase):
    def test_mermaid_id_normalizes_registry_ids(self) -> None:
        self.assertEqual(mermaid_id("repo:cabinet"), "repo_cabinet")
        self.assertEqual(mermaid_id("runtime:heim-pc"), "runtime_heim_pc")
        self.assertEqual(mermaid_id("123:node"), "n_123_node")

    def test_render_mermaid_preserves_registry_boundary_and_edge_status(self) -> None:
        nodes = [
            {
                "id": "actor:alexander",
                "kind": "human",
                "label": "Alexander",
                "status": "active",
            },
            {
                "id": "repo:cabinet",
                "kind": "repository",
                "label": "Cabinet",
                "status": "active",
            },
            {
                "id": "artifact:ecosystem-map",
                "kind": "artifact",
                "label": "Ecosystem Map v0",
                "status": "draft",
            },
        ]
        edges = [
            {
                "from": "actor:alexander",
                "to": "repo:cabinet",
                "type": "steers",
                "status": "active",
            },
            {
                "from": "repo:cabinet",
                "to": "artifact:ecosystem-map",
                "type": "owns",
                "status": "draft",
            },
        ]
        rendered = render_mermaid(nodes, edges)
        self.assertTrue(rendered.startswith("flowchart TD\n"))
        self.assertIn("GENERATED: scripts/render_ecosystem_registry_map.py", rendered)
        self.assertIn("does not establish claim truth", rendered)
        self.assertIn("actor_alexander -->|steers / active| repo_cabinet", rendered)
        self.assertIn("repo_cabinet -->|owns / draft| artifact_ecosystem_map", rendered)

    def test_render_mermaid_rejects_edges_to_unknown_nodes(self) -> None:
        nodes = [
            {
                "id": "repo:cabinet",
                "kind": "repository",
                "label": "Cabinet",
                "status": "active",
            },
            {
                "id": "artifact:ecosystem-map",
                "kind": "artifact",
                "label": "Ecosystem Map v0",
                "status": "draft",
            },
        ]
        edges = [
            {
                "from": "repo:cabinet",
                "to": "repo:missing",
                "type": "owns",
                "status": "active",
            }
        ]
        with self.assertRaises(RegistryMapError):
            render_mermaid(nodes, edges)

    def test_check_mode_accepts_tracked_generated_projection(self) -> None:
        self.assertEqual(render_main(["--repo-root", str(ROOT), "--check"]), 0)

    def test_output_path_may_not_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary) / "ecosystem-registry-map.mmd"
            self.assertEqual(
                render_main(
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
