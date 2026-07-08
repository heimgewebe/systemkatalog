#!/usr/bin/env python3
"""Run the Cabinet Gemini maintenance dry run locally with a personal Gemini CLI login."""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from extract_gemini_maintenance_scan import main as extract_main
from write_gemini_maintenance_evidence_packet import write_packet

DEFAULT_OUTPUT_DIR = Path("pruefung/10 Laeufe")
EVIDENCE_PACKET_NAME = "gemini-maintenance-evidence-packet-v1.json"
RAW_OUTPUT_NAME = "gemini-maintenance-dry-run-raw-output.json"
SCAN_OUTPUT_NAME = "gemini-maintenance-dry-run-scan.json"
REVIEW_OUTPUT_NAME = "gemini-maintenance-dry-run-review.md"
SUMMARY_OUTPUT_NAME = "gemini-maintenance-dry-run-gemini-summary.txt"
ERROR_OUTPUT_NAME = "gemini-maintenance-dry-run-gemini-error.txt"
WRAPPER_OUTPUT_NAME = "gemini-maintenance-dry-run-gemini-wrapper.json"
PROMPT_OUTPUT_NAME = "gemini-maintenance-dry-run-prompt.md"


class LocalDryRunError(RuntimeError):
    """Raised when the local dry run cannot execute."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LocalDryRunError("could not determine repository HEAD") from exc
    commit = result.stdout.strip()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise LocalDryRunError(f"invalid repository HEAD: {commit!r}")
    return commit


def _require_gemini(gemini_bin: str) -> str:
    resolved = shutil.which(gemini_bin)
    if resolved is None:
        raise LocalDryRunError(
            "Gemini CLI was not found on PATH. Install it, then run `gemini` once and sign in with Google before retrying."
        )
    return resolved


def _model_response_from_stdout(stdout: str) -> str:
    """Return model text from Gemini CLI stdout, unwrapping --output-format json when present."""
    stripped = stdout.strip()
    if not stripped:
        return ""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stdout
    if isinstance(payload, dict) and isinstance(payload.get("response"), str):
        return payload["response"]
    return stdout


def build_prompt(evidence_packet: Path) -> str:
    return f"""You are a read-only Cabinet maintenance scout.

Read only this curated evidence packet:
{evidence_packet.as_posix()}

Do not read private logs, .agents runtime content, unrestricted runtime data, secrets, environment files, issue bodies, pull request bodies, comments, or files outside the evidence packet. Do not request repository writes, issue creation, pull request creation, comments, Bureau task creation, queue mutation, Grabowski dispatch, push, merge, deploy, cleanup, runtime access, secrets, private logs, or recurrence.

Return exactly one JSON object. Do not wrap it in Markdown. It must match docs/contracts/cabinet-gemini-maintenance-scan-v1.md and scripts/validate_gemini_maintenance_scan.py.

Fixed values:
- schemaVersion: 1
- kind: cabinet_gemini_maintenance_scan
- contractVersion: "1"
- contractPath: docs/contracts/cabinet-gemini-maintenance-scan-v1.md
- schemaPath: docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json
- source.repository: heimgewebe/cabinet
- source.commit: use the current commit SHA printed in the evidence packet source.commit
- source.executionManifestRef: policy/gemini-maintenance-execution-manifest.v1.json
- source.evidenceManifestRef: {evidence_packet.as_posix()}
- lane.id: cabinet-gemini-maintenance
- lane.bureauTask: CABINET-GEMINI-MAINT-V1-T004
- lane.mode: manual_dry_run

Findings:
- observed findings must be directly evidenced by evidenceRefs from the packet.
- plausible and speculative findings must be labelled in the correct lists.
- do not overclaim claim truth, task approval, merge readiness, runtime correctness, Bureau import, autonomous dispatch, Bureau task creation, schedule approval, or Gemini schedulability.

All effectFlags must be false:
issueCreated, prCreated, commentCreated, taskCreated, queueMutated, grabowskiDispatched, pushOrMerge, runtimeMutated, secretRequested, dumpGenerated, cleanupAction.

forbiddenEffects must list exactly:
issue_creation, pr_creation, comment_creation, bureau_task_creation, queue_mutation, grabowski_dispatch, merge_or_push, runtime_mutation, secret_request, dump_generation, cleanup_action.

doesNotEstablish must list exactly:
task_approval, claim_truth, merge_readiness, runtime_correctness, bureau_import, autonomous_dispatch, bureau_task_created, schedule_approval, gemini_schedulability.
"""


def _write_review(path: Path, *, status: str, timestamp: str) -> None:
    path.write_text(
        f"""# Gemini Maintenance Local Dry Run Review

Timestamp: `{timestamp}`
Mode: local personal Gemini CLI login
Status: `{status}`
Bureau task: `CABINET-GEMINI-MAINT-V1-T004`

## Required review points

- Useful findings:
- False positives:
- Missing evidence:
- Hallucinated refs:
- Overclaiming:
- Any effect flag violation:
- Schedule readiness: not established
- Bureau import readiness: not established

## Boundary

This artifact does not approve a schedule, create a task, create an issue, create a pull request, comment on GitHub, dispatch Grabowski, mutate runtime, push, merge, deploy or clean up anything.
""",
        encoding="utf-8",
    )


def _run_extractor(arguments: list[str]) -> int:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return extract_main(arguments)


def run_local_dry_run(
    *,
    repo_root: Path,
    output_dir: Path,
    gemini_bin: str,
    allow_blocked: bool,
    dry_run: bool,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir if output_dir.is_absolute() else repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    evidence_packet = output_dir / EVIDENCE_PACKET_NAME
    raw_output = output_dir / RAW_OUTPUT_NAME
    scan_output = output_dir / SCAN_OUTPUT_NAME
    review_output = output_dir / REVIEW_OUTPUT_NAME
    summary_output = output_dir / SUMMARY_OUTPUT_NAME
    error_output = output_dir / ERROR_OUTPUT_NAME
    wrapper_output = output_dir / WRAPPER_OUTPUT_NAME
    prompt_output = output_dir / PROMPT_OUTPUT_NAME

    write_packet(repo_root, evidence_packet)
    relative_evidence = evidence_packet.relative_to(repo_root)
    prompt = build_prompt(relative_evidence)
    prompt_output.write_text(prompt, encoding="utf-8")
    commit = _repo_commit(repo_root)
    created_at = _timestamp()

    if dry_run:
        wrapper_output.write_text("", encoding="utf-8")
        summary_output.write_text("", encoding="utf-8")
        error_output.write_text("dry-run mode; Gemini CLI was not invoked\n", encoding="utf-8")
        status = "prepared"
        rc = 0
    else:
        gemini = _require_gemini(gemini_bin)
        result = subprocess.run(
            [gemini, "--prompt", prompt, "--output-format", "json"],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        wrapper_output.write_text(result.stdout, encoding="utf-8")
        summary_output.write_text(_model_response_from_stdout(result.stdout), encoding="utf-8")
        error_output.write_text(result.stderr, encoding="utf-8")
        rc = result.returncode
        status = "gemini_executed"

    extract_rc = _run_extractor([
        "--summary-input",
        str(summary_output),
        "--error-input",
        str(error_output),
        "--raw-output",
        str(raw_output),
        "--scan-output",
        str(scan_output),
        "--source-commit",
        commit,
        "--evidence-manifest-ref",
        relative_evidence.as_posix(),
        "--created-at",
        created_at,
        "--json",
    ])
    scan = json.loads(scan_output.read_text(encoding="utf-8"))
    scan_status = scan.get("status", "unknown")
    _write_review(review_output, status=str(scan_status), timestamp=created_at)

    ok = scan_status == "completed"
    payload = {
        "ok": ok,
        "status": status,
        "geminiReturnCode": rc,
        "extractReturnCode": extract_rc,
        "scanStatus": scan_status,
        "evidencePacket": str(evidence_packet),
        "rawOutput": str(raw_output),
        "scanOutput": str(scan_output),
        "reviewOutput": str(review_output),
        "summaryOutput": str(summary_output),
        "errorOutput": str(error_output),
        "wrapperOutput": str(wrapper_output),
        "promptOutput": str(prompt_output),
    }
    if ok or allow_blocked:
        return payload
    raise LocalDryRunError(
        "Gemini local dry run did not complete with a validated completed scan; inspect generated artifacts."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Cabinet repository root")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="directory for dry-run artifacts")
    parser.add_argument("--gemini-bin", default="gemini", help="Gemini CLI executable name or path")
    parser.add_argument("--allow-blocked", action="store_true", help="exit zero even when the scan artifact is blocked")
    parser.add_argument("--dry-run", action="store_true", help="prepare artifacts without invoking Gemini CLI")
    parser.add_argument("--json", action="store_true", help="print machine-readable status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = run_local_dry_run(
            repo_root=Path(args.repo_root),
            output_dir=Path(args.output_dir),
            gemini_bin=args.gemini_bin,
            allow_blocked=args.allow_blocked,
            dry_run=args.dry_run,
        )
    except LocalDryRunError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"run_gemini_maintenance_local_dry_run: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"local Gemini dry run: scan_status={payload['scanStatus']} scan={payload['scanOutput']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
