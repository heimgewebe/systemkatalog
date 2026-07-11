#!/usr/bin/env python3
"""Validate Cabinet Gemini maintenance scan JSON artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

KIND = "cabinet_gemini_maintenance_scan"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-gemini-maintenance-scan-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json"
EXECUTION_MANIFEST_REF = "policy/gemini-maintenance-execution-manifest.v1.json"
RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_RE = re.compile(r"^CABINET-GEMINI-MAINT-V1-T[0-9]{3}$")

EFFECT_FLAGS = (
    "issueCreated",
    "prCreated",
    "commentCreated",
    "taskCreated",
    "queueMutated",
    "grabowskiDispatched",
    "pushOrMerge",
    "runtimeMutated",
    "secretRequested",
    "dumpGenerated",
    "cleanupAction",
)
FORBIDDEN_EFFECTS = (
    "issue_creation",
    "pr_creation",
    "comment_creation",
    "bureau_task_creation",
    "queue_mutation",
    "grabowski_dispatch",
    "merge_or_push",
    "runtime_mutation",
    "secret_request",
    "dump_generation",
    "cleanup_action",
)
DOES_NOT_ESTABLISH = (
    "task_approval",
    "claim_truth",
    "merge_readiness",
    "runtime_correctness",
    "bureau_import",
    "autonomous_dispatch",
    "bureau_task_created",
    "schedule_approval",
    "gemini_schedulability",
)
TOP_LEVEL = {
    "schemaVersion",
    "kind",
    "contractVersion",
    "contractPath",
    "schemaPath",
    "id",
    "createdAt",
    "status",
    "source",
    "lane",
    "findings",
    "effectFlags",
    "forbiddenEffects",
    "doesNotEstablish",
}
FINDING_KEYS = {"id", "title", "summary", "severity", "confidence", "evidenceRefs", "recommendedNextAction"}


class GeminiMaintenanceScanError(ValueError):
    """Raised when a Gemini maintenance scan violates the contract."""


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise GeminiMaintenanceScanError(f"{label} must be a non-empty trimmed string")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GeminiMaintenanceScanError(f"{label} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    keys = set(value)
    missing = sorted(expected - keys)
    unexpected = sorted(keys - expected)
    if missing or unexpected:
        parts: list[str] = []
        if missing:
            parts.append("missing fields: " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected fields: " + ", ".join(unexpected))
        raise GeminiMaintenanceScanError(f"{label} fields mismatch (" + "; ".join(parts) + ")")


def _timestamp(value: Any, label: str) -> str:
    raw = _text(value, label)
    if not RFC3339_RE.fullmatch(raw):
        raise GeminiMaintenanceScanError(f"{label} must be an RFC3339 timestamp with timezone")
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise GeminiMaintenanceScanError(f"{label} must be parseable ISO datetime") from exc
    return raw


def _string_list(value: Any, label: str, *, exact: tuple[str, ...] | None = None, prefix: str | None = None, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise GeminiMaintenanceScanError(f"{label} must be a {'list' if allow_empty else 'non-empty list'}")
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        raw = _text(item, f"{label} item {index}")
        if prefix and not raw.startswith(prefix):
            raise GeminiMaintenanceScanError(f"{label} item {index} must start with {prefix}")
        result.append(raw)
    if len(result) != len(set(result)):
        raise GeminiMaintenanceScanError(f"{label} must not contain duplicates")
    if exact is not None and set(result) != set(exact):
        raise GeminiMaintenanceScanError(f"{label} must exactly list required values")
    return result


def _finding(value: Any, label: str, *, require_evidence: bool) -> None:
    item = _object(value, label)
    _exact_keys(item, FINDING_KEYS, label)
    if not _text(item["id"], f"{label}.id").startswith("finding:"):
        raise GeminiMaintenanceScanError(f"{label}.id must start with finding:")
    for field in ("title", "summary", "recommendedNextAction"):
        _text(item[field], f"{label}.{field}")
    if item["severity"] not in {"info", "low", "medium", "high", "unknown"}:
        raise GeminiMaintenanceScanError(f"{label}.severity unsupported")
    if item["confidence"] not in {"low", "medium", "high", "unknown"}:
        raise GeminiMaintenanceScanError(f"{label}.confidence unsupported")
    refs = _string_list(item["evidenceRefs"], f"{label}.evidenceRefs", allow_empty=not require_evidence)
    if require_evidence and not refs:
        raise GeminiMaintenanceScanError(f"{label}.evidenceRefs must not be empty for observed findings")


def _finding_list(value: Any, label: str, *, require_evidence: bool) -> None:
    if not isinstance(value, list):
        raise GeminiMaintenanceScanError(f"{label} must be a list")
    for index, item in enumerate(value, start=1):
        _finding(item, f"{label} item {index}", require_evidence=require_evidence)


def validate_scan(scan: dict[str, Any]) -> None:
    _exact_keys(scan, TOP_LEVEL, "top-level")
    if scan["schemaVersion"] != 1 or scan["kind"] != KIND:
        raise GeminiMaintenanceScanError("identity mismatch")
    if scan["contractVersion"] != CONTRACT_VERSION or scan["contractPath"] != CONTRACT_PATH or scan["schemaPath"] != SCHEMA_PATH:
        raise GeminiMaintenanceScanError("contract mismatch")
    if not _text(scan["id"], "id").startswith("gemini-scan:"):
        raise GeminiMaintenanceScanError("id must start with gemini-scan:")
    _timestamp(scan["createdAt"], "createdAt")
    if scan["status"] not in {"completed", "blocked", "failed"}:
        raise GeminiMaintenanceScanError("status unsupported")

    source = _object(scan["source"], "source")
    _exact_keys(source, {"repository", "commit", "executionManifestRef", "evidenceManifestRef", "inputRefs"}, "source")
    if source["repository"] != "heimgewebe/heimgewebe-katalog":
        raise GeminiMaintenanceScanError("source.repository must be heimgewebe/heimgewebe-katalog")
    if not isinstance(source["commit"], str) or not COMMIT_RE.fullmatch(source["commit"]):
        raise GeminiMaintenanceScanError("source.commit must be a 40-character lowercase git SHA")
    if source["executionManifestRef"] != EXECUTION_MANIFEST_REF:
        raise GeminiMaintenanceScanError("source.executionManifestRef mismatch")
    _text(source["evidenceManifestRef"], "source.evidenceManifestRef")
    _string_list(source["inputRefs"], "source.inputRefs", prefix="evidence:")

    lane = _object(scan["lane"], "lane")
    _exact_keys(lane, {"id", "bureauTask", "mode"}, "lane")
    _text(lane["id"], "lane.id")
    if not isinstance(lane["bureauTask"], str) or not TASK_RE.fullmatch(lane["bureauTask"]):
        raise GeminiMaintenanceScanError("lane.bureauTask must be a Cabinet Gemini maintenance task id")
    if lane["mode"] not in {"manual_dry_run", "scheduled_candidate", "review_only"}:
        raise GeminiMaintenanceScanError("lane.mode unsupported")

    findings = _object(scan["findings"], "findings")
    _exact_keys(findings, {"observed", "plausible", "speculative"}, "findings")
    _finding_list(findings["observed"], "findings.observed", require_evidence=True)
    _finding_list(findings["plausible"], "findings.plausible", require_evidence=False)
    _finding_list(findings["speculative"], "findings.speculative", require_evidence=False)

    flags = _object(scan["effectFlags"], "effectFlags")
    if set(flags) != set(EFFECT_FLAGS) or any(flags[field] is not False for field in EFFECT_FLAGS):
        raise GeminiMaintenanceScanError("all effectFlags must exist and be false")
    _string_list(scan["forbiddenEffects"], "forbiddenEffects", exact=FORBIDDEN_EFFECTS)
    _string_list(scan["doesNotEstablish"], "doesNotEstablish", exact=DOES_NOT_ESTABLISH)


def load_scans(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise GeminiMaintenanceScanError("no Gemini maintenance scans found")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        rows: list[dict[str, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise GeminiMaintenanceScanError(f"line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise GeminiMaintenanceScanError(f"line {line_no}: scan must be an object")
            try:
                validate_scan(item)
            except GeminiMaintenanceScanError as exc:
                raise GeminiMaintenanceScanError(f"line {line_no}: {exc}") from exc
            rows.append(item)
        if not rows:
            raise GeminiMaintenanceScanError("no Gemini maintenance scans found")
        return rows

    if isinstance(parsed, dict):
        rows = [parsed]
    elif isinstance(parsed, list):
        rows = parsed
    else:
        raise GeminiMaintenanceScanError("scan input must be a JSON object, array or JSONL objects")
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise GeminiMaintenanceScanError(f"scan {index} must be an object")
        try:
            validate_scan(item)
        except GeminiMaintenanceScanError as exc:
            raise GeminiMaintenanceScanError(f"scan {index}: {exc}") from exc
    if not rows:
        raise GeminiMaintenanceScanError("no Gemini maintenance scans found")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = load_scans(args.input)
    except (OSError, GeminiMaintenanceScanError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"validate_gemini_maintenance_scan: {exc}", file=sys.stderr)
        return 1
    payload = {"ok": True, "kind": KIND, "scanCount": len(rows)}
    print(json.dumps(payload, sort_keys=True) if args.json else f"gemini-maintenance-scan: ok scans={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
