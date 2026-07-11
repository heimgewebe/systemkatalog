#!/usr/bin/env python3
"""Write or validate Cabinet's curated Gemini maintenance evidence packet."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from write_cabinet_maintenance_report import MaintenanceReportError, build_report

KIND = "cabinet_gemini_maintenance_evidence_packet"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-gemini-maintenance-evidence-packet-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-gemini-maintenance-evidence-packet-v1.schema.json"
GENERATOR_PATH = "scripts/write_gemini_maintenance_evidence_packet.py"
DEFAULT_OUTPUT = Path("pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json")
MAINTENANCE_REPORT_REF = "evidence:generated:maintenance-report"
MAINTENANCE_REPORT_PATH = "generated/cabinet-maintenance-report.json"

CURATED_INPUTS: tuple[tuple[str, str, str], ...] = (
    ("AGENTS.md", "agent_rules", "text/markdown"),
    ("README.md", "repository_overview", "text/markdown"),
    ("docs/blueprints/cabinet-maintenance-radar-v0.md", "maintenance_radar_policy", "text/markdown"),
    ("docs/blueprints/agent-routing-brief-v0.md", "agent_routing_policy", "text/markdown"),
    ("docs/contracts/cabinet-frontier-v1.md", "frontier_no_effect_contract", "text/markdown"),
    ("docs/contracts/cabinet-gemini-maintenance-scan-v1.md", "gemini_scan_output_contract", "text/markdown"),
    ("registry/ecosystem/nodes.json", "ecosystem_nodes", "application/json"),
    ("registry/ecosystem/edges.json", "ecosystem_edges", "application/json"),
    ("registry/ecosystem/claims.jsonl", "ecosystem_claims", "application/jsonl"),
    ("registry/ecosystem/external-dump-sources.json", "external_dump_sources", "application/json"),
)

EFFECT_FLAGS = (
    "issueCreationAllowed",
    "prCreationAllowed",
    "commentCreationAllowed",
    "taskCreationAllowed",
    "queueMutationAllowed",
    "grabowskiDispatchAllowed",
    "pushOrMergeAllowed",
    "runtimeMutationAllowed",
    "secretRequestAllowed",
    "dumpGenerationAllowed",
    "cleanupActionAllowed",
    "externalModelExecutionAllowed",
    "scheduleAllowed",
)

DOES_NOT_ESTABLISH = (
    "gemini_available",
    "gemini_schedulability",
    "dry_run_success",
    "scan_quality",
    "claim_truth",
    "task_approval",
    "bureau_import",
    "merge_readiness",
    "runtime_correctness",
    "secret_absence_outside_curated_inputs",
    "complete_repository_context",
    "autonomous_dispatch",
)

FORBIDDEN_PATH_PREFIXES = (
    ".git/",
    ".agents/",
    ".global-agents/",
    ".jobs/",
    ".cabinet-state/",
    ".conversations/",
    ".memory/",
    ".messages/",
    "logs/",
)
FORBIDDEN_FILE_NAMES = (".env", ".cabinet.env", ".cabinet.db", "daemon-token", "runtime.env")
FORBIDDEN_FILE_SUFFIXES = (".key", ".pem", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db", ".log")

_DASH = "-" * 5
_MARKER_PARTS = (
    ("PRIV", "ATE", "KEY"),
    ("RSA", "PRIV", "ATE", "KEY"),
    ("OPENS", "SH", "PRIV", "ATE", "KEY"),
    ("EC", "PRIV", "ATE", "KEY"),
)
KEY_BEGIN_MARKERS = tuple(_DASH + "BEGIN " + " ".join("".join(part for part in parts[:2]) if parts[:2] == ("PRIV", "ATE") else part for part in parts) + _DASH for parts in _MARKER_PARTS)
KEY_BEGIN_MARKERS = (
    _DASH + "BEGIN " + "PRIV" + "ATE " + "KEY" + _DASH,
    _DASH + "BEGIN RSA " + "PRIV" + "ATE " + "KEY" + _DASH,
    _DASH + "BEGIN OPENS" + "SH " + "PRIV" + "ATE " + "KEY" + _DASH,
    _DASH + "BEGIN EC " + "PRIV" + "ATE " + "KEY" + _DASH,
)

TOP_LEVEL_FIELDS = {
    "schemaVersion",
    "kind",
    "contractVersion",
    "contractPath",
    "schemaPath",
    "generator",
    "source",
    "inputPolicy",
    "summary",
    "maintenanceReport",
    "entries",
    "effectFlags",
    "exclusionReport",
    "doesNotEstablish",
}
ENTRY_FIELDS = {"ref", "path", "role", "mediaType", "sha256", "bytes", "lines", "content"}


class EvidencePacketError(RuntimeError):
    """Raised when an evidence packet cannot be built or validated."""


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _is_commit_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str, label: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidencePacketError(f"{label} must be an ISO timestamp") from exc
    if result.tzinfo is None:
        raise EvidencePacketError(f"{label} must include a timezone")
    return result


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
        raise EvidencePacketError("could not determine git source commit") from exc
    commit = result.stdout.strip()
    if not _is_commit_sha(commit):
        raise EvidencePacketError(f"invalid git source commit: {commit!r}")
    return commit


def _normalized_slash(path: str) -> str:
    return path.replace("\\", "/")


def _assert_path_not_forbidden(relative_path: str) -> None:
    normalized = _normalized_slash(relative_path).lstrip("/")
    lowered = normalized.lower()
    parts = tuple(part.lower() for part in normalized.split("/"))
    for prefix in FORBIDDEN_PATH_PREFIXES:
        if lowered == prefix.rstrip("/") or lowered.startswith(prefix):
            raise EvidencePacketError(f"forbidden curated input path: {relative_path}")
    if any(part in {name.lower() for name in FORBIDDEN_FILE_NAMES} for part in parts):
        raise EvidencePacketError(f"forbidden curated input file name: {relative_path}")
    if any(lowered.endswith(suffix) for suffix in FORBIDDEN_FILE_SUFFIXES):
        raise EvidencePacketError(f"forbidden curated input file suffix: {relative_path}")


def _assert_content_not_forbidden(content: str, relative_path: str) -> None:
    if any(marker in content for marker in KEY_BEGIN_MARKERS):
        raise EvidencePacketError(f"key marker found in curated input: {relative_path}")


def _repo_path(repo_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path or Path(relative_path).is_absolute():
        raise EvidencePacketError(f"invalid curated input path: {relative_path!r}")
    parts = Path(relative_path).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise EvidencePacketError(f"curated input path contains traversal: {relative_path}")
    _assert_path_not_forbidden(relative_path)
    current = repo_root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise EvidencePacketError(f"curated input path contains symlink component: {relative_path}")
    resolved = current.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise EvidencePacketError(f"curated input escapes repository: {relative_path}") from exc
    if not resolved.is_file():
        raise EvidencePacketError(f"missing curated input: {relative_path}")
    return resolved


def _line_count(content: str) -> int:
    return len(content.splitlines())


def _entry(ref: str, path: str, role: str, media_type: str, content: str) -> dict[str, Any]:
    if not path.startswith("generated/"):
        _assert_path_not_forbidden(path)
    _assert_content_not_forbidden(content, path)
    encoded = content.encode("utf-8")
    return {
        "ref": ref,
        "path": path,
        "role": role,
        "mediaType": media_type,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        "lines": _line_count(content),
        "content": content,
    }


def _source_entry(repo_root: Path, relative_path: str, role: str, media_type: str) -> dict[str, Any]:
    path = _repo_path(repo_root, relative_path)
    return _entry(f"evidence:{relative_path}", relative_path, role, media_type, path.read_text(encoding="utf-8"))


def _manifest_digest(entries: list[dict[str, Any]], maintenance_report: dict[str, Any]) -> str:
    return _sha256_json({
        "entries": [
            {key: entry[key] for key in ("ref", "path", "role", "sha256", "bytes", "lines")}
            for entry in entries
        ],
        "maintenanceReportSummary": maintenance_report.get("summary"),
    })


def build_packet(repo_root: Path, *, source_commit: str | None = None, generated_at: str | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    commit = source_commit or _git_commit(repo_root)
    if not _is_commit_sha(commit):
        raise EvidencePacketError("source_commit must be a 40 character lowercase git SHA")
    generated_at_value = generated_at or _generated_at()
    generated_time = _parse_timestamp(generated_at_value, "generatedAt")

    entries = [_source_entry(repo_root, path, role, media_type) for path, role, media_type in CURATED_INPUTS]
    try:
        report = build_report(
            repo_root,
            source_commit=commit,
            generated_at=generated_at_value,
            scan_date=generated_time.astimezone(timezone.utc).date(),
        )
    except MaintenanceReportError as exc:
        raise EvidencePacketError(f"could not build maintenance report for packet: {exc}") from exc
    report_content = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    entries.append(_entry(MAINTENANCE_REPORT_REF, MAINTENANCE_REPORT_PATH, "generated_maintenance_report", "application/json", report_content))
    entries.sort(key=lambda item: item["ref"])

    source_file_entries = [entry for entry in entries if not entry["path"].startswith("generated/")]
    generated_entries = [entry for entry in entries if entry["path"].startswith("generated/")]
    packet = {
        "schemaVersion": 1,
        "kind": KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "generator": GENERATOR_PATH,
        "source": {
            "repository": "heimgewebe/heimgewebe-katalog",
            "commit": commit,
            "generatedAt": generated_at_value,
            "mode": "curated_allowlist_only",
        },
        "inputPolicy": {
            "mode": "curated_allowlist_only",
            "allowedRepoPaths": [path for path, _role, _media_type in CURATED_INPUTS],
            "generatedRefs": [MAINTENANCE_REPORT_REF],
            "forbiddenPathPrefixes": list(FORBIDDEN_PATH_PREFIXES),
            "forbiddenFileNames": list(FORBIDDEN_FILE_NAMES),
            "forbiddenFileSuffixes": list(FORBIDDEN_FILE_SUFFIXES),
            "fullRepositoryCrawlAllowed": False,
        },
        "summary": {
            "entryCount": len(entries),
            "sourceFileCount": len(source_file_entries),
            "generatedEntryCount": len(generated_entries),
            "totalBytes": sum(entry["bytes"] for entry in entries),
            "manifestSha256": _manifest_digest(entries, report),
            "maintenanceReportStatus": report["summary"]["status"],
            "maintenanceReportFindingCount": report["summary"]["findingCount"],
        },
        "maintenanceReport": {
            "ref": MAINTENANCE_REPORT_REF,
            "path": MAINTENANCE_REPORT_PATH,
            "kind": report["kind"],
            "sha256": _sha256_text(report_content),
            "summary": report["summary"],
        },
        "entries": entries,
        "effectFlags": {flag: False for flag in EFFECT_FLAGS},
        "exclusionReport": {
            "forbiddenPathHits": [],
            "privateKeyMarkerHits": [],
            "fullRepositoryCrawlUsed": False,
            "runtimeConfigIncluded": False,
            "privateLogsIncluded": False,
            "agentRuntimeIncluded": False,
        },
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    if not isinstance(packet, dict) or set(packet) != TOP_LEVEL_FIELDS:
        raise EvidencePacketError("packet top-level fields mismatch")
    if packet["schemaVersion"] != 1 or packet["kind"] != KIND:
        raise EvidencePacketError("packet identity mismatch")
    if packet["contractVersion"] != CONTRACT_VERSION or packet["contractPath"] != CONTRACT_PATH or packet["schemaPath"] != SCHEMA_PATH:
        raise EvidencePacketError("packet contract mismatch")
    if packet["generator"] != GENERATOR_PATH:
        raise EvidencePacketError("packet generator mismatch")

    source = _object(packet["source"], "source")
    if set(source) != {"repository", "commit", "generatedAt", "mode"}:
        raise EvidencePacketError("source fields mismatch")
    if source["repository"] != "heimgewebe/heimgewebe-katalog" or not _is_commit_sha(source["commit"]):
        raise EvidencePacketError("source repository or commit mismatch")
    _parse_timestamp(_string(source["generatedAt"], "source.generatedAt"), "source.generatedAt")
    if source["mode"] != "curated_allowlist_only":
        raise EvidencePacketError("source mode mismatch")

    policy = _object(packet["inputPolicy"], "inputPolicy")
    expected_paths = [path for path, _role, _media_type in CURATED_INPUTS]
    if policy.get("mode") != "curated_allowlist_only" or policy.get("allowedRepoPaths") != expected_paths:
        raise EvidencePacketError("inputPolicy allowed inputs mismatch")
    if policy.get("generatedRefs") != [MAINTENANCE_REPORT_REF] or policy.get("fullRepositoryCrawlAllowed") is not False:
        raise EvidencePacketError("inputPolicy generated/full-crawl mismatch")
    if policy.get("forbiddenPathPrefixes") != list(FORBIDDEN_PATH_PREFIXES):
        raise EvidencePacketError("inputPolicy forbiddenPathPrefixes mismatch")
    if policy.get("forbiddenFileNames") != list(FORBIDDEN_FILE_NAMES):
        raise EvidencePacketError("inputPolicy forbiddenFileNames mismatch")
    if policy.get("forbiddenFileSuffixes") != list(FORBIDDEN_FILE_SUFFIXES):
        raise EvidencePacketError("inputPolicy forbiddenFileSuffixes mismatch")

    entries = packet["entries"]
    if not isinstance(entries, list) or len(entries) != len(CURATED_INPUTS) + 1:
        raise EvidencePacketError("entries length mismatch")
    expected_by_ref = {f"evidence:{path}": (path, role, media_type) for path, role, media_type in CURATED_INPUTS}
    expected_by_ref[MAINTENANCE_REPORT_REF] = (MAINTENANCE_REPORT_PATH, "generated_maintenance_report", "application/json")
    refs = [entry.get("ref") if isinstance(entry, dict) else None for entry in entries]
    if set(refs) != set(expected_by_ref) or len(refs) != len(set(refs)):
        raise EvidencePacketError("entry refs mismatch")
    for entry in entries:
        _validate_entry(entry)
        expected = expected_by_ref[entry["ref"]]
        if (entry["path"], entry["role"], entry["mediaType"]) != expected:
            raise EvidencePacketError(f"entry binding mismatch: {entry['ref']}")

    report_entry = next(entry for entry in entries if entry["ref"] == MAINTENANCE_REPORT_REF)
    report_meta = _object(packet["maintenanceReport"], "maintenanceReport")
    if report_meta.get("ref") != MAINTENANCE_REPORT_REF or report_meta.get("path") != MAINTENANCE_REPORT_PATH:
        raise EvidencePacketError("maintenanceReport ref/path mismatch")
    if report_meta.get("sha256") != report_entry["sha256"]:
        raise EvidencePacketError("maintenanceReport sha mismatch")
    try:
        report_payload = json.loads(report_entry["content"])
    except json.JSONDecodeError as exc:
        raise EvidencePacketError("maintenance report entry must contain JSON") from exc
    if report_meta.get("kind") != "cabinet_maintenance_report" or report_payload.get("kind") != report_meta.get("kind"):
        raise EvidencePacketError("maintenanceReport kind mismatch")
    if report_meta.get("summary") != report_payload.get("summary"):
        raise EvidencePacketError("maintenanceReport summary mismatch")

    summary = _object(packet["summary"], "summary")
    source_entries = [entry for entry in entries if not entry["path"].startswith("generated/")]
    generated_entries = [entry for entry in entries if entry["path"].startswith("generated/")]
    expected_summary = {
        "entryCount": len(entries),
        "sourceFileCount": len(source_entries),
        "generatedEntryCount": len(generated_entries),
        "totalBytes": sum(entry["bytes"] for entry in entries),
        "manifestSha256": _manifest_digest(entries, report_payload),
        "maintenanceReportStatus": report_payload["summary"]["status"],
        "maintenanceReportFindingCount": report_payload["summary"]["findingCount"],
    }
    if summary != expected_summary:
        raise EvidencePacketError("summary does not match packet contents")

    flags = _object(packet["effectFlags"], "effectFlags")
    if set(flags) != set(EFFECT_FLAGS) or any(flags[flag] is not False for flag in EFFECT_FLAGS):
        raise EvidencePacketError("all effectFlags must exist and be false")
    expected_exclusion = {
        "forbiddenPathHits": [],
        "privateKeyMarkerHits": [],
        "fullRepositoryCrawlUsed": False,
        "runtimeConfigIncluded": False,
        "privateLogsIncluded": False,
        "agentRuntimeIncluded": False,
    }
    if packet["exclusionReport"] != expected_exclusion:
        raise EvidencePacketError("exclusionReport must be clean and effect-free")
    non_claims = packet["doesNotEstablish"]
    if not isinstance(non_claims, list) or set(non_claims) != set(DOES_NOT_ESTABLISH) or len(non_claims) != len(DOES_NOT_ESTABLISH):
        raise EvidencePacketError("doesNotEstablish mismatch")


def _validate_entry(entry: Any) -> None:
    if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
        raise EvidencePacketError("entry fields mismatch")
    for field in ("ref", "path", "role", "mediaType", "content"):
        _string(entry[field], f"entry.{field}")
    if not entry["path"].startswith("generated/"):
        _assert_path_not_forbidden(entry["path"])
    _assert_content_not_forbidden(entry["content"], entry["path"])
    encoded = entry["content"].encode("utf-8")
    if entry["sha256"] != hashlib.sha256(encoded).hexdigest():
        raise EvidencePacketError(f"entry sha mismatch: {entry['ref']}")
    if entry["bytes"] != len(encoded):
        raise EvidencePacketError(f"entry byte count mismatch: {entry['ref']}")
    if entry["lines"] != _line_count(entry["content"]):
        raise EvidencePacketError(f"entry line count mismatch: {entry['ref']}")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidencePacketError(f"{label} must be an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidencePacketError(f"{label} must be a non-empty string")
    return value


def _write_packet(repo_root: Path, output: Path, packet: dict[str, Any]) -> None:
    repo_root = repo_root.resolve()
    target = output if output.is_absolute() else repo_root / output
    try:
        target.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise EvidencePacketError(f"output escapes repository: {output}") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_packet(repo_root: Path, output: Path) -> dict[str, Any]:
    packet = build_packet(repo_root.resolve())
    _write_packet(repo_root, output, packet)
    return packet


def load_packet(path: Path) -> dict[str, Any]:
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidencePacketError(f"missing packet: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidencePacketError(f"invalid packet JSON: {exc}") from exc
    if not isinstance(packet, dict):
        raise EvidencePacketError("packet must be a JSON object")
    validate_packet(packet)
    return packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Git repository root")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="packet output path")
    parser.add_argument("--generated-at", help="override packet timestamp as RFC3339/ISO timestamp")
    parser.add_argument("--source-commit", help="override source commit for deterministic tests")
    parser.add_argument("--check", action="store_true", help="validate packet contract without writing")
    parser.add_argument("--validate", type=Path, help="validate an existing packet JSON file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.validate:
            packet = load_packet(args.validate)
            action = "validate"
        else:
            repo_root = Path(args.repo_root).resolve()
            if args.check:
                packet = build_packet(repo_root, source_commit=args.source_commit, generated_at=args.generated_at)
                action = "check"
            else:
                packet = build_packet(repo_root, source_commit=args.source_commit, generated_at=args.generated_at)
                _write_packet(repo_root, Path(args.output), packet)
                action = "write"
    except EvidencePacketError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"write_gemini_maintenance_evidence_packet: {exc}", file=sys.stderr)
        return 1

    payload = {
        "ok": True,
        "action": action,
        "kind": packet["kind"],
        "entryCount": packet["summary"]["entryCount"],
        "sourceFileCount": packet["summary"]["sourceFileCount"],
        "generatedEntryCount": packet["summary"]["generatedEntryCount"],
        "maintenanceReportStatus": packet["summary"]["maintenanceReportStatus"],
        "manifestSha256": packet["summary"]["manifestSha256"],
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            "gemini-maintenance-evidence-packet: "
            f"{action} ok entries={payload['entryCount']} "
            f"source_files={payload['sourceFileCount']} "
            f"generated={payload['generatedEntryCount']} "
            f"status={payload['maintenanceReportStatus']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
