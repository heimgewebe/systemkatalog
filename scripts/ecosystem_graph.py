#!/usr/bin/env python3
"""Build Cabinet Ecosystem Graph v1 from tracked Repository References.

This builder intentionally reuses ``repository_inventory`` for Repository
Reference parsing. It does not inspect live source repositories and does not
claim runtime freshness. The generated graph is a dated-snapshot projection
from versioned Cabinet reference cards.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from repository_inventory import InventoryError, RepositoryRecord, load_records

DEFAULT_OUTPUT = Path("steuerung/10 Lage/ecosystem-graph.json")
DEFAULT_REPORT = Path("pruefung/10 Laeufe/ecosystem-graph-v1.md")
GRAPH_KIND = "ecosystem_graph"
GRAPH_SCHEMA_VERSION = 1
GENERATOR = "scripts/build-ecosystem-graph.py"
GENERATED_FILE_MODE = 0o644
NODE_ID_RE = re.compile(r"[^A-Za-z0-9._/-]+")


class EcosystemGraphError(RuntimeError):
    """Raised when graph generation or validation cannot proceed."""


def _node_id_for_repository(repository: str) -> str:
    slug = NODE_ID_RE.sub("-", repository.strip().lower()).strip("-")
    if not slug:
        raise EcosystemGraphError("repository name cannot be converted into a node id")
    return f"repo:{slug}"


def _source_ref(record: RepositoryRecord) -> dict[str, str]:
    return {
        "type": "cabinet",
        "ref": record.source_path,
        "observedAt": record.imported_at,
    }


def _git_ref(record: RepositoryRecord) -> dict[str, str]:
    return {
        "type": "git",
        "ref": record.import_head,
        "observedAt": record.imported_at,
    }


def _roles(record: RepositoryRecord) -> list[str]:
    return [record.role] if record.role else []


def _health_dimensions(record: RepositoryRecord) -> list[str]:
    dimensions = [
        "reference_freshness",
        "review_import_relationship",
        "import_worktree_state",
    ]
    if record.relationship.casefold() != "identisch":
        dimensions.append("review_import_drift")
    if record.import_worktree.startswith("dirty:"):
        dimensions.append("dirty_import_worktree")
    return dimensions


def node_from_record(record: RepositoryRecord) -> dict[str, Any]:
    notes = (
        f"origin={record.origin}; default_branch={record.default_branch or 'unknown'}; "
        f"review_head={record.review_head}; import_head={record.import_head}; "
        f"relationship={record.relationship}; import_worktree={record.import_worktree}"
    )
    return {
        "schemaVersion": 1,
        "kind": "ecosystem_node",
        "id": _node_id_for_repository(record.repository),
        "nodeType": "repository",
        "name": record.repository,
        "description": record.role or "Repository reference without canonical role excerpt.",
        "status": "observed",
        "roles": _roles(record),
        "healthDimensions": _health_dimensions(record),
        "links": [],
        "sources": [_source_ref(record), _git_ref(record)],
        "freshness": {
            "class": "dated_snapshot",
            "observedAt": record.imported_at,
        },
        "notes": notes,
    }


def build_graph(records: list[RepositoryRecord], warnings: list[str] | None = None) -> dict[str, Any]:
    nodes = [node_from_record(record) for record in records]
    nodes.sort(key=lambda node: (node["id"], node["name"]))
    return {
        "schemaVersion": GRAPH_SCHEMA_VERSION,
        "kind": GRAPH_KIND,
        "generatedBy": GENERATOR,
        "source": {
            "type": "cabinet_repository_references",
            "contract": "ecosystem-graph.v1",
            "trackedReferences": len(records),
            "freshnessClass": "dated_snapshot",
            "doesNotClaim": [
                "live_source_repository_state",
                "runtime_correctness",
                "ci_status",
                "merge_readiness",
                "absence_of_drift",
            ],
        },
        "nodes": nodes,
        "warnings": sorted(warnings or []),
    }


def render_graph(graph: dict[str, Any]) -> str:
    return json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_report(graph: dict[str, Any]) -> str:
    nodes = graph["nodes"]
    warnings = graph.get("warnings", [])
    lines = [
        "# Ecosystem Graph v1",
        "",
        "<!-- GENERATED: scripts/build-ecosystem-graph.py -->",
        "> **Generierte Datei. Nicht manuell bearbeiten.**",
        "> Quelle: versionierte `Repository Reference.md`-Dateien.",
        "> **Zeitgrenze:** Dieser Graph ist eine Projektion aus datierten Cabinet-Referenzen und behauptet keinen aktuellen Live-Zustand der Quell-Repositories.",
        "",
        "## Summary",
        "",
        f"- Schema-Version: `{graph['schemaVersion']}`",
        f"- Kind: `{graph['kind']}`",
        f"- Tracked references: `{graph['source']['trackedReferences']}`",
        f"- Nodes: `{len(nodes)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Nodes",
        "",
        "| Node | Name | Type | Freshness | Source |",
        "|---|---|---|---|---|",
    ]
    for node in nodes:
        source = node["sources"][0]["ref"] if node.get("sources") else "—"
        freshness = node.get("freshness", {}).get("class", "unknown")
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{node['id']}`",
                    _escape_markdown_cell(str(node["name"])),
                    f"`{node['nodeType']}`",
                    f"`{freshness}`",
                    f"`{_escape_markdown_cell(source)}`",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Does not establish",
            "",
            "- aktueller Live-Zustand der Quell-Repositories",
            "- CI-Status",
            "- Runtime-Korrektheit",
            "- Merge-Readiness",
            "- Abwesenheit von Drift",
            "",
        ]
    )
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    return "\n".join(lines)


def _escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _atomic_write(path: Path, content: str) -> None:
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


def _limited_diff(current: str, expected: str, path: Path) -> str:
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


def _resolve_output(repo_root: Path, raw: str) -> Path:
    output = Path(raw)
    resolved = output.resolve() if output.is_absolute() else (repo_root / output).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise EcosystemGraphError(f"output path escapes repository: {resolved}") from exc
    return resolved


def _check_file(path: Path, expected: str, label: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    if current == expected:
        return True
    print(f"ERROR: {label} is stale: {path}", file=sys.stderr)
    print(_limited_diff(current, expected, path), file=sys.stderr)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated artifacts")
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="graph JSON output")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown proof report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        graph_path = _resolve_output(repo_root, args.output)
        report_path = _resolve_output(repo_root, args.report)
        records, warnings = load_records(repo_root, verify_index_match=args.check)
        graph = build_graph(records, warnings)
        graph_content = render_graph(graph)
        report_content = render_report(graph)

        if args.check:
            graph_ok = _check_file(graph_path, graph_content, "ecosystem graph")
            report_ok = _check_file(report_path, report_content, "ecosystem graph report")
            if graph_ok and report_ok:
                print(
                    "Ecosystem graph: PASS "
                    f"({len(graph['nodes'])} nodes, {len(warnings)} warnings)"
                )
                return 0
            return 1

        _atomic_write(graph_path, graph_content)
        _atomic_write(report_path, report_content)
        print(
            "Ecosystem graph written "
            f"({len(graph['nodes'])} nodes, {len(warnings)} warnings)"
        )
        return 0
    except (InventoryError, EcosystemGraphError, UnicodeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
