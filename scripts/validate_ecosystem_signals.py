#!/usr/bin/env python3
"""Validate Cabinet ecosystem signal JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KIND = "cabinet_ecosystem_signal"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-ecosystem-signal-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-ecosystem-signal-v1.schema.json"
SOURCE_SYSTEMS = {"github", "ci", "local_git", "worktree", "fixture"}
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


def validate_signal(signal: dict[str, Any]) -> None:
    if set(signal) != REQUIRED:
        raise EcosystemSignalError("top-level fields mismatch")
    if signal["schemaVersion"] != 1 or signal["kind"] != KIND:
        raise EcosystemSignalError("identity mismatch")
    if signal["contractVersion"] != CONTRACT_VERSION or signal["contractPath"] != CONTRACT_PATH or signal["schemaPath"] != SCHEMA_PATH:
        raise EcosystemSignalError("contract mismatch")
    if not _text(signal["id"], "id").startswith("signal:"):
        raise EcosystemSignalError("id must start with signal:")
    if "T" not in _text(signal["observedAt"], "observedAt"):
        raise EcosystemSignalError("observedAt must be an ISO timestamp")
    if signal["sourceSystem"] not in SOURCE_SYSTEMS:
        raise EcosystemSignalError("sourceSystem unsupported")
    for field in ("subject", "predicate", "object"):
        _text(signal[field], field)
    evidence = signal["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise EcosystemSignalError("evidence must be non-empty")
    for index, raw in enumerate(evidence, start=1):
        item = _object(raw, f"evidence {index}")
        _text(item.get("type"), f"evidence {index} type")
        _text(item.get("ref"), f"evidence {index} ref")
        sha = item.get("observedHeadSha")
        if sha is not None and (not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha)):
            raise EcosystemSignalError(f"evidence {index} observedHeadSha must be a lowercase git SHA")
    freshness = _object(signal["freshness"], "freshness")
    if set(freshness) != {"basis", "maxAgeHours"} or freshness["basis"] != "observedAt":
        raise EcosystemSignalError("freshness must be based on observedAt")
    if isinstance(freshness["maxAgeHours"], bool) or not isinstance(freshness["maxAgeHours"], int) or freshness["maxAgeHours"] < 1:
        raise EcosystemSignalError("freshness.maxAgeHours must be positive")
    if isinstance(signal["confidence"], bool) or not isinstance(signal["confidence"], (int, float)) or not 0 <= float(signal["confidence"]) <= 1:
        raise EcosystemSignalError("confidence must be 0..1")
    flags = _object(signal["effectFlags"], "effectFlags")
    if set(flags) != set(EFFECT_FLAGS) or any(flags[field] is not False for field in EFFECT_FLAGS):
        raise EcosystemSignalError("all effectFlags must exist and be false")
    non_claims = signal["doesNotEstablish"]
    if not isinstance(non_claims, list) or set(DOES_NOT_ESTABLISH) - {item for item in non_claims if isinstance(item, str)}:
        raise EcosystemSignalError("doesNotEstablish missing required entries")


def load_signals(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise EcosystemSignalError(f"line {line_no} must be an object")
        validate_signal(value)
        rows.append(value)
    if not rows:
        raise EcosystemSignalError("no signals found")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("pruefung/00 Signale/ecosystem-signals.jsonl"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = load_signals(args.input)
    except (OSError, json.JSONDecodeError, EcosystemSignalError) as exc:
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
