#!/usr/bin/env python3
"""Deterministic read-only queries over the versioned Systemkatalog registry."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: root must be an object")
    return value


def _commit(root: Path) -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True)
    candidate = result.stdout.strip() if result.returncode == 0 else ""
    return candidate if len(candidate) == 40 else None


def _normal(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _data(root: Path) -> dict[str, Any]:
    nodes = _load(root, "registry/ecosystem/nodes.json")["nodes"]
    edges = _load(root, "registry/ecosystem/edges.json")["edges"]
    authority = _load(root, "registry/ecosystem/authority-matrix.v1.json")["authorities"]
    sources = _load(root, "registry/ecosystem/source-bindings.v1.json")
    return {
        "nodes": nodes,
        "edges": edges,
        "authorities": authority,
        "sourceBySystem": {item["system"]: item for item in sources["systems"]},
        "sourceByRelation": {
            (item["relation"]["from"], item["relation"]["to"], item["relation"]["type"]): item
            for item in sources["relations"]
        },
    }


def _node(data: dict[str, Any], query: str) -> dict[str, Any]:
    wanted = _normal(query)
    matches = []
    for node in data["nodes"]:
        aliases = {node["id"], node["name"]}
        if node["type"] == "repository":
            aliases.add(node["entrypoints"]["repository"].rstrip("/").split("/")[-1])
        if wanted in {_normal(alias) for alias in aliases}:
            matches.append(node)
    if len(matches) != 1:
        raise LookupError(f"system query must resolve exactly once: {query} ({len(matches)} matches)")
    return matches[0]


def _envelope(root: Path, command: str, result: Any) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_query_result",
        "command": command,
        "catalogRepository": "heimgewebe/systemkatalog",
        "catalogCommit": _commit(root),
        "result": result,
        "sourcePaths": [
            "registry/ecosystem/nodes.json",
            "registry/ecosystem/edges.json",
            "registry/ecosystem/authority-matrix.v1.json",
            "registry/ecosystem/source-bindings.v1.json",
        ],
        "doesNotEstablish": ["runtime_health", "task_status", "merge_readiness", "execution_permission"],
    }


def query(root: Path, command: str, value: str) -> dict[str, Any]:
    data = _data(root)
    if command in {"system", "repository", "entrypoints", "relations"}:
        node = _node(data, value)
    if command == "system":
        result = {"system": node, "sourceBinding": data["sourceBySystem"][node["id"]]}
    elif command == "repository":
        if node["type"] != "repository":
            raise LookupError(f"not a repository system: {node['id']}")
        result = {
            "system": node,
            "repository": node["entrypoints"]["repository"],
            "sourceBinding": data["sourceBySystem"][node["id"]],
        }
    elif command == "entrypoints":
        result = {
            "system": {"id": node["id"], "name": node["name"], "type": node["type"]},
            "entrypoints": node["entrypoints"],
            "sourceBinding": data["sourceBySystem"][node["id"]],
        }
    elif command == "relations":
        relations = []
        for edge in data["edges"]:
            if node["id"] not in {edge["from"], edge["to"]}:
                continue
            key = (edge["from"], edge["to"], edge["type"])
            relations.append({"relation": edge, "sourceBinding": data["sourceByRelation"][key]})
        result = {"system": {"id": node["id"], "name": node["name"]}, "relations": relations}
    elif command == "truth-owner":
        matches = [item for item in data["authorities"] if _normal(item["domain"]) == _normal(value)]
        if len(matches) != 1:
            raise LookupError(f"truth-owner query must resolve exactly once: {value} ({len(matches)} matches)")
        authority = matches[0]
        owners = [candidate for candidate in data["nodes"] if authority["domain"] in candidate["truthOwnership"]]
        owner = owners[0] if len(owners) == 1 else None
        result = {
            "authority": authority,
            "ownerSystem": owner,
            "ownerSourceBinding": data["sourceBySystem"].get(owner["id"]) if owner else None,
        }
    else:
        raise ValueError(f"unsupported command: {command}")
    return _envelope(root, command, result)


def _text(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_text(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {item}")
        return "\n".join(lines)
    if isinstance(value, list):
        return "\n".join(f"{prefix}- {_text(item, indent + 2).lstrip()}" for item in value)
    return f"{prefix}{value}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("system", "repository", "entrypoints", "relations", "truth-owner"):
        child = sub.add_parser(name)
        child.add_argument("value")
    args = parser.parse_args()
    try:
        result = query(args.root.resolve(), args.command, args.value)
    except (LookupError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"kind": "system_catalog_query_error", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True) if args.format == "json" else _text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
