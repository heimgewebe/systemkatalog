#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "registry/ecosystem/authority-matrix.v1.json"
USAGE = ROOT / "registry/ecosystem/consumer-usage.v1.json"

FORBIDDEN_PUBLIC_USAGE_KEYS = {
    "active",
    "address",
    "endpoint",
    "finding",
    "host",
    "hosts",
    "httpprobe",
    "journallines7d",
    "listeners",
    "localunit",
    "method",
    "ports",
    "reachability",
    "remotefindings",
    "status",
    "url",
}
FORBIDDEN_PUBLIC_USAGE_FRAGMENTS = (
    "127.0.0.1",
    ".service",
    ".timer",
    "no route to host",
)


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def _normalize_key(value: str) -> str:
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


def _validate_public_usage(usage: dict[str, Any]) -> None:
    if usage.get("kind") != "operator_consumer_usage_snapshot":
        raise ValueError("usage kind mismatch")
    if usage.get("visibility") != "public_redacted_summary":
        raise ValueError("usage snapshot must be an explicitly redacted public summary")

    present_keys = {_normalize_key(key) for key in _walk_keys(usage)}
    leaked_keys = sorted(FORBIDDEN_PUBLIC_USAGE_KEYS & present_keys)
    if leaked_keys:
        raise ValueError(f"public usage snapshot exposes private runtime keys: {', '.join(leaked_keys)}")

    rendered = json.dumps(usage, ensure_ascii=False).lower()
    leaked_fragments = [fragment for fragment in FORBIDDEN_PUBLIC_USAGE_FRAGMENTS if fragment in rendered]
    if leaked_fragments:
        raise ValueError(
            "public usage snapshot exposes private runtime values: " + ", ".join(leaked_fragments)
        )

    coverage = usage.get("coverageSummary")
    if not isinstance(coverage, dict):
        raise ValueError("coverageSummary missing")
    for field in ("observedLocations", "partiallyObservedLocations", "unknownLocations"):
        value = coverage.get(field)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"coverageSummary.{field} must be a non-negative integer")

    private_evidence = usage.get("privateEvidence")
    if not isinstance(private_evidence, dict):
        raise ValueError("privateEvidence boundary missing")
    if private_evidence.get("storedOutsideRepository") is not True:
        raise ValueError("private runtime evidence must remain outside the repository")
    if private_evidence.get("publicDetailsRedacted") is not True:
        raise ValueError("public runtime details must remain redacted")

    surfaces = usage.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("usage surfaces missing")
    if any(
        not isinstance(item, dict)
        or not item.get("id")
        or not item.get("classification")
        or not item.get("usageSignal")
        or not item.get("decision")
        for item in surfaces
    ):
        raise ValueError("each surface needs id, classification, usageSignal and decision")


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

    _validate_public_usage(usage)
    surfaces = usage["surfaces"]
    coverage = usage["coverageSummary"]
    return {
        "status": "valid",
        "authorityDomains": len(authorities),
        "surfaces": len(surfaces),
        "publicRuntimeDetails": "redacted",
        "coverageLocations": sum(
            coverage[field]
            for field in ("observedLocations", "partiallyObservedLocations", "unknownLocations")
        ),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
