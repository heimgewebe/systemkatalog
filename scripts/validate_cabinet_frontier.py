#!/usr/bin/env python3
"""Validate Cabinet Frontier candidate JSONL."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

KIND = "cabinet_frontier_candidate"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-frontier-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-frontier-v1.schema.json"
RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
EFFECT_FLAGS = (
    "taskCreationAllowed",
    "queueMutationAllowed",
    "dispatchAllowed",
    "mergeOrPushAllowed",
    "runtimeMutationAllowed",
    "cleanupAllowed",
    "dumpGenerationAllowed",
    "authorityInferenceAllowed",
)
FORBIDDEN_EFFECTS = (
    "bureau_task_creation",
    "queue_mutation",
    "agent_dispatch",
    "merge_or_push",
    "runtime_mutation",
    "cleanup_action",
    "dump_generation",
    "authority_inference",
)
DOES_NOT_ESTABLISH = (
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "autonomous_dispatch",
    "bureau_import_implemented",
    "bureau_task_created",
)
TOP_LEVEL = {
    "schemaVersion",
    "kind",
    "contractVersion",
    "contractPath",
    "schemaPath",
    "id",
    "createdAt",
    "source",
    "target",
    "proposal",
    "acceptance",
    "evidence",
    "forbiddenEffects",
    "effectFlags",
    "doesNotEstablish",
}


class CabinetFrontierError(ValueError):
    """Raised when a Frontier candidate violates the contract."""


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise CabinetFrontierError(f"{label} must be a non-empty trimmed string")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CabinetFrontierError(f"{label} must be an object")
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
        raise CabinetFrontierError(f"{label} fields mismatch (" + "; ".join(parts) + ")")


def _timestamp(value: Any, label: str) -> str:
    raw = _text(value, label)
    if not RFC3339_RE.fullmatch(raw):
        raise CabinetFrontierError(f"{label} must be an RFC3339 timestamp with timezone")
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise CabinetFrontierError(f"{label} must be parseable ISO datetime") from exc
    return raw


def _string_list(value: Any, label: str, *, exact: tuple[str, ...] | None = None, prefix: str | None = None) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CabinetFrontierError(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        raw = _text(item, f"{label} item {index}")
        if prefix and not raw.startswith(prefix):
            raise CabinetFrontierError(f"{label} item {index} must start with {prefix}")
        result.append(raw)
    if len(result) != len(set(result)):
        raise CabinetFrontierError(f"{label} must not contain duplicates")
    if exact is not None and set(result) != set(exact):
        raise CabinetFrontierError(f"{label} must exactly list required values")
    return result


def validate_candidate(candidate: dict[str, Any]) -> None:
    _exact_keys(candidate, TOP_LEVEL, "top-level")
    if candidate["schemaVersion"] != 1 or candidate["kind"] != KIND:
        raise CabinetFrontierError("identity mismatch")
    if candidate["contractVersion"] != CONTRACT_VERSION or candidate["contractPath"] != CONTRACT_PATH or candidate["schemaPath"] != SCHEMA_PATH:
        raise CabinetFrontierError("contract mismatch")
    if not _text(candidate["id"], "id").startswith("frontier:"):
        raise CabinetFrontierError("id must start with frontier:")
    _timestamp(candidate["createdAt"], "createdAt")

    source = _object(candidate["source"], "source")
    _exact_keys(source, {"repository", "commit", "maintenanceReportStatus", "maintenanceReportRef", "signalRefs"}, "source")
    if source["repository"] != "heimgewebe/cabinet":
        raise CabinetFrontierError("source.repository must be heimgewebe/cabinet")
    if not isinstance(source["commit"], str) or not COMMIT_RE.fullmatch(source["commit"]):
        raise CabinetFrontierError("source.commit must be a 40-character lowercase git SHA")
    if source["maintenanceReportStatus"] not in {"pass", "warn", "fail", "unknown"}:
        raise CabinetFrontierError("source.maintenanceReportStatus unsupported")
    _text(source["maintenanceReportRef"], "source.maintenanceReportRef")
    signal_refs = source["signalRefs"]
    if not isinstance(signal_refs, list):
        raise CabinetFrontierError("source.signalRefs must be a list")
    if len(signal_refs) != len(set(signal_refs)):
        raise CabinetFrontierError("source.signalRefs must not contain duplicates")
    for index, ref in enumerate(signal_refs, start=1):
        _text(ref, f"source.signalRefs item {index}")
        if not ref.startswith("signal:"):
            raise CabinetFrontierError("source.signalRefs items must start with signal:")

    target = _object(candidate["target"], "target")
    _exact_keys(target, {"repository", "organ"}, "target")
    if not REPO_RE.fullmatch(_text(target["repository"], "target.repository")):
        raise CabinetFrontierError("target.repository must be owner/repo")
    _text(target["organ"], "target.organ")

    proposal = _object(candidate["proposal"], "proposal")
    _exact_keys(proposal, {"title", "summary", "nextAction", "responsibleOrgan", "risk", "priorityHint"}, "proposal")
    for field in ("title", "summary", "nextAction", "responsibleOrgan"):
        _text(proposal[field], f"proposal.{field}")
    if proposal["risk"] not in {"low", "medium", "high", "unknown"}:
        raise CabinetFrontierError("proposal.risk unsupported")
    if proposal["priorityHint"] not in {"now", "next", "later", "blocked"}:
        raise CabinetFrontierError("proposal.priorityHint unsupported")

    acceptance = candidate["acceptance"]
    if not isinstance(acceptance, list) or not acceptance:
        raise CabinetFrontierError("acceptance must be a non-empty list")
    for index, item in enumerate(acceptance, start=1):
        obj = _object(item, f"acceptance {index}")
        _exact_keys(obj, {"id", "assertion"}, f"acceptance {index}")
        _text(obj["id"], f"acceptance {index} id")
        _text(obj["assertion"], f"acceptance {index} assertion")

    evidence = candidate["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise CabinetFrontierError("evidence must be a non-empty list")
    for index, item in enumerate(evidence, start=1):
        obj = _object(item, f"evidence {index}")
        _text(obj.get("type"), f"evidence {index} type")
        _text(obj.get("ref"), f"evidence {index} ref")

    _string_list(candidate["forbiddenEffects"], "forbiddenEffects", exact=FORBIDDEN_EFFECTS)
    flags = _object(candidate["effectFlags"], "effectFlags")
    if set(flags) != set(EFFECT_FLAGS) or any(flags[field] is not False for field in EFFECT_FLAGS):
        raise CabinetFrontierError("all effectFlags must exist and be false")
    _string_list(candidate["doesNotEstablish"], "doesNotEstablish", exact=DOES_NOT_ESTABLISH)


def load_candidates(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CabinetFrontierError(f"line {line_no}: invalid JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise CabinetFrontierError(f"line {line_no}: candidate must be an object")
        try:
            validate_candidate(item)
        except CabinetFrontierError as exc:
            raise CabinetFrontierError(f"line {line_no}: {exc}") from exc
        rows.append(item)
    if not rows:
        raise CabinetFrontierError("no frontier candidates found")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = load_candidates(args.input)
    except (OSError, CabinetFrontierError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"validate_cabinet_frontier: {exc}", file=sys.stderr)
        return 1
    payload = {"ok": True, "kind": KIND, "candidateCount": len(rows)}
    print(json.dumps(payload, sort_keys=True) if args.json else f"cabinet-frontier: ok candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
