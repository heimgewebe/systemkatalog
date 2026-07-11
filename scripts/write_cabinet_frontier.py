#!/usr/bin/env python3
"""Build proposal-only Cabinet Frontier candidates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from validate_cabinet_frontier import (
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    FORBIDDEN_EFFECTS,
    KIND,
    SCHEMA_PATH,
    validate_candidate,
)
from write_cabinet_live_signals import build_rows as build_signal_rows
from write_cabinet_maintenance_report import build_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("pruefung/10 Laeufe/cabinet-frontier-v1.jsonl")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_id(*parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _flags() -> dict[str, bool]:
    return {key: False for key in EFFECT_FLAGS}


def _repo_for_organ(organ: str) -> str:
    mapping = {
        "cabinet": "heimgewebe/heimgewebe-katalog",
        "bureau": "heimgewebe/bureau",
        "grabowski": "heimgewebe/grabowski",
        "repobrief_lenskit": "heimgewebe/lenskit",
        "heimlern": "heimgewebe/heimlern",
        "leitstand": "heimgewebe/leitstand",
    }
    return mapping.get(organ, "heimgewebe/heimgewebe-katalog")


def _risk_for_status(status: str) -> str:
    if status in {"evidenced", "approved", "draft_decision_with_explicit_human_release"}:
        return "low"
    if status in {"plausible", "draft_decision"}:
        return "medium"
    return "unknown"


def _signal_refs(signals: list[dict[str, Any]]) -> list[str]:
    return sorted({row["id"] for row in signals if isinstance(row.get("id"), str)})


def candidate_from_bureau_candidate(
    bureau_candidate: dict[str, Any],
    *,
    report: dict[str, Any],
    signals: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    source = report.get("source") if isinstance(report.get("source"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    candidate_id = str(bureau_candidate.get("id") or "unknown")
    status = str(bureau_candidate.get("status") or "unknown")
    responsible = str(bureau_candidate.get("responsibleOrgan") or "cabinet")
    next_action = str(bureau_candidate.get("nextAction") or "review_candidate")
    evidence = bureau_candidate.get("evidence") if isinstance(bureau_candidate.get("evidence"), list) else []
    frontier = {
        "schemaVersion": 1,
        "kind": KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "id": f"frontier:cabinet:{_hash_id(candidate_id, next_action, source.get('commit'))}",
        "createdAt": created_at,
        "source": {
            "repository": "heimgewebe/heimgewebe-katalog",
            "commit": str(source.get("commit") or "0" * 40),
            "maintenanceReportStatus": str(summary.get("status") or "unknown"),
            "maintenanceReportRef": "scripts/write_cabinet_maintenance_report.py",
            "signalRefs": _signal_refs(signals),
        },
        "target": {
            "repository": _repo_for_organ(responsible),
            "organ": responsible,
        },
        "proposal": {
            "title": f"Review Cabinet frontier candidate {candidate_id}",
            "summary": "Cabinet proposes this maintenance candidate for Bureau preview/review; it is not a task and has no direct effects.",
            "nextAction": next_action,
            "responsibleOrgan": responsible,
            "risk": _risk_for_status(status),
            "priorityHint": "later",
        },
        "acceptance": [
            {"id": "proposal-only", "assertion": "Candidate remains proposal-only until Bureau review and explicit apply."},
            {"id": "effect-closure", "assertion": "All effect flags remain false; no Bureau task, queue mutation or dispatch is created by Cabinet."},
            {"id": "evidence-bound", "assertion": "Candidate carries maintenance-report evidence and source commit binding."},
        ],
        "evidence": [
            {"type": "cabinet_maintenance_report_candidate", "ref": candidate_id},
            *[{"type": "cabinet_candidate_evidence", "ref": str(item)} for item in evidence if isinstance(item, str) and item],
        ],
        "forbiddenEffects": list(FORBIDDEN_EFFECTS),
        "effectFlags": _flags(),
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }
    validate_candidate(frontier)
    return frontier


def build_frontier_candidates(
    report: dict[str, Any],
    signals: list[dict[str, Any]],
    *,
    created_at: str,
) -> list[dict[str, Any]]:
    raw_candidates = report.get("bureauCandidates")
    if not isinstance(raw_candidates, list):
        raw_candidates = []
    return [
        candidate_from_bureau_candidate(candidate, report=report, signals=signals, created_at=created_at)
        for candidate in raw_candidates
        if isinstance(candidate, dict)
    ]


def build_frontier(repo_root: Path, created_at: str | None = None) -> list[dict[str, Any]]:
    created_at = created_at or now_utc()
    report = build_report(repo_root, generated_at=created_at)
    signals = build_signal_rows(repo_root, observed_at=created_at)
    return build_frontier_candidates(report, signals, created_at=created_at)


def _resolve_output(repo_root: Path, output: Path) -> Path:
    resolved = output if output.is_absolute() else repo_root / output
    resolved = resolved.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"output path escapes repository: {resolved}") from exc
    return resolved


def write_jsonl(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    rows = build_frontier(repo_root, created_at=args.created_at)
    output = _resolve_output(repo_root, args.output) if args.output else None
    if output is not None and not args.check:
        write_jsonl(rows, output)
    if args.json:
        print(json.dumps({"ok": True, "kind": KIND, "candidateCount": len(rows), "output": str(output) if output else None}, sort_keys=True))
    elif output is None or args.check:
        for row in rows:
            print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
