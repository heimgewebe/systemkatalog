#!/usr/bin/env python3
"""Validate stable, status-free resilience semantics for Systemkatalog."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

RESILIENCE_REL = Path("registry/ecosystem/resilience.v1.json")
RESILIENCE_SCHEMA_REL = Path("catalog/resilience.schema.v1.json")

CRITICALITY_CLASSES = (
    "foundational", "essential", "supporting", "optional", "unknown",
)
COUPLING_CLASSES = (
    "synchronous-blocking", "asynchronous-durable", "asynchronous-lossy",
    "observational", "manual", "unknown",
)
FAILURE_POLICIES = ("block", "queue", "degrade", "fallback", "ignore", "unknown")
AUTHORITY_DIRECTIONS = ("from-to", "to-from", "bidirectional", "none", "unknown")
RECOVERY_INDEPENDENCE_CLASSES = (
    "independent", "partially-shared", "same-failure-domain", "unknown",
)
FAILURE_DOMAIN_KINDS = {
    "human", "host", "identity", "provider", "network", "credentials",
    "data", "control", "stream", "runtime",
}
RECOVERY_KINDS = {"rollback", "restore", "durable-queue", "failover", "manual-recovery"}
TARGET_AUTHORITY_RELATION_TYPES = {"operates_on", "validated_by", "renders", "observes", "displayed_by"}
TOP_FIELDS = {
    "schemaVersion", "kind", "owner", "catalogRole", "updatedAt",
    "defaultCriticality", "criticalityClasses", "couplingClasses",
    "failurePolicies", "authorityDirections", "recoveryIndependenceClasses",
    "failureDomains", "systems", "relations", "recoveryModes",
    "doesNotEstablish",
}
FAILURE_DOMAIN_FIELDS = {"id", "kind", "meaning", "doesNotEstablish"}
SYSTEM_FIELDS = {
    "system", "criticality", "failureDomains", "recoveryModeRefs",
    "acceptedSinglePathRisks", "evidence", "uncertainty",
}
RELATION_FIELDS = {
    "relation", "coupling", "failurePolicy", "authorityDirection",
    "recoveryModeRef", "evidence", "uncertainty",
}
RELATION_ID_FIELDS = {"from", "to", "type"}
RECOVERY_FIELDS = {
    "id", "system", "kind", "failureDomains", "independence",
    "sharedFailureDomains", "triggerClass", "returnCondition", "evidence",
    "doesNotEstablish",
}


def _load(root: Path) -> dict[str, Any]:
    value = json.loads((root / RESILIENCE_REL).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{RESILIENCE_REL}: root must be an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _strings(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"{label} must be a {'possibly empty' if allow_empty else 'non-empty'} string array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates")
    return value


def _uncertainty(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be between 0 and 1")
    return float(value)


def _evidence(root: Path, value: Any, label: str) -> list[str]:
    paths = _strings(value, label, allow_empty=False)
    for raw in paths:
        candidate = Path(raw)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"{label} must contain repository-relative paths")
        if not (root / candidate).is_file():
            raise ValueError(f"{label} evidence missing: {raw}")
    return paths


def relation_key(value: dict[str, Any]) -> tuple[str, str, str]:
    return (value["from"], value["to"], value["type"])


def indexes(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "system": {item["system"]: item for item in document["systems"]},
        "relation": {relation_key(item["relation"]): item for item in document["relations"]},
        "failureDomain": {item["id"]: item for item in document["failureDomains"]},
        "recoveryMode": {item["id"]: item for item in document["recoveryModes"]},
    }


def validate_resilience(
    root: Path,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    root = root.resolve()
    document = _load(root)
    if set(document) != TOP_FIELDS:
        raise ValueError("resilience registry fields mismatch")
    if (
        document.get("schemaVersion") != 1
        or document.get("kind") != "system_catalog_resilience"
        or document.get("owner") != "repo:systemkatalog"
        or document.get("catalogRole") != "canonical_stable_resilience_semantics"
    ):
        raise ValueError("resilience registry identity mismatch")
    try:
        date.fromisoformat(_string(document.get("updatedAt"), "resilience updatedAt"))
    except ValueError as exc:
        raise ValueError("resilience updatedAt must be an ISO date") from exc
    class_contracts = {
        "criticalityClasses": CRITICALITY_CLASSES,
        "couplingClasses": COUPLING_CLASSES,
        "failurePolicies": FAILURE_POLICIES,
        "authorityDirections": AUTHORITY_DIRECTIONS,
        "recoveryIndependenceClasses": RECOVERY_INDEPENDENCE_CLASSES,
    }
    for field, expected in class_contracts.items():
        if document.get(field) != list(expected):
            raise ValueError(f"resilience {field} contract mismatch")
    if document.get("defaultCriticality") != "unknown":
        raise ValueError("resilience default criticality must remain unknown")
    _strings(document.get("doesNotEstablish"), "resilience doesNotEstablish", allow_empty=False)

    raw_domains = document.get("failureDomains")
    if not isinstance(raw_domains, list) or not raw_domains:
        raise ValueError("resilience failureDomains must be a non-empty array")
    domains: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_domains):
        label = f"failure domain {index}"
        if not isinstance(item, dict) or set(item) != FAILURE_DOMAIN_FIELDS:
            raise ValueError(f"{label} fields mismatch")
        identifier = _string(item.get("id"), f"{label}.id")
        if ":" not in identifier or identifier in domains:
            raise ValueError(f"{label} id is invalid or duplicated")
        if item.get("kind") not in FAILURE_DOMAIN_KINDS:
            raise ValueError(f"{label} kind is invalid")
        _string(item.get("meaning"), f"{label}.meaning")
        _strings(item.get("doesNotEstablish"), f"{label}.doesNotEstablish", allow_empty=False)
        domains[identifier] = item

    known_systems = {item["id"] for item in nodes}
    raw_systems = document.get("systems")
    if not isinstance(raw_systems, list):
        raise ValueError("resilience systems must be an array")
    systems: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_systems):
        label = f"system resilience {index}"
        if not isinstance(item, dict) or set(item) != SYSTEM_FIELDS:
            raise ValueError(f"{label} fields mismatch")
        system = _string(item.get("system"), f"{label}.system")
        if system not in known_systems or system in systems:
            raise ValueError(f"{label} system is unknown or duplicated")
        if item.get("criticality") not in CRITICALITY_CLASSES:
            raise ValueError(f"{label} criticality is invalid")
        for domain in _strings(item.get("failureDomains"), f"{label}.failureDomains"):
            if domain not in domains:
                raise ValueError(f"{label} references unknown failure domain: {domain}")
        mode_refs = _strings(item.get("recoveryModeRefs"), f"{label}.recoveryModeRefs")
        accepted_risks = _strings(item.get("acceptedSinglePathRisks"), f"{label}.acceptedSinglePathRisks")
        if item.get("criticality") in {"foundational", "essential"} and not mode_refs and not accepted_risks:
            raise ValueError(f"{label} critical system requires a recovery mode or accepted single-path risk")
        _evidence(root, item.get("evidence"), f"{label}.evidence")
        _uncertainty(item.get("uncertainty"), f"{label}.uncertainty")
        systems[system] = item
    if set(systems) != known_systems:
        missing = sorted(known_systems - set(systems))
        extra = sorted(set(systems) - known_systems)
        raise ValueError(f"resilience system coverage mismatch: missing={missing} extra={extra}")

    raw_modes = document.get("recoveryModes")
    if not isinstance(raw_modes, list):
        raise ValueError("resilience recoveryModes must be an array")
    modes: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_modes):
        label = f"recovery mode {index}"
        if not isinstance(item, dict) or set(item) != RECOVERY_FIELDS:
            raise ValueError(f"{label} fields mismatch")
        identifier = _string(item.get("id"), f"{label}.id")
        if identifier in modes:
            raise ValueError(f"{label} id is duplicated")
        system = _string(item.get("system"), f"{label}.system")
        if system not in known_systems:
            raise ValueError(f"{label} system is unknown")
        if item.get("kind") not in RECOVERY_KINDS:
            raise ValueError(f"{label} kind is invalid")
        mode_domains = _strings(item.get("failureDomains"), f"{label}.failureDomains", allow_empty=False)
        for domain in mode_domains:
            if domain not in domains:
                raise ValueError(f"{label} references unknown failure domain: {domain}")
        independence = item.get("independence")
        if independence not in RECOVERY_INDEPENDENCE_CLASSES:
            raise ValueError(f"{label} independence is invalid")
        shared = _strings(item.get("sharedFailureDomains"), f"{label}.sharedFailureDomains")
        if not set(shared).issubset(mode_domains):
            raise ValueError(f"{label} shared failure domains must be a subset of failure domains")
        if independence == "independent" and shared:
            raise ValueError(f"{label} independent mode cannot declare shared failure domains")
        if independence in {"partially-shared", "same-failure-domain"} and not shared:
            raise ValueError(f"{label} shared independence class requires shared failure domains")
        _string(item.get("triggerClass"), f"{label}.triggerClass")
        _string(item.get("returnCondition"), f"{label}.returnCondition")
        _evidence(root, item.get("evidence"), f"{label}.evidence")
        _strings(item.get("doesNotEstablish"), f"{label}.doesNotEstablish", allow_empty=False)
        modes[identifier] = item

    for system, item in systems.items():
        for mode_ref in item["recoveryModeRefs"]:
            if mode_ref not in modes:
                raise ValueError(f"system resilience {system} references unknown recovery mode: {mode_ref}")
            if modes[mode_ref]["system"] != system:
                raise ValueError(f"system resilience {system} references another system's recovery mode: {mode_ref}")

    known_relations = {relation_key(item) for item in edges}
    raw_relations = document.get("relations")
    if not isinstance(raw_relations, list):
        raise ValueError("resilience relations must be an array")
    relations: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, item in enumerate(raw_relations):
        label = f"relation resilience {index}"
        if not isinstance(item, dict) or set(item) != RELATION_FIELDS:
            raise ValueError(f"{label} fields mismatch")
        identity = item.get("relation")
        if not isinstance(identity, dict) or set(identity) != RELATION_ID_FIELDS:
            raise ValueError(f"{label}.relation fields mismatch")
        for field in RELATION_ID_FIELDS:
            _string(identity.get(field), f"{label}.relation.{field}")
        key = relation_key(identity)
        if key not in known_relations or key in relations:
            raise ValueError(f"{label} relation is unknown or duplicated")
        if item.get("coupling") not in COUPLING_CLASSES:
            raise ValueError(f"{label} coupling is invalid")
        if item.get("failurePolicy") not in FAILURE_POLICIES:
            raise ValueError(f"{label} failure policy is invalid")
        if item.get("authorityDirection") not in AUTHORITY_DIRECTIONS:
            raise ValueError(f"{label} authority direction is invalid")
        mode_ref = item.get("recoveryModeRef")
        if mode_ref is not None and mode_ref not in modes:
            raise ValueError(f"{label} recovery mode is unknown")
        if item.get("failurePolicy") == "fallback" and mode_ref is None:
            raise ValueError(f"{label} fallback requires a recovery mode")
        if identity["type"] == "scope_boundary" and item.get("authorityDirection") != "none":
            raise ValueError(f"{label} scope boundary must not transfer authority")
        if item.get("authorityDirection") == "none" and identity["type"] != "scope_boundary":
            raise ValueError(f"{label} no-authority direction is only valid for scope boundaries")
        if identity["type"] in TARGET_AUTHORITY_RELATION_TYPES and item.get("authorityDirection") != "to-from":
            raise ValueError(f"{label} target-owned relation must preserve target authority")
        if mode_ref is not None and modes[mode_ref]["system"] not in {identity["from"], identity["to"]}:
            raise ValueError(f"{label} recovery mode must belong to one relation endpoint")
        _evidence(root, item.get("evidence"), f"{label}.evidence")
        _uncertainty(item.get("uncertainty"), f"{label}.uncertainty")
        relations[key] = item

    return document
