#!/usr/bin/env python3
"""Extract and validate a Gemini maintenance scan from action output."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from validate_gemini_maintenance_scan import FORBIDDEN_EFFECTS, DOES_NOT_ESTABLISH, EFFECT_FLAGS, GeminiMaintenanceScanError, validate_scan

KIND = "cabinet_gemini_maintenance_scan"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-gemini-maintenance-scan-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json"
EXECUTION_MANIFEST_REF = "policy/gemini-maintenance-execution-manifest.v1.json"
DEFAULT_EVIDENCE_REF = "pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json"
DEFAULT_SOURCE_COMMIT = "0" * 40
DEFAULT_BLOCKED_REASON = "Gemini dry run did not produce a valid completed scan; review raw output and retry manually."


class GeminiScanExtractionError(RuntimeError):
    """Raised when Gemini output cannot be converted into a valid scan."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_optional(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _normalized_reason(reason: str) -> str:
    normalized = " ".join(str(reason or "").split())
    return normalized or DEFAULT_BLOCKED_REASON


def _balanced_json_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for start, char in enumerate(text):
        if char not in "[{":
            continue
        opener = char
        closer = "}" if opener == "{" else "]"
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            current = text[index]
            if in_string:
                if escape:
                    escape = False
                elif current == "\\":
                    escape = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == opener:
                depth += 1
            elif current == closer:
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : index + 1])
                    break
    return candidates


def _strip_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _load_candidate(text: str) -> dict[str, Any]:
    cleaned = _strip_fence(text)
    attempts = [cleaned, *_balanced_json_candidates(cleaned)]
    errors: list[str] = []
    for candidate in attempts:
        if not candidate.strip():
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if isinstance(parsed, list):
            if len(parsed) != 1 or not isinstance(parsed[0], dict):
                errors.append("JSON array must contain exactly one object")
                continue
            parsed = parsed[0]
        if not isinstance(parsed, dict):
            errors.append("JSON value must be an object")
            continue
        return parsed
    detail = "; ".join(error for error in errors[-3:] if error.strip())
    if detail:
        raise GeminiScanExtractionError("could not find a valid JSON object in Gemini summary: " + detail)
    raise GeminiScanExtractionError("could not find a valid JSON object in Gemini summary")


def _blocked_scan(*, created_at: str, source_commit: str, evidence_manifest_ref: str, reason: str) -> dict[str, Any]:
    safe_reason = _normalized_reason(reason)
    return {
        "schemaVersion": 1,
        "kind": KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "id": "gemini-scan:cabinet:" + created_at.replace(":", "-").replace("+00-00", "Z"),
        "createdAt": created_at,
        "status": "blocked",
        "source": {
            "repository": "heimgewebe/heimgewebe-katalog",
            "commit": source_commit,
            "executionManifestRef": EXECUTION_MANIFEST_REF,
            "evidenceManifestRef": evidence_manifest_ref,
            "inputRefs": ["evidence:generated:maintenance-report"],
        },
        "lane": {
            "id": "cabinet-gemini-maintenance",
            "bureauTask": "CABINET-GEMINI-MAINT-V1-T004",
            "mode": "manual_dry_run",
        },
        "findings": {
            "observed": [],
            "plausible": [
                {
                    "id": "finding:plausible:gemini-output-blocked",
                    "title": "Gemini dry run did not produce a valid completed scan",
                    "summary": safe_reason,
                    "severity": "unknown",
                    "confidence": "medium",
                    "evidenceRefs": [],
                    "recommendedNextAction": "review_raw_output_and_retry_manually",
                }
            ],
            "speculative": [],
        },
        "effectFlags": {flag: False for flag in EFFECT_FLAGS},
        "forbiddenEffects": list(FORBIDDEN_EFFECTS),
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


def extract_scan(summary: str, *, created_at: str, source_commit: str, evidence_manifest_ref: str) -> dict[str, Any]:
    scan = _load_candidate(summary)
    validate_scan(scan)
    if scan["source"]["commit"] != source_commit:
        raise GeminiScanExtractionError("scan source.commit does not match workflow commit")
    if scan["source"]["evidenceManifestRef"] != evidence_manifest_ref:
        raise GeminiScanExtractionError("scan source.evidenceManifestRef does not match generated evidence packet path")
    if scan["lane"]["bureauTask"] != "CABINET-GEMINI-MAINT-V1-T004":
        raise GeminiScanExtractionError("scan lane.bureauTask must be CABINET-GEMINI-MAINT-V1-T004")
    return scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-input", type=Path, required=True)
    parser.add_argument("--error-input", type=Path)
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--scan-output", type=Path, required=True)
    parser.add_argument("--source-commit", default=DEFAULT_SOURCE_COMMIT)
    parser.add_argument("--evidence-manifest-ref", default=DEFAULT_EVIDENCE_REF)
    parser.add_argument("--created-at")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    created_at = args.created_at or _timestamp()
    summary = _read_optional(args.summary_input)
    error = _read_optional(args.error_input)
    raw_payload = {
        "schemaVersion": 1,
        "kind": "cabinet_gemini_maintenance_raw_output",
        "createdAt": created_at,
        "sourceCommit": args.source_commit,
        "summary": summary,
        "error": error,
    }
    _write_json(args.raw_output, raw_payload)

    try:
        scan = extract_scan(
            summary,
            created_at=created_at,
            source_commit=args.source_commit,
            evidence_manifest_ref=args.evidence_manifest_ref,
        )
        status = "completed"
        ok = True
        message = "valid Gemini maintenance scan extracted"
    except (GeminiScanExtractionError, GeminiMaintenanceScanError) as exc:
        status = "blocked"
        ok = False
        message = _normalized_reason(str(exc))
        scan = _blocked_scan(
            created_at=created_at,
            source_commit=args.source_commit,
            evidence_manifest_ref=args.evidence_manifest_ref,
            reason=message,
        )
        validate_scan(scan)

    _write_json(args.scan_output, scan)
    payload = {"ok": ok, "status": status, "message": message, "scanOutput": str(args.scan_output)}
    print(json.dumps(payload, sort_keys=True) if args.json else message)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
