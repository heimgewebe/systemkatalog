#!/usr/bin/env python3
"""Write or validate Cabinet's read-only maintenance report."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from validate_external_dump_sources import ExternalDumpSourcesError, validate_sources

CONTRACT_VERSION = "1"
REPORT_KIND = "cabinet_maintenance_report"
CONTRACT_PATH = "docs/contracts/cabinet-maintenance-report-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-maintenance-report-v1.schema.json"
DEFAULT_OUTPUT = Path("pruefung/10 Laeufe/cabinet-maintenance-report.json")
EXTERNAL_DUMP_REGISTRY = "registry/ecosystem/external-dump-sources.json"

REGISTRY_ROOT = Path("registry/ecosystem")
NODES_PATH = REGISTRY_ROOT / "nodes.json"
EDGES_PATH = REGISTRY_ROOT / "edges.json"
CLAIMS_PATH = REGISTRY_ROOT / "claims.jsonl"
BUREAU_BRIDGE_PATH = REGISTRY_ROOT / "bureau-bridge.json"

EFFECT_FLAGS = (
    "bureauTaskCreationAllowed",
    "grabowskiDelegationAllowed",
    "mergeOrPushAllowed",
    "runtimeMutationAllowed",
    "cleanupAllowed",
    "dumpGenerationAllowed",
    "authorityInferenceFromMapAllowed",
)

DOES_NOT_ESTABLISH = (
    "claim_truth",
    "runtime_correctness",
    "merge_readiness",
    "task_approval",
    "bureau_import_implemented",
    "autonomous_dispatch",
    "external_dump_freshness_completeness",
)

FINDING_CLASSES = ("consistency", "error", "freshness", "handoff", "authority", "risk")
SEVERITIES = ("P0", "P1", "P2", "P3")
ADMISSIBLE_FALLBACK = {"evidenced", "approved", "draft_decision_with_explicit_human_release"}
BLOCKED_FALLBACK = {"plausible", "speculative", "expired", "contradicted", "unverified"}


class MaintenanceReportError(RuntimeError):
    """Raised when the maintenance report contract cannot be satisfied."""


def _repo_path(repo_root: Path, raw_path: str | Path, label: str) -> Path:
    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise MaintenanceReportError(f"{label} escapes repository: {resolved}") from exc
    return resolved


def _load_json(repo_root: Path, relative_path: Path) -> Any:
    path = _repo_path(repo_root, relative_path, str(relative_path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MaintenanceReportError(f"missing input: {relative_path}") from exc
    except json.JSONDecodeError as exc:
        raise MaintenanceReportError(f"invalid JSON in {relative_path}: {exc}") from exc


def _load_jsonl(repo_root: Path, relative_path: Path) -> list[dict[str, Any]]:
    path = _repo_path(repo_root, relative_path, str(relative_path))
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MaintenanceReportError(f"missing input: {relative_path}") from exc
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MaintenanceReportError(f"invalid JSONL in {relative_path}:{line_no}: {exc}") from exc
        if not isinstance(item, dict):
            raise MaintenanceReportError(f"invalid JSONL in {relative_path}:{line_no}: expected object")
        rows.append(item)
    return rows


def _git_commit(repo_root: Path) -> str:
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
        raise MaintenanceReportError("could not determine git source commit") from exc
    commit = result.stdout.strip()
    if not _is_commit_sha(commit):
        raise MaintenanceReportError(f"invalid git source commit: {commit!r}")
    return commit


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_commit_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _parse_date(raw: str, label: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise MaintenanceReportError(f"invalid {label}: {raw}") from exc


def _node_ids(nodes_doc: Any) -> set[str]:
    if not isinstance(nodes_doc, dict) or not isinstance(nodes_doc.get("nodes"), list):
        raise MaintenanceReportError("nodes registry must contain a nodes list")
    result: set[str] = set()
    for index, node in enumerate(nodes_doc["nodes"], start=1):
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
            raise MaintenanceReportError(f"node {index} id must be a non-empty string")
        result.add(node["id"])
    return result


def _string_set(value: Any, fallback: set[str]) -> set[str]:
    if not isinstance(value, list):
        return set(fallback)
    result = {item for item in value if isinstance(item, str) and item}
    return result or set(fallback)


def _claim_evidence(claim: dict[str, Any]) -> list[str]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [item for item in evidence if isinstance(item, str) and item]


def _claim_expiry(claim: dict[str, Any]) -> date | None:
    value = claim.get("expires_at")
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _expires_at_or_refresh_hint(claim: dict[str, Any]) -> str:
    for key in ("expires_at_or_refresh_hint", "expires_at"):
        value = claim.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _local_evidence_candidate(value: str) -> bool:
    if "://" in value or " in heimgewebe/" in value:
        return False
    if value.startswith(("github.com:", "git@", "claim:", "repo:", "artifact:")):
        return False
    return "/" in value or value.endswith((".md", ".json", ".jsonl", ".py", ".yml", ".yaml"))


def _finding(
    finding_id: str,
    klass: str,
    severity: str,
    status: str,
    subject: str,
    message: str,
    evidence: list[str],
    responsible_organ: str,
    next_action: str,
    bureau_admissible: bool = False,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "class": klass,
        "severity": severity,
        "status": status,
        "subject": subject,
        "message": message,
        "evidence": evidence,
        "responsibleOrgan": responsible_organ,
        "nextAction": next_action,
        "bureauAdmissible": bureau_admissible,
    }


def _is_handoff_ready(claim: dict[str, Any], scan_date: date, admissible: set[str]) -> bool:
    if claim.get("status") not in admissible:
        return False
    if not _claim_evidence(claim):
        return False
    expiry = _claim_expiry(claim)
    if expiry is not None and expiry < scan_date:
        return False
    return all(isinstance(claim.get(key), str) and claim[key] for key in ("next_action", "responsible_organ")) and bool(_expires_at_or_refresh_hint(claim))


def _scan_bridge_sources(repo_root: Path, bridge_doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    sources = bridge_doc.get("allowed_sources")
    if not isinstance(sources, list):
        return [_finding(
            "cabqa:error:bridge:allowed-sources-malformed",
            "error",
            "P1",
            "open",
            "registry/ecosystem/bureau-bridge.json",
            "Bureau bridge allowed_sources is not a list.",
            [str(BUREAU_BRIDGE_PATH)],
            "cabinet",
            "repair_bridge_allowed_sources_shape",
        )]
    for source in sources:
        if not isinstance(source, str) or not source:
            findings.append(_finding(
                "cabqa:error:bridge:allowed-source-empty",
                "error",
                "P1",
                "open",
                "registry/ecosystem/bureau-bridge.json",
                "Bureau bridge allowed_sources contains an empty or non-string value.",
                [str(BUREAU_BRIDGE_PATH)],
                "cabinet",
                "remove_invalid_allowed_source",
            ))
            continue
        if not _repo_path(repo_root, source, f"bridge allowed source {source}").exists():
            findings.append(_finding(
                f"cabqa:consistency:bridge:missing-allowed-source:{source}",
                "consistency",
                "P1",
                "open",
                "registry/ecosystem/bureau-bridge.json",
                f"Bureau bridge allowed source is missing: {source}.",
                [str(BUREAU_BRIDGE_PATH)],
                "cabinet",
                "remove_or_restore_bridge_allowed_source",
            ))
    return findings


def _scan_claims(repo_root: Path, claims: list[dict[str, Any]], node_ids: set[str], bridge_doc: dict[str, Any], scan_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    admissible = _string_set(bridge_doc.get("admissible_candidate_statuses"), ADMISSIBLE_FALLBACK)
    blocked = _string_set(bridge_doc.get("blocked_statuses"), BLOCKED_FALLBACK)

    for index, claim in enumerate(claims, start=1):
        claim_id = claim.get("id") if isinstance(claim.get("id"), str) and claim["id"] else f"claim-line-{index}"
        evidence = _claim_evidence(claim)
        status = claim.get("status")
        if claim.get("subject") not in node_ids:
            findings.append(_finding(
                f"cabqa:consistency:{claim_id}:unknown-subject",
                "consistency",
                "P1",
                "open",
                claim_id,
                f"Claim references unknown subject: {claim.get('subject')!r}.",
                [str(CLAIMS_PATH), str(NODES_PATH)],
                "cabinet",
                "repair_claim_subject_or_registry_node",
            ))
        if not evidence:
            findings.append(_finding(
                f"cabqa:error:{claim_id}:missing-evidence",
                "error",
                "P2",
                "open",
                claim_id,
                "Claim has no non-empty evidence entries.",
                [str(CLAIMS_PATH)],
                "cabinet",
                "add_or_remove_claim_evidence_before_handoff",
            ))
        for item in evidence:
            if _local_evidence_candidate(item) and not _repo_path(repo_root, item, f"evidence {item}").exists():
                findings.append(_finding(
                    f"cabqa:consistency:{claim_id}:missing-evidence-path",
                    "consistency",
                    "P2",
                    "open",
                    claim_id,
                    f"Claim evidence path is missing in Cabinet: {item}.",
                    [str(CLAIMS_PATH), item],
                    "cabinet",
                    "refresh_or_replace_missing_evidence_path",
                ))

        raw_expiry = claim.get("expires_at")
        expiry = _claim_expiry(claim)
        if not isinstance(raw_expiry, str) or not raw_expiry:
            findings.append(_finding(
                f"cabqa:freshness:{claim_id}:missing-expiry",
                "freshness",
                "P2",
                "open",
                claim_id,
                "Claim has no expires_at value.",
                [str(CLAIMS_PATH)],
                "cabinet",
                "add_expiry_or_refresh_hint",
            ))
        elif expiry is None:
            findings.append(_finding(
                f"cabqa:freshness:{claim_id}:invalid-expiry",
                "freshness",
                "P2",
                "open",
                claim_id,
                f"Claim expires_at is not an ISO date: {raw_expiry}.",
                [str(CLAIMS_PATH)],
                "cabinet",
                "rewrite_expires_at_as_iso_date",
            ))
        elif expiry < scan_date:
            findings.append(_finding(
                f"cabqa:freshness:{claim_id}:expired",
                "freshness",
                "P1",
                "blocked",
                claim_id,
                f"Claim expired on {expiry.isoformat()} before scan date {scan_date.isoformat()}.",
                [str(CLAIMS_PATH)],
                "cabinet",
                "refresh_or_retire_expired_claim",
            ))

        ready = _is_handoff_ready(claim, scan_date, admissible)
        handoff_attempt = bool(claim.get("next_action") or claim.get("responsible_organ") or claim.get("expires_at_or_refresh_hint"))
        if status in admissible and handoff_attempt and not ready:
            findings.append(_finding(
                f"cabqa:handoff:{claim_id}:not-bureau-ready",
                "handoff",
                "P2",
                "blocked",
                claim_id,
                "Admissible-status claim is missing Bureau handoff fields or is expired.",
                [str(CLAIMS_PATH), str(BUREAU_BRIDGE_PATH)],
                "cabinet",
                "complete_handoff_fields_or_downgrade_claim_status",
            ))
        if status in blocked and (claim.get("next_action") or claim.get("responsible_organ")):
            findings.append(_finding(
                f"cabqa:handoff:{claim_id}:blocked-status-has-handoff-fields",
                "handoff",
                "P3",
                "blocked",
                claim_id,
                "Blocked-status claim contains handoff fields; keep it as refresh or clarification only.",
                [str(CLAIMS_PATH), str(BUREAU_BRIDGE_PATH)],
                "cabinet",
                "confirm_claim_is_not_promoted_until_status_changes",
            ))
        if ready:
            candidates.append({
                "id": claim_id,
                "status": str(status),
                "evidence": evidence,
                "expiresAtOrRefreshHint": _expires_at_or_refresh_hint(claim),
                "nextAction": str(claim["next_action"]),
                "responsibleOrgan": str(claim["responsible_organ"]),
            })
    return findings, candidates



def _parse_manifest_generated_at(value: str, label: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MaintenanceReportError(f"{label} must be an ISO timestamp") from exc
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def _scan_external_dump_sources(repo_root: Path, scan_time: datetime, external_dump_registry: str) -> list[dict[str, Any]]:
    registry_path = _repo_path(repo_root, external_dump_registry, "external dump registry")
    if not registry_path.exists():
        return []
    try:
        registry = validate_sources(repo_root, registry_path)
    except ExternalDumpSourcesError as exc:
        return [_finding(
            "cabqa:error:external-dump-sources:invalid-registry",
            "error",
            "P1",
            "open",
            external_dump_registry,
            f"External dump source registry is invalid: {exc}.",
            [external_dump_registry],
            "cabinet",
            "repair_external_dump_source_registry_contract",
        )]

    findings: list[dict[str, Any]] = []
    scan_cutoff = scan_time.astimezone(timezone.utc)
    for source in registry["sources"]:
        source_id = source["id"]
        observation = source["observation"]
        status = observation["status"]
        if status == "disabled":
            continue
        if status == "unobserved":
            findings.append(_finding(
                f"cabqa:freshness:{source_id}:manifest-unobserved",
                "freshness",
                "P2",
                "open",
                source_id,
                "External dump source contract exists, but Cabinet has not observed a latest manifest yet.",
                [external_dump_registry],
                "repobrief_lenskit",
                "publish_latest_manifest_reference_or_mark_source_disabled",
            ))
            continue
        generated_at = _parse_manifest_generated_at(
            observation["latestManifestGeneratedAt"],
            f"{source_id} latestManifestGeneratedAt",
        )
        max_age = timedelta(hours=int(source["maxAgeHours"]))
        if generated_at + max_age < scan_cutoff:
            findings.append(_finding(
                f"cabqa:freshness:{source_id}:manifest-stale",
                "freshness",
                "P2",
                "open",
                source_id,
                f"External dump manifest is older than maxAgeHours={source['maxAgeHours']} at report time {scan_cutoff.isoformat()}.",
                [external_dump_registry, observation["latestManifestPath"]],
                "repobrief_lenskit",
                "refresh_external_dump_manifest_reference",
            ))
    return findings

def _epistemic_gaps(repo_root: Path, external_dump_registry: str) -> list[dict[str, str]]:
    if _repo_path(repo_root, external_dump_registry, "external dump registry").exists():
        return []
    return [{
        "id": "cabqa:gap:external-dump-automation-contract-v1",
        "topic": "external_repo_brief_lenskit_dump_automation",
        "missing": "path convention, manifest shape, cadence, hashes, artifact names and retention policy",
        "neededFor": "deterministic freshness scan of externally generated RepoBrief/Lenskit dumps",
        "severity": "P2",
    }]


def _summary(findings: list[dict[str, Any]], candidates: list[dict[str, Any]], gaps: list[dict[str, str]]) -> dict[str, Any]:
    severity_counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        severity_counts[finding["severity"]] += 1
    if severity_counts["P0"] or severity_counts["P1"]:
        status = "fail"
    elif findings or gaps:
        status = "warn"
    else:
        status = "pass"
    return {
        "status": status,
        "findingCount": len(findings),
        "epistemicGapCount": len(gaps),
        "bureauCandidateCount": len(candidates),
        "blockedHandoffCount": sum(1 for finding in findings if finding["class"] == "handoff" and not finding["bureauAdmissible"]),
        "severityCounts": severity_counts,
    }


def build_report(
    repo_root: Path,
    *,
    source_commit: str | None = None,
    generated_at: str | None = None,
    scan_date: date | None = None,
    external_dump_registry: str = EXTERNAL_DUMP_REGISTRY,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    commit = source_commit or _git_commit(repo_root)
    if not _is_commit_sha(commit):
        raise MaintenanceReportError("source_commit must be a 40 character lowercase git SHA")
    generated_at_value = generated_at or _generated_at()
    report_generated_time = _parse_manifest_generated_at(generated_at_value, "report generatedAt")
    date_value = scan_date or report_generated_time.astimezone(timezone.utc).date()

    nodes_doc = _load_json(repo_root, NODES_PATH)
    _load_json(repo_root, EDGES_PATH)
    claims = _load_jsonl(repo_root, CLAIMS_PATH)
    bridge_doc = _load_json(repo_root, BUREAU_BRIDGE_PATH)
    if not isinstance(bridge_doc, dict):
        raise MaintenanceReportError("bureau bridge document must be an object")

    findings = _scan_bridge_sources(repo_root, bridge_doc)
    claim_findings, candidates = _scan_claims(repo_root, claims, _node_ids(nodes_doc), bridge_doc, date_value)
    findings.extend(claim_findings)
    findings.extend(_scan_external_dump_sources(repo_root, report_generated_time, external_dump_registry))
    findings.sort(key=lambda item: (item["severity"], item["class"], item["id"]))
    candidates.sort(key=lambda item: item["id"])
    gaps = _epistemic_gaps(repo_root, external_dump_registry)

    report = {
        "schemaVersion": 1,
        "kind": REPORT_KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "mode": "read_only_coherence_scan",
        "source": {
            "repository": "heimgewebe/cabinet",
            "commit": commit,
            "generatedAt": generated_at_value,
            "scanDate": date_value.isoformat(),
        },
        "effectFlags": {flag: False for flag in EFFECT_FLAGS},
        "summary": _summary(findings, candidates, gaps),
        "findings": findings,
        "bureauCandidates": candidates,
        "epistemicGaps": gaps,
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }
    validate_report(report)
    return report


def validate_report(report: dict[str, Any]) -> None:
    required = {
        "schemaVersion", "kind", "contractVersion", "contractPath", "schemaPath",
        "mode", "source", "effectFlags", "summary", "findings",
        "bureauCandidates", "epistemicGaps", "doesNotEstablish",
    }
    if set(report) != required:
        raise MaintenanceReportError("report top-level fields mismatch")
    if report["schemaVersion"] != 1 or report["kind"] != REPORT_KIND:
        raise MaintenanceReportError("report identity mismatch")
    if report["contractVersion"] != CONTRACT_VERSION or report["contractPath"] != CONTRACT_PATH or report["schemaPath"] != SCHEMA_PATH:
        raise MaintenanceReportError("report contract mismatch")
    if report["mode"] != "read_only_coherence_scan":
        raise MaintenanceReportError("mode mismatch")
    source = report["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "commit", "generatedAt", "scanDate"}:
        raise MaintenanceReportError("source fields mismatch")
    if source["repository"] != "heimgewebe/cabinet" or not _is_commit_sha(source["commit"]):
        raise MaintenanceReportError("source mismatch")
    if not isinstance(source["generatedAt"], str) or not source["generatedAt"]:
        raise MaintenanceReportError("source.generatedAt must be a non-empty string")
    _parse_date(source["scanDate"], "scanDate")

    effect_flags = report["effectFlags"]
    if not isinstance(effect_flags, dict) or set(effect_flags) != set(EFFECT_FLAGS):
        raise MaintenanceReportError("effectFlags fields mismatch")
    for flag in EFFECT_FLAGS:
        if effect_flags[flag] is not False:
            raise MaintenanceReportError(f"effect flag must be false: {flag}")

    findings = report["findings"]
    candidates = report["bureauCandidates"]
    gaps = report["epistemicGaps"]
    if not isinstance(findings, list) or not isinstance(candidates, list) or not isinstance(gaps, list):
        raise MaintenanceReportError("report collections must be lists")
    for finding in findings:
        _validate_finding(finding)
    for candidate in candidates:
        _validate_candidate(candidate)
    for gap in gaps:
        _validate_gap(gap)

    expected_summary = _summary(findings, candidates, gaps)
    if report["summary"] != expected_summary:
        raise MaintenanceReportError("summary does not match report contents")
    non_claims = report["doesNotEstablish"]
    if not isinstance(non_claims, list) or set(non_claims) != set(DOES_NOT_ESTABLISH) or len(non_claims) != len(DOES_NOT_ESTABLISH):
        raise MaintenanceReportError("doesNotEstablish mismatch")


def _validate_finding(finding: Any) -> None:
    fields = {"id", "class", "severity", "status", "subject", "message", "evidence", "responsibleOrgan", "nextAction", "bureauAdmissible"}
    if not isinstance(finding, dict) or set(finding) != fields:
        raise MaintenanceReportError("finding fields mismatch")
    for field in ("id", "subject", "message", "responsibleOrgan", "nextAction"):
        if not isinstance(finding[field], str) or not finding[field]:
            raise MaintenanceReportError(f"finding.{field} must be a non-empty string")
    if finding["class"] not in FINDING_CLASSES or finding["severity"] not in SEVERITIES or finding["status"] not in {"open", "blocked", "candidate"}:
        raise MaintenanceReportError("finding enum mismatch")
    if not isinstance(finding["evidence"], list) or not all(isinstance(item, str) and item for item in finding["evidence"]):
        raise MaintenanceReportError("finding.evidence mismatch")
    if not isinstance(finding["bureauAdmissible"], bool):
        raise MaintenanceReportError("finding.bureauAdmissible must be boolean")


def _validate_candidate(candidate: Any) -> None:
    fields = {"id", "status", "evidence", "expiresAtOrRefreshHint", "nextAction", "responsibleOrgan"}
    if not isinstance(candidate, dict) or set(candidate) != fields:
        raise MaintenanceReportError("bureauCandidate fields mismatch")
    for field in ("id", "status", "expiresAtOrRefreshHint", "nextAction", "responsibleOrgan"):
        if not isinstance(candidate[field], str) or not candidate[field]:
            raise MaintenanceReportError(f"bureauCandidate.{field} must be a non-empty string")
    if not isinstance(candidate["evidence"], list) or not candidate["evidence"]:
        raise MaintenanceReportError("bureauCandidate.evidence must be non-empty")


def _validate_gap(gap: Any) -> None:
    fields = {"id", "topic", "missing", "neededFor", "severity"}
    if not isinstance(gap, dict) or set(gap) != fields:
        raise MaintenanceReportError("epistemicGap fields mismatch")
    for field in ("id", "topic", "missing", "neededFor"):
        if not isinstance(gap[field], str) or not gap[field]:
            raise MaintenanceReportError(f"epistemicGap.{field} must be a non-empty string")
    if gap["severity"] not in SEVERITIES:
        raise MaintenanceReportError("epistemicGap.severity mismatch")


def write_report(repo_root: Path, output: Path, *, external_dump_registry: str = EXTERNAL_DUMP_REGISTRY) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = _repo_path(repo_root, output, "output")
    report = build_report(repo_root, external_dump_registry=external_dump_registry)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="report output path")
    parser.add_argument("--external-dump-registry", default=EXTERNAL_DUMP_REGISTRY, help="optional external dump source registry path")
    parser.add_argument("--today", help="override scan date as YYYY-MM-DD")
    parser.add_argument("--check", action="store_true", help="validate report contract without writing")
    parser.add_argument("--strict", action="store_true", help="return non-zero when report summary status is fail")
    parser.add_argument("--json", action="store_true", help="emit machine-readable status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    scan_date = _parse_date(args.today, "today") if args.today else None
    try:
        if args.check:
            report = build_report(repo_root, scan_date=scan_date, external_dump_registry=args.external_dump_registry)
            action = "check"
        else:
            report = write_report(repo_root, Path(args.output), external_dump_registry=args.external_dump_registry)
            action = "write"
    except MaintenanceReportError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"write_cabinet_maintenance_report: {exc}", file=sys.stderr)
        return 1

    payload = {
        "ok": True,
        "action": action,
        "kind": report["kind"],
        "status": report["summary"]["status"],
        "findingCount": report["summary"]["findingCount"],
        "epistemicGapCount": report["summary"]["epistemicGapCount"],
        "bureauCandidateCount": report["summary"]["bureauCandidateCount"],
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            "cabinet-maintenance-report: "
            f"{action} ok status={payload['status']} "
            f"findings={payload['findingCount']} "
            f"gaps={payload['epistemicGapCount']} "
            f"bureau_candidates={payload['bureauCandidateCount']}"
        )
    if args.strict and report["summary"]["status"] == "fail":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
