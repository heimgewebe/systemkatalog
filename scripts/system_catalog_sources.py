#!/usr/bin/env python3
"""Validate source provenance and freshness contracts for Systemkatalog."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

SOURCE_BINDINGS_REL = Path("registry/ecosystem/source-bindings.v1.json")
FRESHNESS_POLICY_REL = Path("policy/freshness-slo.v1.json")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOCATOR_KINDS = {"file", "json_pointer", "repository_metadata", "private_repository_metadata"}
METHODS = {
    "repository_primary_document",
    "github_repository_metadata",
    "private_repository_metadata_projection",
    "catalog_curator_review",
}


def _load(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: root must be an object")
    return value


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return value


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must stay within its repository")
    return value


def _locator(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    kind = value.get("kind")
    if kind not in LOCATOR_KINDS:
        raise ValueError(f"{label}.kind is invalid")
    digest = value.get("contentSha256")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise ValueError(f"{label}.contentSha256 must be lowercase SHA-256")
    expected = {"kind", "contentSha256"}
    if kind in {"file", "json_pointer"}:
        expected.add("path")
        _safe_relative(value.get("path"), f"{label}.path")
    if kind == "json_pointer":
        expected.add("pointer")
        pointer = value.get("pointer")
        if not isinstance(pointer, str) or not pointer.startswith("/") or "\n" in pointer or "\r" in pointer:
            raise ValueError(f"{label}.pointer must be a JSON pointer")
    if set(value) != expected:
        raise ValueError(f"{label} fields mismatch")
    return value


def _source(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"repository", "commit", "defaultBranch", "locator"}:
        raise ValueError(f"{label} fields mismatch")
    repository = value.get("repository")
    if not isinstance(repository, str) or REPOSITORY.fullmatch(repository) is None:
        raise ValueError(f"{label}.repository must use owner/repository form")
    default_branch = value.get("defaultBranch")
    if not isinstance(default_branch, str) or not default_branch or any(char.isspace() for char in default_branch):
        raise ValueError(f"{label}.defaultBranch must be a non-empty branch name")
    commit = value.get("commit")
    if commit != "redacted" and (not isinstance(commit, str) or SHA40.fullmatch(commit) is None):
        raise ValueError(f"{label}.commit must be a lowercase Git SHA or redacted")
    locator = _locator(value.get("locator"), f"{label}.locator")
    if commit == "redacted" and locator["kind"] != "private_repository_metadata":
        raise ValueError(f"{label}: redacted commit requires private_repository_metadata")
    if commit != "redacted" and locator["kind"] == "private_repository_metadata":
        raise ValueError(f"{label}: private_repository_metadata requires redacted commit")
    return value


def _validate_local_source_bytes(root: Path, source: dict[str, Any], label: str) -> None:
    locator = source["locator"]
    if source["repository"] != "heimgewebe/systemkatalog" or source["commit"] == "redacted":
        return
    if locator["kind"] not in {"file", "json_pointer"}:
        return
    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if inside.returncode != 0:
        return
    result = subprocess.run(
        ["git", "show", f"{source['commit']}:{locator['path']}"],
        cwd=root,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"{label} cannot resolve the bound catalog commit and path")
    digest = hashlib.sha256(result.stdout).hexdigest()
    if digest != locator["contentSha256"]:
        raise ValueError(f"{label} contentSha256 differs from the bound catalog bytes")


def _review_fields(item: dict[str, Any], label: str) -> None:
    _timestamp(item.get("reviewedAt"), f"{label}.reviewedAt")
    if item.get("method") not in METHODS:
        raise ValueError(f"{label}.method is invalid")
    uncertainty = item.get("uncertainty")
    if isinstance(uncertainty, bool) or not isinstance(uncertainty, (int, float)) or not 0 <= uncertainty <= 1:
        raise ValueError(f"{label}.uncertainty must be between 0 and 1")


def validate_source_bindings(root: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    doc = _load(root, SOURCE_BINDINGS_REL)
    if set(doc) != {"schemaVersion", "kind", "catalogRepository", "observedAt", "systems", "relations", "doesNotEstablish"}:
        raise ValueError("source bindings fields mismatch")
    if doc.get("schemaVersion") != 1 or doc.get("kind") != "system_catalog_source_bindings":
        raise ValueError("source bindings identity mismatch")
    if doc.get("catalogRepository") != "heimgewebe/systemkatalog":
        raise ValueError("source bindings repository mismatch")
    _timestamp(doc.get("observedAt"), "source bindings observedAt")
    nonclaims = doc.get("doesNotEstablish")
    if not isinstance(nonclaims, list) or not nonclaims or any(not isinstance(item, str) or not item for item in nonclaims):
        raise ValueError("source bindings non-claims missing")

    systems = doc.get("systems")
    if not isinstance(systems, list):
        raise ValueError("source bindings systems must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    node_by_id = {node["id"]: node for node in nodes}
    for index, item in enumerate(systems):
        label = f"source system {index}"
        if not isinstance(item, dict) or set(item) != {"system", "source", "reviewedAt", "method", "uncertainty"}:
            raise ValueError(f"{label} fields mismatch")
        system_id = item.get("system")
        if system_id not in node_by_id or system_id in by_id:
            raise ValueError(f"{label} identity missing, unknown or duplicated")
        source = _source(item.get("source"), f"{label}.source")
        _validate_local_source_bytes(root, source, f"{label}.source")
        node = node_by_id[system_id]
        if node["type"] == "repository":
            expected = "/".join(node["entrypoints"]["repository"].rstrip("/").split("/")[-2:])
            if source["repository"] != expected:
                raise ValueError(f"{label} repository differs from node entrypoint")
        elif source["repository"] != "heimgewebe/systemkatalog":
            raise ValueError(f"{label} non-repository system must bind to the catalog")
        _review_fields(item, label)
        by_id[system_id] = item
    if set(by_id) != set(node_by_id):
        missing = sorted(set(node_by_id) - set(by_id))
        extra = sorted(set(by_id) - set(node_by_id))
        raise ValueError(f"source system coverage mismatch: missing={missing} extra={extra}")

    relations = doc.get("relations")
    if not isinstance(relations, list):
        raise ValueError("source bindings relations must be an array")
    expected_relations = {(edge["from"], edge["to"], edge["type"]) for edge in edges}
    seen_relations: set[tuple[str, str, str]] = set()
    for index, item in enumerate(relations):
        label = f"source relation {index}"
        if not isinstance(item, dict) or set(item) != {"relation", "source", "reviewedAt", "method", "uncertainty"}:
            raise ValueError(f"{label} fields mismatch")
        relation = item.get("relation")
        if not isinstance(relation, dict) or set(relation) != {"from", "to", "type"}:
            raise ValueError(f"{label}.relation fields mismatch")
        key = (relation.get("from"), relation.get("to"), relation.get("type"))
        if key not in expected_relations or key in seen_relations:
            raise ValueError(f"{label} identity missing, unknown or duplicated")
        source = _source(item.get("source"), f"{label}.source")
        _validate_local_source_bytes(root, source, f"{label}.source")
        if source["repository"] != "heimgewebe/systemkatalog" or source["locator"]["kind"] != "json_pointer":
            raise ValueError(f"{label} must bind to the curated edge registry")
        _review_fields(item, label)
        seen_relations.add(key)
    if seen_relations != expected_relations:
        raise ValueError("source relation coverage mismatch")
    return doc


def validate_freshness_policy(root: Path) -> dict[str, Any]:
    doc = _load(root, FRESHNESS_POLICY_REL)
    required = {"schemaVersion", "kind", "owner", "statusProjectionOwner", "proposalOnly", "autoMerge", "driftCandidateId", "rules", "doesNotEstablish"}
    if set(doc) != required:
        raise ValueError("freshness policy fields mismatch")
    if doc.get("schemaVersion") != 1 or doc.get("kind") != "system_catalog_freshness_policy":
        raise ValueError("freshness policy identity mismatch")
    if doc.get("owner") != "repo:systemkatalog" or doc.get("statusProjectionOwner") != "repo:leitstand":
        raise ValueError("freshness policy ownership mismatch")
    if doc.get("proposalOnly") is not True or doc.get("autoMerge") is not False:
        raise ValueError("freshness policy must remain proposal-only")
    if doc.get("driftCandidateId") != "SYSTEMKATALOG-DRIFT-CLOSED-LOOP-V1":
        raise ValueError("freshness policy candidate binding mismatch")
    rules = doc.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("freshness policy rules missing")
    expected_ids = {"repository_inventory", "fleet_membership", "primary_source_document", "catalog_semantics", "check_failure"}
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != {"id", "authority", "detectWithinMinutes", "reviewWithinHours", "effect"}:
            raise ValueError(f"freshness rule {index} fields mismatch")
        rule_id = rule.get("id")
        if rule_id not in expected_ids or rule_id in seen:
            raise ValueError(f"freshness rule {index} id invalid or duplicated")
        for field in ("detectWithinMinutes", "reviewWithinHours"):
            value = rule.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"freshness rule {index}.{field} must be positive integer")
        if rule.get("effect") not in {"fail_check", "register_bureau_candidate", "request_semantic_review"}:
            raise ValueError(f"freshness rule {index}.effect invalid")
        if not isinstance(rule.get("authority"), str) or not rule["authority"]:
            raise ValueError(f"freshness rule {index}.authority missing")
        seen.add(rule_id)
    if seen != expected_ids:
        raise ValueError("freshness policy rule coverage mismatch")
    nonclaims = doc.get("doesNotEstablish")
    if not isinstance(nonclaims, list) or not nonclaims:
        raise ValueError("freshness policy non-claims missing")
    return doc
