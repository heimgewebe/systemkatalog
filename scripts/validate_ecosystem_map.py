#!/usr/bin/env python3
"""Validate the Cabinet ecosystem map v0 registry.

The validator is intentionally small and stdlib-only. It checks structural
consistency, not semantic truth. GitHub, CI, runtime and human decisions remain
primary truth sources for their own domains.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "ecosystem"
NODES_PATH = REGISTRY / "nodes.json"
EDGES_PATH = REGISTRY / "edges.json"
CLAIMS_PATH = REGISTRY / "claims.jsonl"
BUREAU_BRIDGE_PATH = REGISTRY / "bureau-bridge.json"

CLAIM_STATUSES = {
    "observed",
    "plausible",
    "evidenced",
    "validated",
    "canonical",
    "approved",
    "stale",
    "contradicted",
    "refuted",
    "draft_decision",
}

BRIDGE_DIRECTION = "cabinet_to_bureau_read_only_candidate_signal"
BRIDGE_ADMISSIBLE_STATUSES = {
    "evidenced",
    "approved",
    "draft_decision_with_explicit_human_release",
}
BRIDGE_REQUIRED_FIELDS = {
    "id",
    "status",
    "evidence",
    "expires_at_or_refresh_hint",
    "next_action",
    "responsible_organ",
}
BRIDGE_BLOCKED_STATUSES = {
    "plausible",
    "speculative",
    "expired",
    "contradicted",
    "unverified",
}
BRIDGE_REQUIRED_PROHIBITIONS = {
    "automatic_bureau_task_creation",
    "automatic_grabowski_delegation",
    "merge_or_push_action",
    "runtime_mutation",
    "cleanup_action",
    "authority_inference_from_map",
}
BRIDGE_REQUIRED_NEGATIVES = {
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "bureau_import_implemented",
    "autonomous_dispatch",
}
BRIDGE_REQUIRED_ORGAN_ROLES = {
    "cabinet",
    "bureau",
    "grabowski_operator",
    "repobrief",
    "steuerboard",
    "chronik",
    "github_ci",
    "schauwerk",
    "external_agents",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path.relative_to(ROOT)}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"missing file: {path.relative_to(ROOT)}") from None
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path.relative_to(ROOT)}:{line_no}: {exc}") from None
        if not isinstance(item, dict):
            raise ValueError(f"claim line {line_no} must be an object")
        rows.append(item)
    return rows


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def require_string_set(value: Any, label: str) -> set[str]:
    items = require_list(value, label)
    result: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, str) or not item:
            raise ValueError(f"{label} item {index} must be a non-empty string")
        result.add(item)
    if len(result) != len(items):
        raise ValueError(f"{label} must not contain duplicates")
    return result


def require_existing_repo_path(raw_path: str, label: str) -> None:
    candidate = (ROOT / raw_path).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        raise ValueError(f"{label} escapes repository root: {raw_path}") from None
    if not candidate.exists():
        raise ValueError(f"{label} references missing path: {raw_path}")


def validate_nodes(nodes_doc: dict[str, Any]) -> set[str]:
    nodes = require_list(nodes_doc.get("nodes"), "nodes")
    seen: set[str] = set()
    for index, node in enumerate(nodes, start=1):
        node_obj = require_object(node, f"node {index}")
        node_id = node_obj.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(f"node {index} id must be a non-empty string")
        if node_id in seen:
            raise ValueError(f"duplicate node id: {node_id}")
        seen.add(node_id)
        for key in ("kind", "label", "role", "status"):
            if not isinstance(node_obj.get(key), str) or not node_obj[key]:
                raise ValueError(f"node {node_id} missing string field: {key}")
    return seen


def validate_edges(edges_doc: dict[str, Any], node_ids: set[str]) -> None:
    edge_types = set(require_list(edges_doc.get("edge_types"), "edge_types"))
    if not edge_types:
        raise ValueError("edge_types must not be empty")
    edges = require_list(edges_doc.get("edges"), "edges")
    for index, edge in enumerate(edges, start=1):
        edge_obj = require_object(edge, f"edge {index}")
        source = edge_obj.get("from")
        target = edge_obj.get("to")
        edge_type = edge_obj.get("type")
        if source not in node_ids:
            raise ValueError(f"edge {index} references unknown from node: {source}")
        if target not in node_ids:
            raise ValueError(f"edge {index} references unknown to node: {target}")
        if edge_type not in edge_types:
            raise ValueError(f"edge {index} uses undeclared type: {edge_type}")
        if not isinstance(edge_obj.get("status"), str) or not edge_obj["status"]:
            raise ValueError(f"edge {index} missing status")


def validate_claims(claims: list[dict[str, Any]], node_ids: set[str]) -> None:
    seen: set[str] = set()
    for index, claim in enumerate(claims, start=1):
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError(f"claim {index} id must be a non-empty string")
        if claim_id in seen:
            raise ValueError(f"duplicate claim id: {claim_id}")
        seen.add(claim_id)
        subject = claim.get("subject")
        if subject not in node_ids:
            raise ValueError(f"claim {claim_id} references unknown subject: {subject}")
        status = claim.get("status")
        if status not in CLAIM_STATUSES:
            raise ValueError(f"claim {claim_id} has invalid status: {status}")
        confidence = claim.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise ValueError(f"claim {claim_id} confidence must be numeric")
        if not 0 <= float(confidence) <= 1:
            raise ValueError(f"claim {claim_id} confidence must be between 0 and 1")
        if not isinstance(claim.get("expires_at"), str) or not claim["expires_at"]:
            raise ValueError(f"claim {claim_id} missing expires_at")
        if not isinstance(claim.get("evidence"), list):
            raise ValueError(f"claim {claim_id} evidence must be a list")


def validate_bridge_policy(bridge_doc: dict[str, Any], node_ids: set[str]) -> None:
    if bridge_doc.get("schema_version") != 1:
        raise ValueError("bureau bridge schema_version must be 1")
    if bridge_doc.get("direction") != BRIDGE_DIRECTION:
        raise ValueError("bureau bridge direction is invalid")
    if bridge_doc.get("source_owner") not in node_ids:
        raise ValueError("bureau bridge source_owner must reference an ecosystem node")
    if bridge_doc.get("target_consumer") not in node_ids:
        raise ValueError("bureau bridge target_consumer must reference an ecosystem node")

    canonical_doc = require_string(bridge_doc.get("canonical_doc"), "bureau bridge canonical_doc")
    require_existing_repo_path(canonical_doc, "bureau bridge canonical_doc")
    for allowed_source in require_string_set(bridge_doc.get("allowed_sources"), "bureau bridge allowed_sources"):
        require_existing_repo_path(allowed_source, "bureau bridge allowed_sources")

    admissible_statuses = require_string_set(
        bridge_doc.get("admissible_candidate_statuses"),
        "bureau bridge admissible_candidate_statuses",
    )
    missing_admissible = BRIDGE_ADMISSIBLE_STATUSES - admissible_statuses
    if missing_admissible:
        raise ValueError("bureau bridge missing admissible statuses: " + ", ".join(sorted(missing_admissible)))
    if admissible_statuses & BRIDGE_BLOCKED_STATUSES:
        raise ValueError("bureau bridge admits blocked statuses")

    candidate_fields = require_string_set(
        bridge_doc.get("required_candidate_fields"),
        "bureau bridge required_candidate_fields",
    )
    missing_fields = BRIDGE_REQUIRED_FIELDS - candidate_fields
    if missing_fields:
        raise ValueError("bureau bridge missing candidate fields: " + ", ".join(sorted(missing_fields)))

    blocked_statuses = require_string_set(bridge_doc.get("blocked_statuses"), "bureau bridge blocked_statuses")
    missing_blocked = BRIDGE_BLOCKED_STATUSES - blocked_statuses
    if missing_blocked:
        raise ValueError("bureau bridge missing blocked statuses: " + ", ".join(sorted(missing_blocked)))

    prohibited_effects = require_string_set(bridge_doc.get("prohibited_effects"), "bureau bridge prohibited_effects")
    missing_prohibitions = BRIDGE_REQUIRED_PROHIBITIONS - prohibited_effects
    if missing_prohibitions:
        raise ValueError("bureau bridge missing prohibitions: " + ", ".join(sorted(missing_prohibitions)))

    organ_roles = require_object(bridge_doc.get("organ_roles"), "bureau bridge organ_roles")
    missing_roles = BRIDGE_REQUIRED_ORGAN_ROLES - set(organ_roles)
    if missing_roles:
        raise ValueError("bureau bridge missing organ roles: " + ", ".join(sorted(missing_roles)))
    for role, description in organ_roles.items():
        require_string(role, "bureau bridge organ role key")
        require_string(description, f"bureau bridge organ role {role}")

    negatives = require_string_set(bridge_doc.get("does_not_establish"), "bureau bridge does_not_establish")
    missing_negatives = BRIDGE_REQUIRED_NEGATIVES - negatives
    if missing_negatives:
        raise ValueError("bureau bridge missing negative semantics: " + ", ".join(sorted(missing_negatives)))


def main() -> int:
    errors: list[str] = []
    try:
        nodes_doc = require_object(load_json(NODES_PATH), "nodes document")
        edges_doc = require_object(load_json(EDGES_PATH), "edges document")
        claims = load_jsonl(CLAIMS_PATH)
        bridge_doc = require_object(load_json(BUREAU_BRIDGE_PATH), "bureau bridge document")
        node_ids = validate_nodes(nodes_doc)
        validate_edges(edges_doc, node_ids)
        validate_claims(claims, node_ids)
        validate_bridge_policy(bridge_doc, node_ids)
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: ecosystem map registry and bureau bridge are structurally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
