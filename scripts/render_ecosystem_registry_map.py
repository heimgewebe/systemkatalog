#!/usr/bin/env python3
"""Render the Cabinet ecosystem registry as a deterministic Mermaid projection.

This is a projection, not a new truth source. The canonical input is the
versioned registry under ``registry/ecosystem``. GitHub, CI, runtime and human
release decisions remain primary truth sources in their own domains.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import difflib
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

DEFAULT_OUTPUT = Path("rendered/ecosystem-registry-map.mmd")
DEFAULT_VIEW_CONFIG = Path("docs/blueprints/o.json")
GENERATOR = "scripts/render_ecosystem_registry_map.py"
GENERATED_FILE_MODE = 0o644
MERMAID_ID_RE = re.compile(r"[^A-Za-z0-9_]+")
NODE_REQUIRED_FIELDS = ("id", "kind", "label", "status")
EDGE_REQUIRED_FIELDS = ("from", "to", "type", "status")
DEFAULT_VISUAL_ANCHOR_NODE_IDS = ("repo:cabinet", "artifact:ecosystem-map")

DEFAULT_KIND_ORDER = (
    "human",
    "repository",
    "concept",
    "artifact",
    "service",
    "runtime",
    "agent",
)
DEFAULT_KIND_TITLES = {
    "human": "Menschen und Entscheidung",
    "repository": "Repos und Organe",
    "concept": "Konzepte",
    "artifact": "Artefakte",
    "service": "Primaere Dienste",
    "runtime": "Runtime",
    "agent": "Agenten",
}


class RegistryMapError(RuntimeError):
    """Raised when registry rendering cannot proceed safely."""


@dataclass(frozen=True)
class RegistryData:
    """Validated ecosystem registry inputs."""

    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@dataclass(frozen=True)
class ProjectionViewConfig:
    """Display-only settings for the generated Mermaid projection."""

    kind_order: tuple[str, ...] = DEFAULT_KIND_ORDER
    kind_titles: dict[str, str] | None = None
    visual_anchor_node_ids: tuple[str, ...] = DEFAULT_VISUAL_ANCHOR_NODE_IDS

    def title_for(self, kind: str) -> str:
        titles = self.kind_titles or DEFAULT_KIND_TITLES
        return titles.get(kind, kind)


@dataclass(frozen=True)
class ProjectionRunReport:
    """Machine-readable result for CI and agent callers."""

    ok: bool
    mode: Literal["write", "check"]
    output: str
    node_count: int
    edge_count: int
    stale: bool
    message: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "mode": self.mode,
                "output": self.output,
                "node_count": self.node_count,
                "edge_count": self.edge_count,
                "stale": self.stale,
                "message": self.message,
                "does_not_establish": [
                    "claim_truth",
                    "runtime_correctness",
                    "merge_readiness",
                    "primary_source_freshness",
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n"


class RegistryLoader:
    """Load and minimally validate the ecosystem registry."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.registry = repo_root / "registry" / "ecosystem"

    def load(self) -> RegistryData:
        nodes_doc = load_json(self.registry / "nodes.json")
        edges_doc = load_json(self.registry / "edges.json")
        raw_nodes = nodes_doc.get("nodes")
        raw_edges = edges_doc.get("edges")
        if not isinstance(raw_nodes, list):
            raise RegistryMapError("nodes.json field nodes must be a list")
        if not isinstance(raw_edges, list):
            raise RegistryMapError("edges.json field edges must be a list")
        nodes = [validate_node(node, index) for index, node in enumerate(raw_nodes, start=1)]
        edges = [validate_edge(edge, index) for index, edge in enumerate(raw_edges, start=1)]
        return RegistryData(nodes=nodes, edges=edges)


class ProjectionConfigLoader:
    """Load optional view settings without changing registry truth semantics."""

    def __init__(self, repo_root: Path, config_path: Path) -> None:
        self.repo_root = repo_root
        self.config_path = config_path

    def load(self) -> ProjectionViewConfig:
        path = self._resolve_config_path()
        if not path.is_file():
            return ProjectionViewConfig(kind_titles=dict(DEFAULT_KIND_TITLES))
        doc = load_json(path)
        raw_config = doc.get("ecosystem_map_v0", {}).get("registry_projection_view", {})
        if raw_config in ({}, None):
            return ProjectionViewConfig(kind_titles=dict(DEFAULT_KIND_TITLES))
        if not isinstance(raw_config, dict):
            raise RegistryMapError("registry_projection_view must be an object")
        return ProjectionViewConfig(
            kind_order=load_string_tuple(raw_config.get("kind_order"), "registry_projection_view.kind_order", DEFAULT_KIND_ORDER),
            kind_titles=load_string_dict(raw_config.get("kind_titles"), "registry_projection_view.kind_titles", DEFAULT_KIND_TITLES),
            visual_anchor_node_ids=load_string_tuple(
                raw_config.get("visual_anchor_node_ids"),
                "registry_projection_view.visual_anchor_node_ids",
                DEFAULT_VISUAL_ANCHOR_NODE_IDS,
            ),
        )

    def _resolve_config_path(self) -> Path:
        raw_path = self.config_path
        resolved = raw_path.resolve() if raw_path.is_absolute() else (self.repo_root / raw_path).resolve()
        try:
            resolved.relative_to(self.repo_root)
        except ValueError as exc:
            raise RegistryMapError(f"config path escapes repository: {resolved}") from exc
        return resolved


class MermaidRenderer:
    """Render validated registry data into Mermaid."""

    def __init__(self, config: ProjectionViewConfig) -> None:
        self.config = config

    def render(self, registry: RegistryData) -> str:
        node_ids = self._node_ids(registry.nodes)
        lines = [
            "flowchart TD",
            "    %% GENERATED FILE. Do not edit manually.",
            f"    %% GENERATED: {GENERATOR}",
            f"    %% Run: python3 {GENERATOR}",
            "    %% Source: registry/ecosystem/nodes.json + registry/ecosystem/edges.json",
            "    %% Boundary: this projection does not establish claim truth, runtime correctness or merge readiness.",
            "",
        ]
        lines.extend(self._render_nodes(registry.nodes, node_ids))
        lines.extend(self._render_edges(registry.edges, node_ids))
        lines.extend(self._render_visual_anchors(node_ids))
        lines.append("")
        return "\n".join(lines)

    def _node_ids(self, nodes: list[dict[str, Any]]) -> dict[str, str]:
        node_ids: dict[str, str] = {}
        for index, raw_node in enumerate(nodes, start=1):
            node = validate_node(raw_node, index)
            raw_id = node["id"]
            rendered_id = mermaid_id(raw_id)
            if rendered_id in node_ids.values():
                raise RegistryMapError(f"node id collision after Mermaid normalization: {raw_id}")
            node_ids[raw_id] = rendered_id
        return node_ids

    def _render_nodes(self, nodes: list[dict[str, Any]], node_ids: dict[str, str]) -> list[str]:
        lines: list[str] = []
        nodes_by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in sorted(nodes, key=lambda item: (str(item.get("kind", "")), str(item.get("id", "")))):
            nodes_by_kind[str(node.get("kind", "unknown"))].append(node)

        for kind in self._ordered_kinds(nodes):
            title = self.config.title_for(kind)
            group_id = mermaid_id(f"kind:{kind}")
            lines.append(f"    subgraph {group_id}[{escape_label(title)}]")
            for node in nodes_by_kind.get(kind, []):
                lines.append(f"        {node_ids[node['id']]}[\"{node_label(node)}\"]")
            lines.append("    end")
            lines.append("")
        return lines

    def _ordered_kinds(self, nodes: list[dict[str, Any]]) -> list[str]:
        present = {str(node.get("kind", "unknown")) for node in nodes}
        ordered = [kind for kind in self.config.kind_order if kind in present]
        extras = sorted(present - set(self.config.kind_order))
        return ordered + extras

    def _render_edges(self, edges: list[dict[str, Any]], node_ids: dict[str, str]) -> list[str]:
        lines: list[str] = []
        for index, raw_edge in enumerate(
            sorted(edges, key=lambda item: (str(item.get("from", "")), str(item.get("to", "")), str(item.get("type", "")))),
            start=1,
        ):
            edge = validate_edge(raw_edge, index)
            source = edge["from"]
            target = edge["to"]
            if source not in node_ids:
                raise RegistryMapError(f"edge {index} references unknown from node: {source}")
            if target not in node_ids:
                raise RegistryMapError(f"edge {index} references unknown to node: {target}")
            edge_type = escape_label(edge["type"])
            status = escape_label(edge["status"])
            lines.append(f"    {node_ids[source]} -->|{edge_type} / {status}| {node_ids[target]}")
        return lines

    def _render_visual_anchors(self, node_ids: dict[str, str]) -> list[str]:
        visual_anchor_nodes = [node_ids[node_id] for node_id in self.config.visual_anchor_node_ids if node_id in node_ids]
        if not visual_anchor_nodes:
            return []
        return [
            "",
            "    %% Visual anchor only; does not establish canonical truth.",
            "    classDef mapAnchor stroke-width:2px;",
            f"    class {','.join(visual_anchor_nodes)} mapAnchor;",
        ]


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RegistryMapError(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise RegistryMapError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryMapError(f"{path} must contain a JSON object")
    return value


def load_string_tuple(value: Any, label: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list):
        raise RegistryMapError(f"{label} must be a list")
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item:
            raise RegistryMapError(f"{label} item {index} must be a non-empty string")
        result.append(item)
    if len(set(result)) != len(result):
        raise RegistryMapError(f"{label} must not contain duplicates")
    return tuple(result)


def load_string_dict(value: Any, label: str, default: dict[str, str]) -> dict[str, str]:
    if value is None:
        return dict(default)
    if not isinstance(value, dict):
        raise RegistryMapError(f"{label} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise RegistryMapError(f"{label} keys must be non-empty strings")
        if not isinstance(item, str) or not item:
            raise RegistryMapError(f"{label}.{key} must be a non-empty string")
        result[key] = item
    return result


def require_text_field(item: dict[str, Any], field: str, label: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        raise RegistryMapError(f"{label} missing required string field: {field}")
    return value


def validate_node(raw_node: Any, index: int) -> dict[str, Any]:
    label = f"node {index}"
    if not isinstance(raw_node, dict):
        raise RegistryMapError(f"{label} must be an object")
    for field in NODE_REQUIRED_FIELDS:
        require_text_field(raw_node, field, label)
    return raw_node


def validate_edge(raw_edge: Any, index: int) -> dict[str, Any]:
    label = f"edge {index}"
    if not isinstance(raw_edge, dict):
        raise RegistryMapError(f"{label} must be an object")
    for field in EDGE_REQUIRED_FIELDS:
        require_text_field(raw_edge, field, label)
    return raw_edge


def load_registry(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry = RegistryLoader(repo_root).load()
    return registry.nodes, registry.edges


def mermaid_id(node_id: str) -> str:
    value = MERMAID_ID_RE.sub("_", node_id).strip("_")
    if not value:
        raise RegistryMapError("empty node id cannot be rendered")
    if value[0].isdigit():
        value = f"n_{value}"
    return value


def escape_label(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return html.escape(text, quote=True)


def node_label(node: dict[str, Any]) -> str:
    label = escape_label(node["label"])
    node_id = escape_label(node["id"])
    kind = escape_label(node["kind"])
    status = escape_label(node["status"])
    return f"{label}<br/>id: {node_id}<br/>{kind}<br/>status: {status}"


def ordered_kinds(nodes: list[dict[str, Any]]) -> list[str]:
    return MermaidRenderer(ProjectionViewConfig(kind_titles=dict(DEFAULT_KIND_TITLES)))._ordered_kinds(nodes)


def render_mermaid(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    registry = RegistryData(nodes=nodes, edges=edges)
    return MermaidRenderer(ProjectionViewConfig(kind_titles=dict(DEFAULT_KIND_TITLES))).render(registry)


def resolve_output(repo_root: Path, raw_output: str) -> Path:
    raw_path = Path(raw_output)
    output = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
    try:
        output.relative_to(repo_root)
    except ValueError as exc:
        raise RegistryMapError(f"output path escapes repository: {output}") from exc
    return output


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            os.fchmod(handle.fileno(), GENERATED_FILE_MODE)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def limited_diff(current: str, expected: str, path: Path) -> str:
    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile=str(path),
            tofile=f"{path} (expected)",
            lineterm="",
        )
    )
    limit = 200
    if len(diff) > limit:
        diff = diff[:limit] + [f"... diff truncated after {limit} lines ..."]
    return "\n".join(diff)


def check_file(path: Path, expected: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    if current == expected:
        return True
    print(f"ERROR: ecosystem registry Mermaid projection is stale: {path}", file=sys.stderr)
    print(limited_diff(current, expected, path), file=sys.stderr)
    return False


def run_projection(repo_root: Path, output: Path, config_path: Path, check: bool) -> ProjectionRunReport:
    registry = RegistryLoader(repo_root).load()
    config = ProjectionConfigLoader(repo_root, config_path).load()
    content = MermaidRenderer(config).render(registry)
    if check:
        ok = check_file(output, content)
        message = (
            f"Ecosystem registry Mermaid: PASS ({len(registry.nodes)} nodes, {len(registry.edges)} edges)"
            if ok
            else "Ecosystem registry Mermaid: STALE"
        )
        return ProjectionRunReport(
            ok=ok,
            mode="check",
            output=str(output),
            node_count=len(registry.nodes),
            edge_count=len(registry.edges),
            stale=not ok,
            message=message,
        )
    atomic_write(output, content)
    return ProjectionRunReport(
        ok=True,
        mode="write",
        output=str(output),
        node_count=len(registry.nodes),
        edge_count=len(registry.edges),
        stale=False,
        message=f"Ecosystem registry Mermaid written ({len(registry.nodes)} nodes, {len(registry.edges)} edges)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Mermaid output path")
    parser.add_argument("--view-config", default=str(DEFAULT_VIEW_CONFIG), help="optional projection view config")
    parser.add_argument("--check", action="store_true", help="verify generated Mermaid projection")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--json", action="store_true", help="shortcut for --format json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    report_format = "json" if args.json else args.format
    try:
        output = resolve_output(repo_root, args.output)
        config_path = Path(args.view_config)
        report = run_projection(repo_root, output, config_path, bool(args.check))
        if report_format == "json":
            print(report.to_json(), end="")
        else:
            print(report.message)
        return 0 if report.ok else 1
    except (RegistryMapError, OSError, UnicodeError) as exc:
        if report_format == "json":
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(exc),
                        "mode": "check" if args.check else "write",
                        "output": str(args.output),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
