"""Tests for the stable registry-derived Mermaid projection."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
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
    ProjectionRunReport,
    ProjectionViewConfig,
    RegistryData,
    RegistryMapError,
    main as render_main,
    mermaid_id,
    render_mermaid,
)


def node(node_id: str, kind: str = "repository", label: str = "Heimgewebe-Systemkatalog", purpose: str = "stable purpose") -> dict:
    return {"id": node_id, "kind": kind, "label": label, "purpose": purpose}


def edge(source: str, target: str, relation: str = "owns", stability: str = "stable") -> dict:
    return {"from": source, "to": target, "type": relation, "stability": stability, "meaning": "stable meaning"}


class EcosystemRegistryMapRenderTests(unittest.TestCase):
    def test_mermaid_id_normalizes_registry_ids(self) -> None:
        self.assertEqual(mermaid_id("repo:heimgewebe-katalog"), "repo_heimgewebe_katalog")
        self.assertEqual(mermaid_id("123:node"), "n_123_node")

    def test_render_mermaid_preserves_boundary_and_stability_class(self) -> None:
        nodes = [node("actor:alexander", "human", "Alexander", "approval and abort authority"), node("repo:heimgewebe-katalog"), node("artifact:ecosystem-map", "artifact", "Ecosystem Map")]
        edges = [edge("actor:alexander", "repo:heimgewebe-katalog", "steers"), edge("repo:heimgewebe-katalog", "artifact:ecosystem-map", "owns", "bounded")]
        rendered = render_mermaid(nodes, edges)
        self.assertTrue(rendered.startswith("flowchart TD\n"))
        self.assertIn("does not establish claim truth", rendered)
        self.assertIn("actor_alexander -->|steers / stable| repo_heimgewebe_katalog", rendered)
        self.assertIn("repo_heimgewebe_katalog -->|owns / bounded| artifact_ecosystem_map", rendered)
        self.assertNotIn("status:", rendered)

    def test_render_mermaid_rejects_edges_to_unknown_nodes(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, "unknown to node"):
            render_mermaid([node("repo:heimgewebe-katalog")], [edge("repo:heimgewebe-katalog", "repo:missing")])

    def test_check_mode_accepts_tracked_generated_projection(self) -> None:
        self.assertEqual(render_main(["--repo-root", str(ROOT), "--check"]), 0)

    def test_output_path_may_not_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary) / "ecosystem-registry-map.mmd"
            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = render_main(["--repo-root", str(ROOT), "--output", str(outside)])
            self.assertEqual(result, 2)
            self.assertIn("output path escapes repository", stderr.getvalue())

    def test_node_label_contains_purpose_not_operational_status(self) -> None:
        rendered = render_mermaid([node("repo:heimgewebe-katalog", purpose="app-independent catalog")], [])
        self.assertIn("Heimgewebe-Systemkatalog<br/>id: repo:heimgewebe-katalog<br/>repository<br/>app-independent catalog", rendered)
        self.assertNotIn("status:", rendered)

    def test_non_object_nodes_fail_closed(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, r"node \d+ must be an object"):
            render_mermaid(["not-an-object"], [])

    def test_missing_purpose_fails_closed(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, "missing required string field: purpose"):
            render_mermaid([{"id": "repo:heimgewebe-katalog", "kind": "repository", "label": "Heimgewebe-Systemkatalog"}], [])

    def test_non_object_edges_fail_closed_before_sorting(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, r"edge \d+ must be an object"):
            render_mermaid([node("repo:heimgewebe-katalog")], ["not-an-object"])

    def test_missing_edge_source_fails_closed(self) -> None:
        with self.assertRaisesRegex(RegistryMapError, "missing required string field: from"):
            render_mermaid([node("repo:heimgewebe-katalog")], [{"to": "repo:heimgewebe-katalog", "type": "owns", "stability": "stable"}])

    def test_missing_visual_anchor_nodes_do_not_raise(self) -> None:
        rendered = render_mermaid([node("repo:other", label="Other")], [])
        self.assertNotIn("mapAnchor", rendered)
        self.assertIn("repo_other", rendered)

    def test_visual_anchor_is_explicitly_noncanonical(self) -> None:
        rendered = render_mermaid([node("repo:heimgewebe-katalog")], [])
        self.assertIn("Visual anchor only; does not establish canonical truth.", rendered)
        self.assertIn("classDef mapAnchor", rendered)
        self.assertNotIn("classDef canon", rendered)

    def test_generated_comment_marks_manual_edit_boundary(self) -> None:
        rendered = render_mermaid([node("repo:heimgewebe-katalog")], [])
        self.assertIn("GENERATED FILE", rendered)
        self.assertIn("Do not edit manually", rendered)

    def test_projection_policy_can_reorder_groups(self) -> None:
        config = ProjectionViewConfig(kind_order=("artifact", "repository"), kind_titles={"artifact": "Artefakte", "repository": "Repos"}, visual_anchor_node_ids=())
        rendered = MermaidRenderer(config).render(RegistryData(nodes=[node("repo:heimgewebe-katalog"), node("artifact:map", "artifact", "Map")], edges=[]))
        self.assertLess(rendered.index("kind_artifact[Artefakte]"), rendered.index("kind_repository[Repos]"))

    def test_partial_kind_title_override_preserves_default_titles(self) -> None:
        config = ProjectionViewConfig(kind_titles={"repository": "Repos"})
        self.assertEqual(config.title_for("repository"), "Repos")
        self.assertEqual(config.title_for("artifact"), "Artefakte")

    def test_projection_config_loader_reads_catalog_policy(self) -> None:
        config = ProjectionConfigLoader(ROOT, Path("policy/ecosystem-map-view.v1.json")).load()
        self.assertEqual(config.kind_order, ("human", "repository", "concept", "artifact", "service"))
        self.assertEqual(config.title_for("repository"), "Repos und Organe")
        self.assertIn("repo:heimgewebe-katalog", config.visual_anchor_node_ids)

    def test_projection_config_must_be_non_authoritative(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "scripts/tests") as temporary:
            config = Path(temporary) / "bad-config.json"
            config.write_text(json.dumps({"kind": "heimgewebe_system_catalog_map_projection_policy", "authoritative": True}), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout), redirect_stderr(StringIO()):
                result = render_main(["--repo-root", str(ROOT), "--check", "--json", "--view-config", str(config.relative_to(ROOT))])
            self.assertEqual(result, 2)
            self.assertEqual(json.loads(stdout.getvalue())["error"], "view config must be explicitly non-authoritative")

    def test_json_flag_returns_success_report(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = render_main(["--repo-root", str(ROOT), "--check", "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["node_count"], 19)
        self.assertEqual(payload["edge_count"], 24)

    def test_json_error_for_malformed_projection_policy_is_stable(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "scripts/tests") as temporary:
            config = Path(temporary) / "bad-config.json"
            config.write_text(json.dumps({"kind": "wrong", "authoritative": False}), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout), redirect_stderr(StringIO()):
                result = render_main(["--repo-root", str(ROOT), "--check", "--json", "--view-config", str(config.relative_to(ROOT))])
            self.assertEqual(result, 2)
            self.assertEqual(json.loads(stdout.getvalue())["error"], "view config kind mismatch")

    def test_explicit_missing_view_config_fails_closed(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = render_main(["--repo-root", str(ROOT), "--check", "--json", "--view-config", "scripts/tests/missing-view-config.json"])
        self.assertEqual(result, 2)
        self.assertIn("view config file not found", json.loads(stdout.getvalue())["error"])

    def test_json_report_preserves_non_truth_boundary(self) -> None:
        text = ProjectionRunReport(ok=True, mode="check", output="rendered/ecosystem-registry-map.mmd", node_count=2, edge_count=1, stale=False, message="ok").to_json()
        self.assertIn('"claim_truth"', text)
        self.assertIn('"merge_readiness"', text)


if __name__ == "__main__":
    unittest.main()
