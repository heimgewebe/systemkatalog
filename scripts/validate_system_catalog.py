#!/usr/bin/env python3
"""Validate the active, app-independent Systemkatalog bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from system_catalog_fleet import COVERAGE_REL, validate_coverage

ROOT = Path(__file__).resolve().parents[1]
POLICY_REL = Path("policy/system-catalog.v1.json")
SCHEMA_REL = Path("catalog/system-catalog.schema.v1.json")
EXAMPLE_REL = Path("catalog/system-catalog.example.v1.json")
NODES_REL = Path("registry/ecosystem/nodes.json")
EDGES_REL = Path("registry/ecosystem/edges.json")
CLAIMS_REL = Path("registry/ecosystem/claims.jsonl")
AUTHORITY_REL = Path("registry/ecosystem/authority-matrix.v1.json")
VIEW_REL = Path("policy/ecosystem-map-view.v1.json")
FLEET_REL = COVERAGE_REL
ARCHIVE_REL = Path("docs/archive/cabinet-era")

NODE_FIELDS = {"id", "kind", "label", "purpose"}
EDGE_FIELDS = {"from", "to", "type", "stability", "meaning"}
CLAIM_FIELDS = {"id", "subject", "predicate", "object", "evidence", "does_not_establish"}
ALLOWED_NODE_KINDS = {"human", "repository", "concept", "artifact", "service"}
LEGACY_ROOTS = {
    "bestand", "pruefung", "steuerung", "vorzimmer", "heimgewebe",
    "weltgewebe", "werkstatt", "labor", "betrieb",
}
LEGACY_ACTIVE_MARKERS = {".cabinet", ".home", ".agents", ".jobs", "Cabinet-Modell.md"}
CANON_SCAN_EXCLUDED_PARTS = {".git", "node_modules", "__pycache__"}
CANON_KIND_PATHS = {
    "system_catalog_policy": POLICY_REL,
    "system_catalog_authority_matrix": AUTHORITY_REL,
    "system_catalog_inventory": NODES_REL,
    "system_catalog_relations": EDGES_REL,
    "system_catalog_fleet_coverage": FLEET_REL,
    "system_catalog": EXAMPLE_REL,
}
LEGACY_CATALOG_KINDS = {
    "heimgewebe_system_catalog_policy",
    "heimgewebe_system_catalog_authority_matrix",
    "heimgewebe_system_inventory",
    "heimgewebe_system_relations",
    "heimgewebe_system_catalog",
}


def _path(root: Path, relative: Path | str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes catalog root: {relative}") from exc
    return candidate


def _load(root: Path, relative: Path | str) -> dict[str, Any]:
    path = _path(root, relative)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: root must be an object")
    return value


class RegistryValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RegistryData:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


def validate_node(raw_node: Any, index: int) -> dict[str, Any]:
    label = f"node {index}"
    if not isinstance(raw_node, dict) or set(raw_node) != NODE_FIELDS:
        raise RegistryValidationError(f"{label} fields mismatch")
    for field in NODE_FIELDS:
        _require_string(raw_node.get(field), f"{label}.{field}")
    if raw_node["kind"] not in ALLOWED_NODE_KINDS:
        raise RegistryValidationError(f"{label} uses non-catalog kind: {raw_node['kind']}")
    if raw_node["id"].startswith(("runtime:", "agent:")):
        raise RegistryValidationError("runtime and agent identities are not catalog systems")
    return raw_node


def validate_edge(raw_edge: Any, index: int) -> dict[str, Any]:
    label = f"edge {index}"
    if not isinstance(raw_edge, dict) or set(raw_edge) != EDGE_FIELDS:
        raise RegistryValidationError(f"{label} fields mismatch")
    for field in EDGE_FIELDS:
        _require_string(raw_edge.get(field), f"{label}.{field}")
    return raw_edge


def load_registry(root: Path) -> RegistryData:
    nodes_doc = _load(root, NODES_REL)
    edges_doc = _load(root, EDGES_REL)
    raw_nodes, raw_edges = nodes_doc.get("nodes"), edges_doc.get("edges")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise RegistryValidationError("registry nodes missing")
    if not isinstance(raw_edges, list):
        raise RegistryValidationError("registry edges missing")
    nodes = [validate_node(item, index) for index, item in enumerate(raw_nodes, 1)]
    node_ids = [item["id"] for item in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise RegistryValidationError("registry node identities are duplicated")
    known = set(node_ids)
    edges = [validate_edge(item, index) for index, item in enumerate(raw_edges, 1)]
    seen: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges, 1):
        if edge["from"] not in known:
            raise RegistryValidationError(f"edge {index} references unknown from node: {edge['from']}")
        if edge["to"] not in known:
            raise RegistryValidationError(f"edge {index} references unknown to node: {edge['to']}")
        key = (edge["from"], edge["to"], edge["type"])
        if key in seen:
            raise RegistryValidationError(f"duplicate edge: {key}")
        seen.add(key)
    return RegistryData(nodes=nodes, edges=edges)


def _load_jsonl(root: Path, relative: Path | str) -> list[dict[str, Any]]:
    path = _path(root, relative)
    result: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{relative}:{line_no}: entry must be an object")
        result.append(value)
    return result


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_string_array(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label} must be a {'possibly empty ' if allow_empty else 'non-empty '}string array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates")
    return value


def _normalized_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _validate_no_operational_fields(policy: dict[str, Any], label: str, value: Any) -> None:
    prohibited = {_normalized_key(item) for item in policy.get("prohibitedOperationalFields", [])}
    if not prohibited:
        raise ValueError("policy prohibitedOperationalFields missing")
    leaked = sorted(prohibited & {_normalized_key(key) for key in _walk_keys(value)})
    if leaked:
        raise ValueError(f"{label} contains prohibited operational fields: {', '.join(leaked)}")


def _validate_active_layout(root: Path) -> None:
    present_rooms = sorted(name for name in LEGACY_ROOTS if (root / name).exists())
    if present_rooms:
        raise ValueError(f"legacy room roots remain active: {', '.join(present_rooms)}")
    present_markers = sorted(name for name in LEGACY_ACTIVE_MARKERS if (root / name).exists())
    if present_markers:
        raise ValueError(f"legacy Cabinet markers remain active: {', '.join(present_markers)}")
    archive = root / ARCHIVE_REL
    if not archive.is_dir() or not (archive / "README.md").is_file():
        raise ValueError("historical Cabinet archive boundary missing")


def _is_canon_scan_excluded(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if relative == ARCHIVE_REL or ARCHIVE_REL in relative.parents:
        return True
    return any(part in CANON_SCAN_EXCLUDED_PARTS for part in relative.parts)


def _validate_unique_canons(root: Path) -> None:
    found: dict[str, list[Path]] = {kind: [] for kind in CANON_KIND_PATHS}
    manual_authority_files: list[Path] = []
    legacy_kind_files: list[Path] = []

    for path in root.rglob("*.json"):
        if _is_canon_scan_excluded(root, path):
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        kind = value.get("kind")
        relative = path.relative_to(root)
        if kind in found:
            found[str(kind)].append(relative)
        if kind in LEGACY_CATALOG_KINDS:
            legacy_kind_files.append(relative)
        if "authorities" in value and kind != "system_catalog_authority_matrix":
            manual_authority_files.append(relative)

    for kind, expected_path in CANON_KIND_PATHS.items():
        actual = sorted(found[kind])
        if actual != [expected_path]:
            rendered = ", ".join(str(item) for item in actual) or "none"
            raise ValueError(
                f"exactly one active {kind} is required at {expected_path}; found: {rendered}"
            )
    if manual_authority_files:
        rendered = ", ".join(str(item) for item in sorted(manual_authority_files))
        raise ValueError(f"manual authority assignments outside the matrix are forbidden: {rendered}")
    if legacy_kind_files:
        rendered = ", ".join(str(item) for item in sorted(legacy_kind_files))
        raise ValueError(f"legacy catalog kinds remain active outside the archive: {rendered}")


def _validate_example(policy: dict[str, Any], example: dict[str, Any]) -> int:
    if example.get("schemaVersion") != 1 or example.get("kind") != "system_catalog":
        raise ValueError("example contract mismatch")
    if example.get("exampleOnly") is not True:
        raise ValueError("example must be explicitly non-canonical")
    _validate_no_operational_fields(policy, "example", example)
    required = _require_string_array(
        policy.get("targetFormat", {}).get("requiredSystemFields"),
        "targetFormat.requiredSystemFields",
    )
    systems = example.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError("example systems missing")
    ids: list[str] = []
    for index, system in enumerate(systems):
        if not isinstance(system, dict):
            raise ValueError(f"systems[{index}] must be an object")
        missing = [field for field in required if field not in system]
        if missing:
            raise ValueError(f"systems[{index}] misses: {', '.join(missing)}")
        system_id = _require_string(system.get("id"), f"systems[{index}].id")
        for field in ("name", "type", "purpose"):
            _require_string(system.get(field), f"systems[{index}].{field}")
        if not isinstance(system.get("notResponsibleFor"), list):
            raise ValueError(f"systems[{index}].notResponsibleFor must be an array")
        if not isinstance(system.get("truthOwnership"), list):
            raise ValueError(f"systems[{index}].truthOwnership must be an array")
        if not isinstance(system.get("entrypoints"), dict) or not system["entrypoints"]:
            raise ValueError(f"systems[{index}].entrypoints must be non-empty")
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
        if relation.get("from") not in known or relation.get("to") not in known:
            raise ValueError(f"relations[{index}] references unknown system")
        _require_string(relation.get("type"), f"relations[{index}].type")
        _require_string(relation.get("meaning"), f"relations[{index}].meaning")
    truth_owners = example.get("truthOwners")
    if not isinstance(truth_owners, list) or not truth_owners:
        raise ValueError("example truthOwners must be a non-empty array")
    domains: list[str] = []
    for index, item in enumerate(truth_owners):
        if not isinstance(item, dict) or item.get("owner") not in known:
            raise ValueError(f"truthOwners[{index}] invalid")
        domains.append(_require_string(item.get("domain"), f"truthOwners[{index}].domain"))
    if not domains or len(domains) != len(set(domains)):
        raise ValueError("truth-owner domains missing or duplicated")
    return len(systems)


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    _validate_active_layout(root)
    _validate_unique_canons(root)
    policy = _load(root, POLICY_REL)
    _load(root, SCHEMA_REL)
    example = _load(root, EXAMPLE_REL)
    nodes_doc = _load(root, NODES_REL)
    edges_doc = _load(root, EDGES_REL)
    claims = _load_jsonl(root, CLAIMS_REL)
    authority = _load(root, AUTHORITY_REL)
    view = _load(root, VIEW_REL)
    fleet_coverage = _load(root, FLEET_REL)

    if policy.get("kind") != "system_catalog_policy":
        raise ValueError("system catalog policy kind mismatch")
    if policy.get("contractState") != "active" or policy.get("role") != "app-independent system catalog":
        raise ValueError("system catalog policy role/state mismatch")
    if policy.get("repository") != "heimgewebe/systemkatalog":
        raise ValueError("repository identity mismatch")
    catalog_inputs = [str(NODES_REL), str(EDGES_REL), str(CLAIMS_REL), str(AUTHORITY_REL)]
    expected_inputs = [*catalog_inputs, str(FLEET_REL)]
    if policy.get("canonicalInputs") != expected_inputs:
        raise ValueError("canonicalInputs mismatch")
    if policy.get("canonicalAuthorityMatrix") != str(AUTHORITY_REL):
        raise ValueError("canonical authority matrix mismatch")
    if policy.get("canonicalGeneratedMap") != "rendered/ecosystem-registry-map.mmd":
        raise ValueError("generated map binding mismatch")
    if policy.get("canonicalProjectionPolicy") != str(VIEW_REL):
        raise ValueError("projection policy binding mismatch")
    archive = policy.get("archiveBoundary")
    if not isinstance(archive, dict) or archive != {
        "path": str(ARCHIVE_REL),
        "role": "historical_noncanonical_material",
        "activeInput": False,
        "maintained": False,
    }:
        raise ValueError("archive boundary mismatch")
    if "runtimeProjection" in policy:
        raise ValueError("runtimeProjection must remain absent from the static catalog policy")
    if set(policy.get("publicProjection", {}).get("excludedKinds", [])) != {"runtime", "agent"}:
        raise ValueError("public projection exclusions mismatch")
    for relative in policy.get("maintainedCatalogSurfaces", []):
        if not isinstance(relative, str) or not _path(root, relative).is_file():
            raise ValueError(f"maintained surface missing: {relative}")

    canonical_values = {
        str(POLICY_REL): policy,
        str(NODES_REL): nodes_doc,
        str(EDGES_REL): edges_doc,
        str(CLAIMS_REL): claims,
        str(AUTHORITY_REL): authority,
        str(VIEW_REL): view,
        str(FLEET_REL): fleet_coverage,
    }
    for label, value in canonical_values.items():
        _validate_no_operational_fields(policy, label, value)

    if nodes_doc.get("kind") != "system_catalog_inventory" or nodes_doc.get("owner") != "repo:systemkatalog":
        raise ValueError("system inventory contract mismatch")
    if nodes_doc.get("catalogRole") != "canonical_system_inventory":
        raise ValueError("system inventory role mismatch")
    registry = load_registry(root)
    nodes = registry.nodes
    node_ids = [node["id"] for node in nodes]
    if "repo:systemkatalog" not in node_ids:
        raise ValueError("registry node identity mismatch")
    known_nodes = set(node_ids)

    if edges_doc.get("kind") != "system_catalog_relations" or edges_doc.get("catalogRole") != "canonical_stable_relations":
        raise ValueError("relation inventory contract mismatch")
    relation_types = set(_require_string_array(edges_doc.get("relationTypes"), "relationTypes"))
    stability_classes = set(_require_string_array(edges_doc.get("stabilityClasses"), "stabilityClasses"))
    if stability_classes != set(policy.get("stableRelationClasses", [])):
        raise ValueError("stability classes differ")
    edges = registry.edges
    for index, edge in enumerate(edges):
        if edge["type"] not in relation_types:
            raise ValueError(f"edge {index} relation type mismatch")
        if edge["stability"] not in stability_classes:
            raise ValueError(f"edge {index} stability mismatch")

    repository_node_ids = {node["id"] for node in nodes if node["kind"] == "repository"}
    fleet_coverage = validate_coverage(root, repository_node_ids)

    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        if set(claim) != CLAIM_FIELDS:
            raise ValueError(f"claim {index} fields mismatch")
        claim_id = _require_string(claim.get("id"), f"claim {index}.id")
        if not claim_id.startswith("systemkatalog:") or claim_id in claim_ids:
            raise ValueError(f"claim id invalid or duplicated: {claim_id}")
        claim_ids.add(claim_id)
        if claim.get("subject") not in known_nodes:
            raise ValueError(f"claim {claim_id} references unknown subject")
        _require_string(claim.get("predicate"), f"claim {claim_id}.predicate")
        _require_string(claim.get("object"), f"claim {claim_id}.object")
        for evidence in _require_string_array(claim.get("evidence"), f"claim {claim_id}.evidence"):
            if not _path(root, evidence).is_file():
                raise ValueError(f"claim {claim_id} evidence missing: {evidence}")
        _require_string_array(claim.get("does_not_establish"), f"claim {claim_id}.does_not_establish")

    if authority.get("kind") != "system_catalog_authority_matrix":
        raise ValueError("authority matrix kind mismatch")
    if authority.get("canonicalMap") != policy["canonicalGeneratedMap"]:
        raise ValueError("authority canonical map mismatch")
    if authority.get("registryInputs") != [str(NODES_REL), str(EDGES_REL), str(CLAIMS_REL)]:
        raise ValueError("authority registry inputs mismatch")
    if authority.get("specializedViews") != []:
        raise ValueError("manual specialized map views are retired")
    authorities = authority.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        raise ValueError("authority assignments missing")
    domains: list[str] = []
    for index, item in enumerate(authorities):
        if not isinstance(item, dict) or set(item) != {"domain", "owner", "projections"}:
            raise ValueError(f"authority {index} fields mismatch")
        domains.append(_require_string(item.get("domain"), f"authority {index}.domain"))
        _require_string(item.get("owner"), f"authority {index}.owner")
        _require_string_array(item.get("projections"), f"authority {index}.projections", allow_empty=True)
    if len(domains) != len(set(domains)):
        raise ValueError("authority domains duplicated")
    authority_by_domain = {item["domain"]: item for item in authorities}
    if authority_by_domain.get("fleet_membership", {}).get("owner") != "metarepo":
        raise ValueError("Fleet membership authority must remain Metarepo")
    if authority_by_domain.get("agent_routing", {}).get("owner") != "grabowski":
        raise ValueError("agent routing authority must remain Grabowski")

    if view.get("kind") != "system_catalog_map_projection_policy" or view.get("authoritative") is not False:
        raise ValueError("map projection policy mismatch")
    if view.get("source") != "registry/ecosystem/nodes.json + registry/ecosystem/edges.json":
        raise ValueError("map projection source mismatch")
    if view.get("visualAnchorNodeIds") != ["repo:systemkatalog", "artifact:ecosystem-map"]:
        raise ValueError("map anchor identity mismatch")

    example_count = _validate_example(policy, example)
    return {
        "status": "valid",
        "registrySystems": len(nodes),
        "registryRelations": len(edges),
        "stableClaims": len(claims),
        "authorityDomains": len(authorities),
        "exampleSystems": example_count,
        "catalogRepositories": len(repository_node_ids),
        "fleetRepositories": sum(1 for item in fleet_coverage["repositories"] if item["membership"] in {"fleet", "related"}),
        "fleetExclusions": len(fleet_coverage["sourceExclusions"]),
        "activeLegacyRooms": 0,
        "archive": str(ARCHIVE_REL),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
