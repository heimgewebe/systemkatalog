#!/usr/bin/env python3
"""Validate the app-independent Cabinet system catalog.

The validator checks the maintained catalog bundle only. Historical Cabinet
surfaces may remain readable, but they cannot become a competing canon or leak
operational state into the maintained catalog.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
POLICY_REL = Path("policy/system-catalog.v1.json")
SCHEMA_REL = Path("catalog/system-catalog.schema.v1.json")
EXAMPLE_REL = Path("catalog/system-catalog.example.v1.json")
NODES_REL = Path("registry/ecosystem/nodes.json")
EDGES_REL = Path("registry/ecosystem/edges.json")
CLAIMS_REL = Path("registry/ecosystem/claims.jsonl")
AUTHORITY_REL = Path("registry/ecosystem/authority-matrix.v1.json")
VIEW_REL = Path("policy/ecosystem-map-view.v1.json")

POLICY = ROOT / POLICY_REL
SCHEMA = ROOT / SCHEMA_REL
EXAMPLE = ROOT / EXAMPLE_REL
NODES = ROOT / NODES_REL
EDGES = ROOT / EDGES_REL
CLAIMS = ROOT / CLAIMS_REL
AUTHORITY = ROOT / AUTHORITY_REL
VIEW = ROOT / VIEW_REL

NODE_FIELDS = {"id", "kind", "label", "purpose"}
EDGE_FIELDS = {"from", "to", "type", "stability", "meaning"}
CLAIM_FIELDS = {"id", "subject", "predicate", "object", "evidence", "does_not_establish"}
ALLOWED_NODE_KINDS = {"human", "repository", "concept", "artifact", "service"}
CANON_SCAN_EXCLUDED_PARTS = {
    ".git",
    ".agents",
    "external",
    "node_modules",
    "rendered",
    "pruefung",
}
CANON_SCAN_EXCLUDED_PREFIXES = (
    Path("docs/archive"),
)


def _path(root: Path, relative: Path | str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes catalog root: {relative}") from exc
    return candidate


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def _load_rel(root: Path, relative: Path | str) -> dict[str, Any]:
    return _load(_path(root, relative))


def _load_jsonl(root: Path, relative: Path | str) -> list[dict[str, Any]]:
    path = _path(root, relative)
    result: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{relative}:{line_no}: claim must be an object")
        result.append(value)
    return result


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


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_string_array(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty string array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates")
    return value


def _validate_no_operational_fields(policy: dict[str, Any], label: str, value: Any) -> None:
    prohibited = {
        _normalized_key(item)
        for item in policy.get("prohibitedOperationalFields", [])
        if isinstance(item, str)
    }
    if not prohibited:
        raise ValueError("policy prohibitedOperationalFields missing")
    present = {_normalized_key(item) for item in _walk_keys(value)}
    leaked = sorted(prohibited & present)
    if leaked:
        raise ValueError(f"{label} contains prohibited operational fields: {', '.join(leaked)}")


def _validate_example(policy: dict[str, Any], example: dict[str, Any]) -> int:
    if example.get("schemaVersion") != 1:
        raise ValueError("example schemaVersion must be 1")
    if example.get("kind") != "heimgewebe_system_catalog":
        raise ValueError("example kind mismatch")
    if example.get("exampleOnly") is not True:
        raise ValueError("example must remain explicitly non-canonical")
    _validate_no_operational_fields(policy, "example", example)

    required = policy.get("targetFormat", {}).get("requiredSystemFields")
    if not isinstance(required, list) or not required:
        raise ValueError("policy targetFormat.requiredSystemFields missing")
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
        for field in ("name", "type", "purpose"):
            _require_nonempty_string(system.get(field), f"systems[{index}].{field}")
        for field in ("notResponsibleFor", "truthOwnership"):
            if not isinstance(system.get(field), list):
                raise ValueError(f"systems[{index}].{field} must be an array")
        if not isinstance(system.get("entrypoints"), dict) or not system["entrypoints"]:
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
        if relation.get("from") not in known or relation.get("to") not in known:
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
        if item.get("owner") not in known:
            raise ValueError(f"truthOwners[{index}] references an unknown owner")
        domains.append(domain)
    if len(domains) != len(set(domains)):
        raise ValueError("example truth-owner domains must be unique")
    return len(systems)


def _is_canon_scan_excluded(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in CANON_SCAN_EXCLUDED_PARTS for part in relative.parts):
        return True
    return any(relative == prefix or prefix in relative.parents for prefix in CANON_SCAN_EXCLUDED_PREFIXES)


def _validate_unique_canons(root: Path) -> None:
    authority_files: list[Path] = []
    policy_files: list[Path] = []
    catalog_docs: list[Path] = []
    manual_authority_files: list[Path] = []
    for path in root.rglob("*.json"):
        if _is_canon_scan_excluded(root, path):
            continue
        try:
            value = _load(path)
        except (ValueError, json.JSONDecodeError, UnicodeError):
            continue
        kind = value.get("kind")
        if kind == "cabinet_ecosystem_authority_matrix":
            authority_files.append(path)
        elif kind == "heimgewebe_system_catalog_policy":
            policy_files.append(path)
        elif kind == "heimgewebe_system_catalog":
            catalog_docs.append(path)
        if "authorities" in value and kind != "cabinet_ecosystem_authority_matrix":
            manual_authority_files.append(path)
    authority_files.sort()
    policy_files.sort()
    catalog_docs.sort()
    manual_authority_files.sort()
    if authority_files != [_path(root, AUTHORITY_REL)]:
        raise ValueError("exactly one maintained authority matrix is required")
    if policy_files != [_path(root, POLICY_REL)]:
        raise ValueError("exactly one maintained system catalog policy is required")
    expected_example = _path(root, EXAMPLE_REL)
    if catalog_docs != [expected_example]:
        raise ValueError("stored catalog documents must be limited to the explicit non-canonical example")
    if manual_authority_files:
        rendered = ", ".join(str(path.relative_to(root)) for path in manual_authority_files)
        raise ValueError(f"manual authority assignments outside the matrix are forbidden: {rendered}")


def _validate_legacy_automation(root: Path, policy: dict[str, Any]) -> None:
    automation = policy.get("legacyAutomationPolicy")
    if not isinstance(automation, dict):
        raise ValueError("legacyAutomationPolicy missing")
    for field in ("scheduledExecution", "automaticPushOrPullRequestExecution", "automaticDispatch", "automaticMutation"):
        if automation.get(field) is not False:
            raise ValueError(f"legacyAutomationPolicy.{field} must be false")
    workflows = _require_string_array(automation.get("manualCompatibilityWorkflows"), "legacyAutomationPolicy.manualCompatibilityWorkflows")
    for relative in workflows:
        path = _path(root, relative)
        text = path.read_text(encoding="utf-8")
        if "workflow_dispatch:" not in text:
            raise ValueError(f"legacy compatibility workflow is not manually dispatchable: {relative}")
        for forbidden in ("schedule:", "pull_request:", "push:"):
            if forbidden in text:
                raise ValueError(f"legacy compatibility workflow has automatic trigger {forbidden}: {relative}")
    validation_workflow = automation.get("compatibilityValidationWorkflow")
    if not isinstance(validation_workflow, str) or not _path(root, validation_workflow).is_file():
        raise ValueError("legacy compatibility validation workflow missing")
    bridge_adapter = automation.get("bridgeProbeAdapter")
    if not isinstance(bridge_adapter, str) or not _path(root, bridge_adapter).is_file():
        raise ValueError("legacy bridge probe adapter missing")
    if bridge_adapter not in policy.get("legacyCompatibilitySurfaces", []):
        raise ValueError("legacy bridge probe adapter must be a compatibility surface")
    bridge_workflow_name = automation.get("bridgeProbeWorkflow")
    if not isinstance(bridge_workflow_name, str) or not bridge_workflow_name:
        raise ValueError("legacy bridge probe workflow missing")
    bridge_workflow = _path(root, bridge_workflow_name)
    if not bridge_workflow.is_file():
        raise ValueError("legacy bridge probe workflow missing")
    workflow_text = bridge_workflow.read_text(encoding="utf-8")
    required_fragments = (
        f"python3 {bridge_adapter} --output bridge-probe-sandbox",
        "--bridge-policy bridge-probe-sandbox/registry/ecosystem/bureau-bridge.json",
        "set -o pipefail",
    )
    missing = [fragment for fragment in required_fragments if fragment not in workflow_text]
    if missing:
        raise ValueError("legacy bridge probe workflow bypasses the isolated adapter")


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    policy = _load_rel(root, POLICY_REL)
    _load_rel(root, SCHEMA_REL)
    example = _load_rel(root, EXAMPLE_REL)
    nodes_doc = _load_rel(root, NODES_REL)
    edges_doc = _load_rel(root, EDGES_REL)
    claims = _load_jsonl(root, CLAIMS_REL)
    authority = _load_rel(root, AUTHORITY_REL)
    view = _load_rel(root, VIEW_REL)

    if policy.get("kind") != "heimgewebe_system_catalog_policy":
        raise ValueError("system catalog policy kind mismatch")
    if policy.get("contractState") != "active":
        raise ValueError("system catalog policy must be active")
    if policy.get("role") != "app-independent system catalog":
        raise ValueError("system catalog role mismatch")
    app = policy.get("externalCabinetApp")
    if not isinstance(app, dict):
        raise ValueError("externalCabinetApp policy missing")
    if app.get("required") is not False or app.get("canonical") is not False:
        raise ValueError("external Cabinet app must be optional and non-canonical")
    if app.get("runtimeAuthoritative") is not False or app.get("shutdownAuthorized") is not False:
        raise ValueError("external Cabinet runtime must not be authoritative or shutdown-authorized")

    expected_inputs = [str(NODES_REL), str(EDGES_REL), str(CLAIMS_REL), str(AUTHORITY_REL)]
    if policy.get("currentCanonicalInputs") != expected_inputs:
        raise ValueError("currentCanonicalInputs must be the exact maintained catalog inputs")
    if policy.get("canonicalAuthorityMatrix") != str(AUTHORITY_REL):
        raise ValueError("canonicalAuthorityMatrix mismatch")
    if policy.get("canonicalGeneratedMap") != "rendered/ecosystem-registry-map.mmd":
        raise ValueError("canonicalGeneratedMap mismatch")
    if policy.get("canonicalProjectionPolicy") != str(VIEW_REL):
        raise ValueError("canonicalProjectionPolicy mismatch")
    projection = policy.get("publicProjection")
    if not isinstance(projection, dict) or set(projection.get("excludedKinds", [])) != {"runtime", "agent"}:
        raise ValueError("publicProjection must exclude runtime and provider-agent identities")
    for relative in policy.get("maintainedCatalogSurfaces", []):
        if not isinstance(relative, str) or not _path(root, relative).is_file():
            raise ValueError(f"maintained catalog surface missing: {relative}")
    for relative in policy.get("legacyCompatibilitySurfaces", []):
        if not isinstance(relative, str) or not _path(root, relative).is_file():
            raise ValueError(f"legacy compatibility surface missing: {relative}")

    archives = policy.get("legacySourceArchives")
    if not isinstance(archives, list) or not archives:
        raise ValueError("legacySourceArchives missing")
    archive_paths: set[str] = set()
    for index, archive in enumerate(archives):
        if not isinstance(archive, dict) or set(archive) != {"path", "sha256", "sourceRevision"}:
            raise ValueError(f"legacySourceArchives[{index}] fields mismatch")
        relative = _require_nonempty_string(archive.get("path"), f"legacySourceArchives[{index}].path")
        digest = _require_nonempty_string(archive.get("sha256"), f"legacySourceArchives[{index}].sha256")
        _require_nonempty_string(archive.get("sourceRevision"), f"legacySourceArchives[{index}].sourceRevision")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"legacySourceArchives[{index}].sha256 malformed")
        path = _path(root, relative)
        if not path.is_file():
            raise ValueError(f"legacy source archive missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"legacy source archive integrity mismatch: {relative}")
        archive_paths.add(relative)
    if not archive_paths.issubset(set(policy.get("legacyCompatibilitySurfaces", []))):
        raise ValueError("legacy source archives must be registered as compatibility surfaces")

    canonical_values = {
        str(POLICY_REL): policy,
        str(NODES_REL): nodes_doc,
        str(EDGES_REL): edges_doc,
        str(CLAIMS_REL): claims,
        str(AUTHORITY_REL): authority,
        str(VIEW_REL): view,
    }
    for label, value in canonical_values.items():
        _validate_no_operational_fields(policy, label, value)

    if nodes_doc.get("schemaVersion") != 1 or nodes_doc.get("kind") != "heimgewebe_system_inventory":
        raise ValueError("node inventory contract mismatch")
    if nodes_doc.get("catalogRole") != "canonical_system_inventory":
        raise ValueError("node inventory catalog role mismatch")
    nodes = nodes_doc.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("registry nodes missing")
    node_ids: list[str] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict) or set(node) != NODE_FIELDS:
            raise ValueError(f"node {index} fields mismatch")
        node_ids.append(_require_nonempty_string(node.get("id"), f"node {index}.id"))
        kind = _require_nonempty_string(node.get("kind"), f"node {index}.kind")
        if kind not in ALLOWED_NODE_KINDS:
            raise ValueError(f"node {index} uses non-catalog kind: {kind}")
        _require_nonempty_string(node.get("label"), f"node {index}.label")
        _require_nonempty_string(node.get("purpose"), f"node {index}.purpose")
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("registry node ids must be unique")
    known_nodes = set(node_ids)
    if any(node_id.startswith(("runtime:", "agent:")) for node_id in known_nodes):
        raise ValueError("runtime and provider-agent identities must not be catalog nodes")

    if edges_doc.get("schemaVersion") != 1 or edges_doc.get("kind") != "heimgewebe_system_relations":
        raise ValueError("relation inventory contract mismatch")
    relation_types = set(_require_string_array(edges_doc.get("relationTypes"), "relationTypes"))
    stability_classes = set(_require_string_array(edges_doc.get("stabilityClasses"), "stabilityClasses"))
    if stability_classes != set(policy.get("stableRelationClasses", [])):
        raise ValueError("edge and policy stability classes differ")
    edges = edges_doc.get("edges")
    if not isinstance(edges, list):
        raise ValueError("registry edges missing")
    edge_keys: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict) or set(edge) != EDGE_FIELDS:
            raise ValueError(f"edge {index} fields mismatch")
        source = edge.get("from")
        target = edge.get("to")
        if source not in known_nodes or target not in known_nodes:
            raise ValueError(f"edge {index} references an unknown node")
        relation_type = _require_nonempty_string(edge.get("type"), f"edge {index}.type")
        if relation_type not in relation_types:
            raise ValueError(f"edge {index} uses an unknown type")
        if edge.get("stability") not in stability_classes:
            raise ValueError(f"edge {index} uses an unknown stability class")
        _require_nonempty_string(edge.get("meaning"), f"edge {index}.meaning")
        edge_key = (source, target, relation_type)
        if edge_key in edge_keys:
            raise ValueError(f"duplicate edge: {edge_key}")
        edge_keys.add(edge_key)

    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        if set(claim) != CLAIM_FIELDS:
            raise ValueError(f"claim {index} fields mismatch")
        claim_id = _require_nonempty_string(claim.get("id"), f"claim {index}.id")
        if claim_id in claim_ids:
            raise ValueError(f"duplicate claim id: {claim_id}")
        claim_ids.add(claim_id)
        if claim.get("subject") not in known_nodes:
            raise ValueError(f"claim {claim_id} references an unknown subject")
        _require_nonempty_string(claim.get("predicate"), f"claim {claim_id}.predicate")
        _require_nonempty_string(claim.get("object"), f"claim {claim_id}.object")
        for field in ("evidence", "does_not_establish"):
            _require_string_array(claim.get(field), f"claim {claim_id}.{field}")
            if field == "evidence":
                for evidence in claim[field]:
                    if not _path(root, evidence).is_file():
                        raise ValueError(f"claim {claim_id} references missing evidence: {evidence}")

    if authority.get("kind") != "cabinet_ecosystem_authority_matrix":
        raise ValueError("authority matrix kind mismatch")
    if authority.get("canonicalMap") != policy["canonicalGeneratedMap"]:
        raise ValueError("authority matrix canonical map mismatch")
    if authority.get("registryInputs") != [str(NODES_REL), str(EDGES_REL), str(CLAIMS_REL)]:
        raise ValueError("authority matrix registry inputs mismatch")
    specialized = authority.get("specializedViews")
    if not isinstance(specialized, list):
        raise ValueError("specializedViews must be an array")
    for item in specialized:
        if not isinstance(item, dict) or item.get("authoritative") is not False:
            raise ValueError("specialized views must be non-authoritative")
    authorities = authority.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        raise ValueError("authority matrix missing")
    domains: list[str] = []
    for index, item in enumerate(authorities):
        if not isinstance(item, dict):
            raise ValueError(f"authority {index} must be an object")
        domains.append(_require_nonempty_string(item.get("domain"), f"authority {index}.domain"))
        _require_nonempty_string(item.get("owner"), f"authority {index}.owner")
    if len(domains) != len(set(domains)):
        raise ValueError("authority domains must be unique")

    if view.get("kind") != "cabinet_ecosystem_map_projection_policy" or view.get("authoritative") is not False:
        raise ValueError("map projection policy must be explicitly non-authoritative")
    if view.get("source") != "registry/ecosystem/nodes.json + registry/ecosystem/edges.json":
        raise ValueError("map projection source mismatch")

    _validate_unique_canons(root)
    _validate_legacy_automation(root, policy)
    example_count = _validate_example(policy, example)
    migration = policy.get("migrationCompletion")
    if not isinstance(migration, dict) or migration.get("task") != "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T004":
        raise ValueError("T004 migration completion record missing")

    return {
        "status": "valid",
        "registrySystems": len(nodes),
        "registryRelations": len(edges),
        "stableClaims": len(claims),
        "authorityDomains": len(authorities),
        "exampleSystems": example_count,
        "maintainedCatalogSurfaces": len(policy["maintainedCatalogSurfaces"]),
        "legacyCompatibilitySurfaces": len(policy["legacyCompatibilitySurfaces"]),
        "externalAppRequired": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
