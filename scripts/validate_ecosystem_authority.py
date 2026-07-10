#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "registry/ecosystem/authority-matrix.v1.json"
USAGE = ROOT / "registry/ecosystem/consumer-usage.v1.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def validate() -> dict:
    matrix = _load(MATRIX)
    usage = _load(USAGE)
    if matrix.get("kind") != "cabinet_ecosystem_authority_matrix":
        raise ValueError("authority matrix kind mismatch")
    canonical = matrix.get("canonicalMap")
    if canonical != "rendered/ecosystem-registry-map.mmd":
        raise ValueError("exactly the registry-derived map must be canonical")
    if not (ROOT / canonical).is_file():
        raise ValueError("canonical map missing")
    specialized = matrix.get("specializedViews")
    if not isinstance(specialized, list):
        raise ValueError("specializedViews must be array")
    for view in specialized:
        if view.get("authoritative") is not False:
            raise ValueError("specialized views must be non-authoritative")
        if not (ROOT / view["path"]).is_file():
            raise ValueError(f"specialized view missing: {view['path']}")
    authorities = matrix.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        raise ValueError("authorities missing")
    domains = [item.get("domain") for item in authorities]
    if len(domains) != len(set(domains)):
        raise ValueError("authority domains must be unique")
    if any(not item.get("owner") for item in authorities):
        raise ValueError("every domain requires exactly one owner")
    if usage.get("kind") != "operator_consumer_usage_snapshot":
        raise ValueError("usage kind mismatch")
    hosts = {item.get("id"): item.get("status") for item in usage.get("hosts", [])}
    if hosts.get("heimserver") != "unknown_unreachable":
        raise ValueError("unreachable hosts must remain unknown, never absent")
    surfaces = usage.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("usage surfaces missing")
    if any(not item.get("classification") or not item.get("decision") for item in surfaces):
        raise ValueError("each surface needs classification and decision")
    return {"status": "valid", "authorityDomains": len(authorities), "surfaces": len(surfaces)}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
