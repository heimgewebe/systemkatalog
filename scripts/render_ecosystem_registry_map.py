#!/usr/bin/env python3
"""Render the Cabinet ecosystem registry as a deterministic Mermaid projection.

This is a projection, not a new truth source. The canonical input is the
versioned registry under ``registry/ecosystem``. GitHub, CI, runtime and human
release decisions remain primary truth sources in their own domains.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import difflib
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = Path("rendered/ecosystem-registry-map.mmd")
GENERATOR = "scripts/render_ecosystem_registry_map.py"
GENERATED_FILE_MODE = 0o644
MERMAID_ID_RE = re.compile(r"[^A-Za-z0-9_]+")
NODE_REQUIRED_FIELDS = ("id", "kind", "label", "status")
EDGE_REQUIRED_FIELDS = ("from", "to", "type", "status")
VISUAL_ANCHOR_NODE_IDS = ("repo:cabinet", "artifact:ecosystem-map")

KIND_ORDER = [
    "human",
    "repository",
    "concept",
    "artifact",
    "service",
    "runtime",
    "agent",
]
KIND_TITLES = {
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
    registry = repo_root / "registry" / "ecosystem"
    nodes_doc = load_json(registry / "nodes.json")
    edges_doc = load_json(registry / "edges.json")
    raw_nodes = nodes_doc.get("nodes")
    raw_edges = edges_doc.get("edges")
    if not isinstance(raw_nodes, list):
        raise RegistryMapError("nodes.json field nodes must be a list")
    if not isinstance(raw_edges, list):
        raise RegistryMapError("edges.json field edges must be a list")
    nodes = [validate_node(node, index) for index, node in enumerate(raw_nodes, start=1)]
    edges = [validate_edge(edge, index) for index, edge in enumerate(raw_edges, start=1)]
    return nodes, edges


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
    present = {str(node.get("kind", "unknown")) for node in nodes}
    ordered = [kind for kind in KIND_ORDER if kind in present]
    extras = sorted(present - set(KIND_ORDER))
    return ordered + extras


def render_mermaid(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    node_ids: dict[str, str] = {}
    for index, raw_node in enumerate(nodes, start=1):
        node = validate_node(raw_node, index)
        raw_id = node["id"]
        rendered_id = mermaid_id(raw_id)
        if rendered_id in node_ids.values():
            raise RegistryMapError(f"node id collision after Mermaid normalization: {raw_id}")
        node_ids[raw_id] = rendered_id

    lines = [
        "flowchart TD",
        "    %% GENERATED FILE. Do not edit manually.",
        f"    %% GENERATED: {GENERATOR}",
        f"    %% Run: python3 {GENERATOR}",
        "    %% Source: registry/ecosystem/nodes.json + registry/ecosystem/edges.json",
        "    %% Boundary: this projection does not establish claim truth, runtime correctness or merge readiness.",
        "",
    ]

    nodes_by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in sorted(nodes, key=lambda item: (str(item.get("kind", "")), str(item.get("id", "")))):
        nodes_by_kind[str(node.get("kind", "unknown"))].append(node)

    for kind in ordered_kinds(nodes):
        title = KIND_TITLES.get(kind, kind)
        group_id = mermaid_id(f"kind:{kind}")
        lines.append(f"    subgraph {group_id}[{escape_label(title)}]")
        for node in nodes_by_kind.get(kind, []):
            lines.append(f"        {node_ids[node['id']]}[\"{node_label(node)}\"]")
        lines.append("    end")
        lines.append("")

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

    visual_anchor_nodes = [node_ids[node_id] for node_id in VISUAL_ANCHOR_NODE_IDS if node_id in node_ids]
    if visual_anchor_nodes:
        lines.extend(
            [
                "",
                "    %% Visual anchor only; does not establish canonical truth.",
                "    classDef mapAnchor stroke-width:2px;",
                f"    class {','.join(visual_anchor_nodes)} mapAnchor;",
            ]
        )
    lines.append("")
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Mermaid output path")
    parser.add_argument("--check", action="store_true", help="verify generated Mermaid projection")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        output = resolve_output(repo_root, args.output)
        nodes, edges = load_registry(repo_root)
        content = render_mermaid(nodes, edges)
        if args.check:
            if check_file(output, content):
                print(f"Ecosystem registry Mermaid: PASS ({len(nodes)} nodes, {len(edges)} edges)")
                return 0
            return 1
        atomic_write(output, content)
        print(f"Ecosystem registry Mermaid written ({len(nodes)} nodes, {len(edges)} edges)")
        return 0
    except (RegistryMapError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
