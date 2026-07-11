#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
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
EXPECTED_SOURCE_REPOS = {
    "bureau",
    "cabinet",
    "chronik",
    "grabowski",
    "heimlern",
    "leitstand",
    "lenskit",
    "metarepo",
    "schauwerk",
    "steuerboard",
    "vibe-lab",
    "wgx",
}
EXPECTED_SURFACE_IDS = {
    "cabinet",
    "chronik",
    "heimlern",
    "leitstand",
    "rlens",
    "schauwerk",
    "steuerboard",
    "vibe_lab",
    "wgx",
}
ALLOWED_CONSUMER_CLASSES = {
    "runtime_observed",
    "source_integrated",
    "declared_only",
    "absent",
}
ALLOWED_USAGE_CLASSES = {
    "recent_access_observed",
    "automated_activity_only",
    "runtime_without_operator_access_signal",
    "no_runtime_activity_observed",
    "measurement_unavailable",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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


def _require_nonempty_strings(value: Any, *, context: str) -> None:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{context} must be a non-empty string array")


def _validate_public_usage(usage: dict[str, Any]) -> None:
    if usage.get("kind") != "operator_consumer_usage_snapshot":
        raise ValueError("usage kind mismatch")
    if usage.get("visibility") != "public_redacted_summary":
        raise ValueError("usage snapshot must be an explicitly redacted public summary")
    if usage.get("snapshotRole") != "dated_decision_evidence_not_live_status":
        raise ValueError("usage snapshot must be dated decision evidence, not live status")
    if usage.get("taskId") != "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T007":
        raise ValueError("usage snapshot task binding mismatch")
    if usage.get("schemaVersion") != 1:
        raise ValueError("usage snapshot schema version mismatch")
    if usage.get("window") != "7d":
        raise ValueError("usage snapshot window mismatch")
    if not UTC_TIMESTAMP_RE.fullmatch(str(usage.get("observedAt", ""))):
        raise ValueError("usage snapshot observedAt must be a UTC timestamp")

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
    if not isinstance(coverage.get("detailPolicy"), str) or not coverage["detailPolicy"]:
        raise ValueError("coverageSummary.detailPolicy missing")
    coverage_fields = (
        "registeredLocations",
        "observedLocations",
        "partiallyObservedLocations",
        "unknownLocations",
    )
    for field in coverage_fields:
        value = coverage.get(field)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"coverageSummary.{field} must be a non-negative integer")
    covered = sum(coverage[field] for field in coverage_fields[1:])
    if coverage["registeredLocations"] != covered:
        raise ValueError("coverageSummary registered location count mismatch")

    _require_nonempty_strings(usage.get("measurementMethod"), context="measurementMethod")
    _require_nonempty_strings(usage.get("measurementLimits"), context="measurementLimits")

    private_evidence = usage.get("privateEvidence")
    if not isinstance(private_evidence, dict):
        raise ValueError("privateEvidence boundary missing")
    if private_evidence.get("storedOutsideRepository") is not True:
        raise ValueError("private runtime evidence must remain outside the repository")
    if private_evidence.get("publicDetailsRedacted") is not True:
        raise ValueError("public runtime details must remain redacted")
    if private_evidence.get("evidenceFormat") != "cabinet-consumer-usage-private-evidence-v1":
        raise ValueError("private evidence format mismatch")
    if not SHA256_RE.fullmatch(str(private_evidence.get("evidenceSha256", ""))):
        raise ValueError("private evidence SHA-256 missing or malformed")
    _require_nonempty_strings(private_evidence.get("contains"), context="privateEvidence.contains")

    source_snapshot = usage.get("sourceSnapshot")
    if not isinstance(source_snapshot, dict) or not source_snapshot:
        raise ValueError("sourceSnapshot missing")
    if set(source_snapshot) != EXPECTED_SOURCE_REPOS:
        raise ValueError("sourceSnapshot repository coverage mismatch")
    if any(not isinstance(repo, str) or not repo or not COMMIT_RE.fullmatch(str(commit)) for repo, commit in source_snapshot.items()):
        raise ValueError("sourceSnapshot must map repository ids to full commit hashes")

    surfaces = usage.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("usage surfaces missing")
    ids: list[str] = []
    for item in surfaces:
        if not isinstance(item, dict):
            raise ValueError("each usage surface must be an object")
        for field in ("id", "consumerClass", "usageClass", "usageSignal", "decision", "uncertainty"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ValueError(f"each usage surface requires non-empty {field}")
        ids.append(item["id"])
        if item["consumerClass"] not in ALLOWED_CONSUMER_CLASSES:
            raise ValueError(f"unknown consumer class: {item['consumerClass']}")
        if item["usageClass"] not in ALLOWED_USAGE_CLASSES:
            raise ValueError(f"unknown usage class: {item['usageClass']}")
    if len(ids) != len(set(ids)):
        raise ValueError("usage surface ids must be unique")
    if set(ids) != EXPECTED_SURFACE_IDS:
        raise ValueError("usage surface coverage does not match the registered decision set")

    decision_inputs = usage.get("decisionInputs")
    if not isinstance(decision_inputs, dict) or set(decision_inputs) != {"T004", "T013", "T014"}:
        raise ValueError("decisionInputs must bind T004, T013 and T014")
    if any(not isinstance(value, str) or not value for value in decision_inputs.values()):
        raise ValueError("decisionInputs values must be non-empty strings")

    non_claims = usage.get("doesNotEstablish")
    required_non_claims = {
        "safe_shutdown",
        "complete_remote_inventory",
        "unique_human_users",
        "runtime_health",
        "consumer_semantic_correctness",
        "current_live_status",
        "repository_rename_readiness",
    }
    if not isinstance(non_claims, list) or not required_non_claims.issubset(set(non_claims)):
        raise ValueError("usage snapshot non-claims are incomplete")


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
        "coverageLocations": coverage["registeredLocations"],
        "consumerClasses": dict(sorted(Counter(item["consumerClass"] for item in surfaces).items())),
        "usageClasses": dict(sorted(Counter(item["usageClass"] for item in surfaces).items())),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
