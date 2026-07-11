#!/usr/bin/env python3
"""Project one private Cabinet runtime inventory into a redacted T013 snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/migration/cabinet-runtime-retirement-preflight-v1.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID = "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013"
DEPENDENCY_IDS = ("T004", "T007", "T012", "T018")


class PreflightProjectionError(ValueError):
    """Raised when private evidence cannot be projected safely."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreflightProjectionError(f"private evidence missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PreflightProjectionError(
            f"private evidence invalid JSON: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise PreflightProjectionError("private evidence must be an object")
    return value


def _expect_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreflightProjectionError(f"{label} must be an object")
    return value


def _expect_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise PreflightProjectionError(f"{label} must be boolean")
    return value


def _expect_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PreflightProjectionError(f"{label} must be a non-negative integer")
    return value


def _tree_summary(trees: dict[str, Any], role: str) -> dict[str, int | bool]:
    tree = _expect_dict(trees.get(role), f"runtime.trees.{role}")
    return {
        "exists": _expect_bool(tree.get("exists"), f"runtime.trees.{role}.exists"),
        "regularFiles": _expect_int(
            tree.get("regular_files"), f"runtime.trees.{role}.regular_files"
        ),
        "directories": _expect_int(
            tree.get("directories"), f"runtime.trees.{role}.directories"
        ),
        "symlinks": _expect_int(tree.get("symlinks"), f"runtime.trees.{role}.symlinks"),
        "bytes": _expect_int(tree.get("bytes"), f"runtime.trees.{role}.bytes"),
    }


def _dependency_projection(dependencies: dict[str, Any]) -> dict[str, Any]:
    if set(dependencies) != set(DEPENDENCY_IDS):
        raise PreflightProjectionError(
            "private dependencies must be exactly T004/T007/T012/T018"
        )
    output: dict[str, Any] = {}
    for task_id in DEPENDENCY_IDS:
        item = _expect_dict(dependencies[task_id], f"dependencies.{task_id}")
        if item.get("state") != "verified":
            raise PreflightProjectionError(f"dependency {task_id} is not verified")
        projected: dict[str, Any] = {"verified": True}
        for key in (
            "merge_commit",
            "public_snapshot_sha256",
            "private_evidence_sha256",
            "receipt_sha256",
        ):
            value = item.get(key)
            if value is None:
                continue
            if key == "merge_commit":
                if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
                    raise PreflightProjectionError(
                        f"dependency {task_id}.{key} invalid"
                    )
            elif not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                raise PreflightProjectionError(f"dependency {task_id}.{key} invalid")
            projected[
                {
                    "merge_commit": "mergeCommit",
                    "public_snapshot_sha256": "publicSnapshotSha256",
                    "private_evidence_sha256": "privateEvidenceSha256",
                    "receipt_sha256": "receiptSha256",
                }[key]
            ] = value
        output[task_id] = projected
    return output


def build_public_snapshot(private_path: Path) -> dict[str, Any]:
    private_bytes = private_path.read_bytes()
    private = _load(private_path)
    if private.get("schema_version") != 1:
        raise PreflightProjectionError("private evidence schema_version must be 1")
    if private.get("kind") != "cabinet_runtime_retirement_private_preflight":
        raise PreflightProjectionError("private evidence kind mismatch")
    if private.get("task_id") != TASK_ID:
        raise PreflightProjectionError("private evidence task mismatch")

    repository = _expect_dict(private.get("repository"), "repository")
    source_commit = repository.get("head")
    if not isinstance(source_commit, str) or not COMMIT_RE.fullmatch(source_commit):
        raise PreflightProjectionError("repository head must be a full commit id")
    if repository.get("clean") is not True:
        raise PreflightProjectionError("private evidence repository must be clean")

    effect = _expect_dict(private.get("effect_boundary"), "effect_boundary")
    expected_effect_keys = {
        "service_mutation_performed",
        "runtime_mutation_performed",
        "private_data_mutation_performed",
        "backup_or_restore_performed",
        "retention_change_performed",
        "repository_rename_performed",
        "effect_authorized",
    }
    if set(effect) != expected_effect_keys or any(effect.values()):
        raise PreflightProjectionError(
            "private evidence must prove a no-effect, unauthorized preflight"
        )

    service = _expect_dict(private.get("service"), "service")
    properties = _expect_dict(service.get("properties"), "service.properties")
    runtime = _expect_dict(private.get("runtime"), "runtime")
    processes = runtime.get("processes")
    listeners = runtime.get("listeners")
    if not isinstance(processes, list) or not processes:
        raise PreflightProjectionError("runtime.processes must be a non-empty list")
    if not isinstance(listeners, list) or not listeners:
        raise PreflightProjectionError("runtime.listeners must be a non-empty list")
    if any(
        not isinstance(item, dict) or item.get("address") != "127.0.0.1"
        for item in listeners
    ):
        raise PreflightProjectionError("all observed listeners must be loopback-only")

    trees = _expect_dict(runtime.get("trees"), "runtime.trees")
    audit = _expect_dict(
        private.get("existing_runtime_audit"), "existing_runtime_audit"
    )
    audit_returncode = _expect_int(
        audit.get("returncode"), "existing_runtime_audit.returncode"
    )
    if audit_returncode == 0:
        failure_class = "none"
    elif "driftet" in str(audit.get("first_stop_reason", "")).lower():
        failure_class = "local_wrapper_drift"
    else:
        failure_class = "legacy_audit_failure"

    log = _expect_dict(runtime.get("private_log"), "runtime.private_log")
    residual = private.get("residual_uncertainty")
    if not isinstance(residual, list) or not all(
        isinstance(item, str) and item for item in residual
    ):
        raise PreflightProjectionError(
            "residual_uncertainty must be a non-empty string list"
        )

    return {
        "schemaVersion": 1,
        "kind": "cabinet_runtime_retirement_preflight",
        "task": TASK_ID,
        "catalogAuthoritative": False,
        "snapshotRole": "dated_decision_evidence_not_live_status",
        "observedAt": private.get("observed_at"),
        "sourceCommit": source_commit,
        "privateEvidenceSha256": hashlib.sha256(private_bytes).hexdigest(),
        "dependencies": _dependency_projection(
            _expect_dict(private.get("dependencies"), "dependencies")
        ),
        "runtimeObservation": {
            "serviceLoadedAtObservation": properties.get("LoadState") == "loaded",
            "serviceActiveAtObservation": properties.get("ActiveState") == "active",
            "serviceEnabledAtObservation": properties.get("UnitFileState") == "enabled",
            "restartCount": int(properties.get("NRestarts", "0")),
            "processCount": len(processes),
            "listenerCount": len(listeners),
            "listenerExposure": "loopback_only",
            "observedRuntimeVersion": runtime.get("observed_version"),
            "repositoryRuntimeContractVersion": runtime.get(
                "repository_contract_version"
            ),
            "footprints": {
                "externalApp": _tree_summary(trees, "app_runtime"),
                "cliDistribution": _tree_summary(trees, "cli_distribution"),
                "privateStateExcludingEvidence": _tree_summary(trees, "state"),
                "privateConfig": _tree_summary(trees, "config"),
            },
            "privateLogSummary": {
                "exists": _expect_bool(log.get("exists"), "runtime.private_log.exists"),
                "bytes": _expect_int(log.get("bytes"), "runtime.private_log.bytes"),
                "startMarkers": _expect_int(
                    log.get("start_markers"), "runtime.private_log.start_markers"
                ),
                "stopMarkers": _expect_int(
                    log.get("stop_markers"), "runtime.private_log.stop_markers"
                ),
                "errorWordLines": _expect_int(
                    log.get("error_word_lines"), "runtime.private_log.error_word_lines"
                ),
            },
        },
        "contractDrift": {
            "detected": runtime.get("observed_version")
            != runtime.get("repository_contract_version"),
            "existingAuditPassed": audit_returncode == 0,
            "firstFailureClass": failure_class,
            "repairRecommendation": "do_not_rebase_catalog_on_external_runtime; use_retirement_preflight",
        },
        "decision": {
            "readOnlyPreflightComplete": True,
            "runtimeEffectAuthorized": False,
            "repositoryRenameAuthorized": False,
            "recommendation": "controlled_reversible_retirement_after_explicit_authorization",
            "nextAllowedWithoutNewAuthorization": [
                "refresh_read_only_inventory",
                "maintain_rollback_plan",
                "prepare_authorization_packet",
            ],
            "requiresExplicitAuthorization": [
                "bounded_service_stop_test",
                "service_disablement",
                "runtime_file_quarantine_or_removal",
                "versioned_runtime_surface_removal",
                "repository_rename",
            ],
        },
        "rollbackPlan": {
            "phaseA": {
                "action": "bounded_service_stop_test",
                "executed": False,
                "rollback": "restart_service_and_verify_loopback_runtime",
            },
            "phaseB": {
                "action": "disable_service_but_retain_all_files",
                "executed": False,
                "rollback": "enable_and_restart_service",
            },
            "phaseC": {
                "action": "remove_versioned_runtime_surfaces_in_reviewed_pr",
                "executed": False,
                "rollback": "revert_repository_change",
            },
            "phaseD": {
                "action": "quarantine_external_app_binaries_after_retention_decision",
                "executed": False,
                "rollback": "restore_quarantined_paths",
            },
            "alwaysPreserve": [
                "private_configuration_until_separate_classification",
                "private_state_until_separate_classification",
                "verified_export_and_restore_receipts",
            ],
        },
        "residualUncertainty": residual,
        "doesNotEstablish": [
            "safe_immediate_shutdown",
            "current_human_non_use",
            "remote_consumer_absence",
            "runtime_removal_permission",
            "private_data_deletion_permission",
            "backup_or_retention_change_permission",
            "repository_rename_permission",
        ],
    }


def render(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        text = render(build_public_snapshot(args.private_evidence))
        output = args.output.expanduser().resolve()
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != text:
                print(
                    f"runtime retirement preflight is stale: {output}", file=sys.stderr
                )
                return 1
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
        print(
            json.dumps(
                {
                    "kind": "cabinet_runtime_retirement_preflight",
                    "action": "check" if args.check else "write",
                    "output": str(output),
                    "privateEvidenceSha256": hashlib.sha256(
                        args.private_evidence.read_bytes()
                    ).hexdigest(),
                    "ok": True,
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, PreflightProjectionError, ValueError) as exc:
        print(f"runtime retirement preflight: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
