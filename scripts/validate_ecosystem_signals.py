#!/usr/bin/env python3
"""Validate Cabinet ecosystem signal JSONL."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse

KIND = "cabinet_ecosystem_signal"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-ecosystem-signal-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-ecosystem-signal-v1.schema.json"
SOURCE_SYSTEMS = {"github", "ci", "local_git", "worktree", "fixture"}
PR_PREDICATES = {"github_pr_state", "github_pr_draft", "github_check_state"}
RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
)
EFFECT_FLAGS = (
    "taskCreationAllowed",
    "queueMutationAllowed",
    "dispatchAllowed",
    "mergeOrPushAllowed",
    "runtimeMutationAllowed",
    "dumpGenerationAllowed",
    "authorityInferenceAllowed",
)
DOES_NOT_ESTABLISH = (
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "autonomous_dispatch",
    "bureau_import_implemented",
)
REQUIRED = {
    "schemaVersion", "kind", "contractVersion", "contractPath", "schemaPath", "id",
    "observedAt", "sourceSystem", "subject", "predicate", "object", "evidence",
    "freshness", "confidence", "effectFlags", "doesNotEstablish",
}


class EcosystemSignalError(ValueError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise EcosystemSignalError(f"{label} must be a non-empty trimmed string")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EcosystemSignalError(f"{label} must be an object")
    return value


def _iso_timestamp(value: Any, label: str) -> str:
    raw = _text(value, label)
    if not RFC3339_RE.fullmatch(raw):
        raise EcosystemSignalError(f"{label} must be an RFC3339 timestamp with T and timezone")
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise EcosystemSignalError(f"{label} must be an ISO timestamp") from exc
    return raw


def _url(value: Any, label: str) -> str:
    raw = _text(value, label)
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise EcosystemSignalError(f"{label} must be an http(s) URL")
    return raw


def validate_signal(signal: dict[str, Any], *, allow_fixture_source: bool = False) -> None:
    keys = set(signal)
    missing = sorted(REQUIRED - keys)
    unexpected = sorted(keys - REQUIRED)
    if missing or unexpected:
        parts: list[str] = []
        if missing:
            parts.append("missing fields: " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected fields: " + ", ".join(unexpected))
        raise EcosystemSignalError("top-level fields mismatch (" + "; ".join(parts) + ")")
    if signal["schemaVersion"] != 1 or signal["kind"] != KIND:
        raise EcosystemSignalError("identity mismatch")
    if signal["contractVersion"] != CONTRACT_VERSION or signal["contractPath"] != CONTRACT_PATH or signal["schemaPath"] != SCHEMA_PATH:
        raise EcosystemSignalError("contract mismatch")
    if not _text(signal["id"], "id").startswith("signal:"):
        raise EcosystemSignalError("id must start with signal:")
    _iso_timestamp(signal["observedAt"], "observedAt")
    if signal["sourceSystem"] not in SOURCE_SYSTEMS:
        raise EcosystemSignalError("sourceSystem unsupported")
    if signal["sourceSystem"] == "fixture" and not allow_fixture_source:
        raise EcosystemSignalError("fixture sourceSystem requires allow_fixture_source")
    for field in ("subject", "predicate", "object"):
        _text(signal[field], field)
    if signal["predicate"] in PR_PREDICATES and not signal["subject"].startswith("pr:"):
        raise EcosystemSignalError("PR predicates require subject to start with pr:")
    evidence = signal["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise EcosystemSignalError("evidence must be non-empty")
    for index, raw in enumerate(evidence, start=1):
        item = _object(raw, f"evidence {index}")
        _text(item.get("type"), f"evidence {index} type")
        _text(item.get("ref"), f"evidence {index} ref")
        url = item.get("url")
        if url is not None:
            _url(url, f"evidence {index} url")
        sha = item.get("observedHeadSha")
        if sha is not None and (not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha)):
            raise EcosystemSignalError(f"evidence {index} observedHeadSha must be a lowercase git SHA")
    freshness = _object(signal["freshness"], "freshness")
    if set(freshness) != {"basis", "maxAgeHours"} or freshness["basis"] != "observedAt":
        raise EcosystemSignalError("freshness must be based on observedAt")
    if type(freshness["maxAgeHours"]) is not int or freshness["maxAgeHours"] < 1:
        raise EcosystemSignalError("freshness.maxAgeHours must be positive")
    if isinstance(signal["confidence"], bool) or not isinstance(signal["confidence"], (int, float)) or not 0 <= float(signal["confidence"]) <= 1:
        raise EcosystemSignalError("confidence must be 0..1")
    flags = _object(signal["effectFlags"], "effectFlags")
    if set(flags) != set(EFFECT_FLAGS) or any(flags[field] is not False for field in EFFECT_FLAGS):
        raise EcosystemSignalError("all effectFlags must exist and be false")
    non_claims = signal["doesNotEstablish"]
    if (
        not isinstance(non_claims, list)
        or any(not isinstance(item, str) for item in non_claims)
        or len(non_claims) != len(set(non_claims))
        or set(non_claims) != set(DOES_NOT_ESTABLISH)
    ):
        raise EcosystemSignalError("doesNotEstablish must exactly list required non-establishing boundaries")


def load_signals(path: Path, *, allow_fixture_source: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EcosystemSignalError(f"line {line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise EcosystemSignalError(f"line {line_no}: must be an object")
        try:
            validate_signal(value, allow_fixture_source=allow_fixture_source)
        except EcosystemSignalError as exc:
            raise EcosystemSignalError(f"line {line_no}: {exc}") from exc
        rows.append(value)
    if not rows:
        raise EcosystemSignalError("no signals found")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--allow-fixture-source", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = load_signals(args.input, allow_fixture_source=args.allow_fixture_source)
    except (OSError, EcosystemSignalError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"validate_ecosystem_signals: {exc}", file=sys.stderr)
        return 1
    payload = {"ok": True, "kind": KIND, "signalCount": len(rows)}
    print(json.dumps(payload, sort_keys=True) if args.json else f"ecosystem-signals: ok signals={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
