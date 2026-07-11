#!/usr/bin/env python3
"""Validate the canonical Cabinet catalog map and its legacy bridge boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_system_catalog import validate as validate_system_catalog  # noqa: E402

BRIDGE_REL = Path("registry/ecosystem/bureau-bridge.json")
REQUIRED_PROHIBITED_EFFECTS = {
    "automatic_bureau_task_creation",
    "automatic_grabowski_delegation",
    "merge_or_push_action",
    "runtime_mutation",
    "cleanup_action",
    "authority_inference_from_map",
}


def _load(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: root must be an object")
    return value


def validate_bridge_policy(root: Path, bridge: dict[str, Any]) -> None:
    if bridge.get("status") != "legacy_compatibility_only":
        raise ValueError("Cabinet-Bureau bridge must be legacy compatibility only")
    if bridge.get("catalog_authoritative") is not False:
        raise ValueError("Cabinet-Bureau bridge must be non-authoritative for the catalog")
    if bridge.get("source_owner") != "repo:cabinet" or bridge.get("target_consumer") != "repo:bureau":
        raise ValueError("Cabinet-Bureau bridge endpoints mismatch")
    if bridge.get("organ_roles", {}).get("cabinet") != "legacy_proposal_source_not_task_or_queue_authority":
        raise ValueError("legacy bridge Cabinet role mismatch")
    allowed_sources = bridge.get("allowed_sources")
    if not isinstance(allowed_sources, list) or not allowed_sources:
        raise ValueError("legacy bridge allowed_sources missing")
    if "registry/ecosystem/claims.jsonl" in allowed_sources:
        raise ValueError("legacy bridge must not consume canonical stable catalog claims")
    if "docs/archive/cabinet-era/ecosystem-dynamic-claims-v0.jsonl" not in allowed_sources:
        raise ValueError("legacy bridge archive source missing")
    for relative in allowed_sources:
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise ValueError(f"legacy bridge source missing: {relative}")
    prohibited = set(bridge.get("prohibited_effects", []))
    if not REQUIRED_PROHIBITED_EFFECTS.issubset(prohibited):
        raise ValueError("legacy bridge effect boundary incomplete")
    non_claims = set(bridge.get("does_not_establish", []))
    if not {"task_approval", "merge_readiness", "runtime_correctness", "claim_truth"}.issubset(non_claims):
        raise ValueError("legacy bridge non-claims incomplete")


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    catalog = validate_system_catalog(root)
    bridge = _load(root, BRIDGE_REL)
    validate_bridge_policy(root, bridge)
    return {
        "status": "valid",
        "nodes": catalog["registrySystems"],
        "edges": catalog["registryRelations"],
        "stableClaims": catalog["stableClaims"],
        "authorityDomains": catalog["authorityDomains"],
        "legacyBridge": "non_authoritative_compatibility_only",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
