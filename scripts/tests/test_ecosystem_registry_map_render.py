from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from render_ecosystem_registry_map import (  # noqa: E402
    MermaidRenderer,
    ProjectionConfigLoader,
    ProjectionViewConfig,
    RegistryData,
    RegistryMapError,
    load_registry,
    mermaid_id,
    render_mermaid,
    run_projection,
)


def node(
    node_id: str,
    node_type: str = "repository",
    name: str = "Systemkatalog",
    purpose: str = "stable purpose",
) -> dict[str, object]:
    return {
        "id": node_id,
        "name": name,
        "type": node_type,
        "purpose": purpose,
        "notResponsibleFor": ["runtime state"],
        "truthOwnership": [],
        "entrypoints": {"repository": "https://example.invalid/system"},
    }


def edge(source: str, target: str, relation: str = "owns", stability: str = "stable") -> dict[str, str]:
    return {"from": source, "to": target, "type": relation, "stability": stability, "meaning": "bounded meaning"}


class EcosystemRegistryMapTests(unittest.TestCase):
    def test_mermaid_id_is_deterministic(self) -> None:
        self.assertEqual(mermaid_id("repo:systemkatalog"), "repo_systemkatalog")

    def test_render_has_single_systemkatalog_anchor(self) -> None:
        nodes = [node("repo:systemkatalog"), node("artifact:ecosystem-map", "artifact", "Ecosystem Map")]
        rendered = render_mermaid(nodes, [edge("repo:systemkatalog", "artifact:ecosystem-map")])
        self.assertIn("repo_systemkatalog -->|owns / stable| artifact_ecosystem_map", rendered)
        self.assertIn("class repo_systemkatalog,artifact_ecosystem_map mapAnchor", rendered)
        self.assertNotIn("heimgewebe_katalog", rendered)

    def test_unknown_edge_endpoint_fails_closed(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, "unknown to node"):
            render_mermaid([node("repo:systemkatalog")], [edge("repo:systemkatalog", "repo:missing")])

    def test_projection_config_requires_neutral_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "view.json"
            path.write_text(json.dumps({"kind": "old", "authoritative": False}), encoding="utf-8")
            with self.assertRaisesRegex(RegistryMapError, "kind mismatch"):
                ProjectionConfigLoader(root, path).load()

    def test_repository_projection_is_current(self) -> None:
        nodes, edges = load_registry(ROOT)
        config = ProjectionConfigLoader(ROOT, Path("policy/ecosystem-map-view.v1.json")).load()
        rendered = MermaidRenderer(config).render(RegistryData(nodes=nodes, edges=edges))
        actual = (ROOT / "rendered/ecosystem-registry-map.mmd").read_text(encoding="utf-8")
        self.assertEqual(actual, rendered)
        report = run_projection(ROOT, ROOT / "rendered/ecosystem-registry-map.mmd", Path("policy/ecosystem-map-view.v1.json"), True)
        self.assertTrue(report.ok)
        self.assertFalse(report.stale)


if __name__ == "__main__":
    unittest.main()
