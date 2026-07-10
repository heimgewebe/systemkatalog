#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policy/system-catalog.v1.json"
SCHEMA = ROOT / "catalog/system-catalog.schema.v1.json"
EXAMPLE = ROOT / "catalog/system-catalog.example.v1.json"
NODES = ROOT / "registry/ecosystem/nodes.json"
EDGES = ROOT / "registry/ecosystem/edges.json"
AUTHORITY = ROOT / "registry/ecosystem/authority-matrix.v1.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def _normalized_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _walk_keys(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            result.append(str(key))
            result.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            result.extend(_walk_keys(item))
    return result


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _validate_example(policy: dict[str, Any], example: dict[str, Any]) -> int:
    if example.get("schemaVersion") != 1:
        raise ValueError("example schemaVersion must be 1")
    if example.get("kind") != "heimgewebe_system_catalog":
        raise ValueError("example kind mismatch")
    if example.get("exampleOnly") is not True:
        raise ValueError("example must remain explicitly non-canonical")

    required = policy.get("targetFormat", {}).get("requiredSystemFields")
    if not isinstance(required, list) or not required:
        raise ValueError("policy targetFormat.requiredSystemFields missing")

    prohibited = {
        _normalized_key(item)
        for item in policy.get("prohibitedOperationalFields", [])
        if isinstance(item, str)
    }
    present = {_normalized_key(item) for item in _walk_keys(example)}
    leaked = sorted(prohibited & present)
    if leaked:
        raise ValueError(f"example contains prohibited operational fields: {', '.join(leaked)}")

    systems = example.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError("example systems must be a non-empty array")
    ids: list[str] = []
    for index, system in enumerate(systems):
        if not isinstance(system, dict):
            raise ValueError(f"example systems[{index}] must be an object")
        missing = [field for field in required if field not in system]
        if missing:
            raise ValueError(f"example systems[{index}] misses: {', '.join(missing)}")
        system_id = _require_nonempty_string(system.get("id"), f"systems[{index}].id")
        _require_nonempty_string(system.get("name"), f"systems[{index}].name")
        _require_nonempty_string(system.get("type"), f"systems[{index}].type")
        _require_nonempty_string(system.get("purpose"), f"systems[{index}].purpose")
        if not isinstance(system.get("notResponsibleFor"), list):
            raise ValueError(f"systems[{index}].notResponsibleFor must be an array")
        if not isinstance(system.get("truthOwnership"), list):
            raise ValueError(f"systems[{index}].truthOwnership must be an array")
        entrypoints = system.get("entrypoints")
        if not isinstance(entrypoints, dict) or not entrypoints:
            raise ValueError(f"systems[{index}].entrypoints must be a non-empty object")
        ids.append(system_id)
    if len(ids) != len(set(ids)):
        raise ValueError("example system ids must be unique")

    known = set(ids)
    relations = example.get("relations")
    if not isinstance(relations, list):
        raise ValueError("example relations must be an array")
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            raise ValueError(f"relations[{index}] must be an object")
        source = relation.get("from")
        target = relation.get("to")
        if source not in known or target not in known:
            raise ValueError(f"relations[{index}] references an unknown system")
        _require_nonempty_string(relation.get("type"), f"relations[{index}].type")
        _require_nonempty_string(relation.get("meaning"), f"relations[{index}].meaning")

    truth_owners = example.get("truthOwners")
    if not isinstance(truth_owners, list) or not truth_owners:
        raise ValueError("example truthOwners must be a non-empty array")
    domains: list[str] = []
    for index, item in enumerate(truth_owners):
        if not isinstance(item, dict):
            raise ValueError(f"truthOwners[{index}] must be an object")
        domain = _require_nonempty_string(item.get("domain"), f"truthOwners[{index}].domain")
        owner = item.get("owner")
        if owner not in known:
            raise ValueError(f"truthOwners[{index}] references an unknown owner")
        domains.append(domain)
    if len(domains) != len(set(domains)):
        raise ValueError("example truth-owner domains must be unique")
    return len(systems)


def validate() -> dict[str, Any]:
    policy = _load(POLICY)
    _load(SCHEMA)
    example = _load(EXAMPLE)
    nodes_doc = _load(NODES)
    edges_doc = _load(EDGES)
    authority = _load(AUTHORITY)

    if policy.get("kind") != "heimgewebe_system_catalog_policy":
        raise ValueError("system catalog policy kind mismatch")
    if policy.get("role") != "app-independent system catalog":
        raise ValueError("system catalog role mismatch")
    app = policy.get("externalCabinetApp")
    if not isinstance(app, dict):
        raise ValueError("externalCabinetApp policy missing")
    if app.get("required") is not False or app.get("canonical") is not False:
        raise ValueError("external Cabinet app must be optional and non-canonical")
    if app.get("runtimeAuthoritative") is not False:
        raise ValueError("external Cabinet runtime must not be authoritative")
    if app.get("shutdownAuthorized") is not False:
        raise ValueError("catalog-core slice must not authorize shutdown")

    expected_inputs = policy.get("currentCanonicalInputs")
    if not isinstance(expected_inputs, list) or not expected_inputs:
        raise ValueError("currentCanonicalInputs missing")
    for relative in expected_inputs:
        if not isinstance(relative, str) or not (ROOT / relative).is_file():
            raise ValueError(f"canonical input missing: {relative}")
    projection = policy.get("canonicalReadableProjection")
    if not isinstance(projection, str) or not (ROOT / projection).is_file():
        raise ValueError("canonical readable projection missing")

    nodes = nodes_doc.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("registry nodes missing")
    node_ids = [item.get("id") for item in nodes if isinstance(item, dict)]
    if len(node_ids) != len(nodes) or any(not isinstance(item, str) or not item for item in node_ids):
        raise ValueError("every registry node needs a non-empty id")
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("registry node ids must be unique")

    edge_types = set(edges_doc.get("edge_types", []))
    edges = edges_doc.get("edges")
    if not isinstance(edges, list):
        raise ValueError("registry edges missing")
    known_nodes = set(node_ids)
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError(f"edge {index} must be an object")
        if edge.get("from") not in known_nodes or edge.get("to") not in known_nodes:
            raise ValueError(f"edge {index} references an unknown node")
        if edge.get("type") not in edge_types:
            raise ValueError(f"edge {index} uses an unknown type")

    authorities = authority.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        raise ValueError("authority matrix missing")
    domains = [item.get("domain") for item in authorities if isinstance(item, dict)]
    if len(domains) != len(authorities) or len(domains) != len(set(domains)):
        raise ValueError("authority domains must be complete and unique")
    if any(not item.get("owner") for item in authorities):
        raise ValueError("every authority domain needs one owner")

    example_count = _validate_example(policy, example)
    debt = policy.get("legacyMigrationDebt")
    if not isinstance(debt, list) or not debt:
        raise ValueError("legacy migration debt must remain explicit during T011")

    return {
        "status": "valid",
        "registrySystems": len(nodes),
        "registryRelations": len(edges),
        "authorityDomains": len(authorities),
        "exampleSystems": example_count,
        "legacyDebtItems": len(debt),
        "externalAppRequired": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
