#!/usr/bin/env python3
"""Validate the redacted Cabinet T013 runtime-retirement preflight."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs/migration/cabinet-runtime-retirement-preflight-v1.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
PRIVATE_STRING_PATTERNS = (
    re.compile(r"/home/", re.I),
    re.compile(r"~\./|~/", re.I),
    re.compile(r"127\.0\.0\.1(?::\d+)?"),
    re.compile(
        r"(?:password|passwd|api[_-]?key|access[_-]?token|private[_-]?key)\s*[:=]", re.I
    ),
)
FORBIDDEN_KEYS = {
    "path",
    "port",
    "pid",
    "ppid",
    "argv",
    "mainpid",
    "fragmentpath",
    "dropinpaths",
    "environmentfiles",
    "keyfiles",
    "enabledlink",
}


class PreflightValidationError(ValueError):
    """Raised when the public preflight violates its contract."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreflightValidationError(f"preflight missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PreflightValidationError(f"preflight invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PreflightValidationError("preflight must be an object")
    return value


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def validate(path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    doc = _load(path)
    expected_top = {
        "schemaVersion",
        "kind",
        "task",
        "catalogAuthoritative",
        "snapshotRole",
        "observedAt",
        "sourceCommit",
        "privateEvidenceSha256",
        "dependencies",
        "runtimeObservation",
        "contractDrift",
        "decision",
        "rollbackPlan",
        "residualUncertainty",
        "doesNotEstablish",
    }
    if set(doc) != expected_top:
        raise PreflightValidationError("preflight top-level fields mismatch")
    if (
        doc["schemaVersion"] != 1
        or doc["kind"] != "cabinet_runtime_retirement_preflight"
    ):
        raise PreflightValidationError("preflight identity mismatch")
    if doc["task"] != "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013":
        raise PreflightValidationError("preflight task mismatch")
    if doc["catalogAuthoritative"] is not False:
        raise PreflightValidationError("preflight must remain non-authoritative")
    if doc["snapshotRole"] != "dated_decision_evidence_not_live_status":
        raise PreflightValidationError("preflight snapshot role mismatch")
    if not isinstance(doc["observedAt"], str) or not doc["observedAt"].endswith("Z"):
        raise PreflightValidationError("observedAt must be an explicit UTC timestamp")
    if not isinstance(doc["sourceCommit"], str) or not COMMIT_RE.fullmatch(
        doc["sourceCommit"]
    ):
        raise PreflightValidationError("sourceCommit invalid")
    if not isinstance(doc["privateEvidenceSha256"], str) or not SHA256_RE.fullmatch(
        doc["privateEvidenceSha256"]
    ):
        raise PreflightValidationError("privateEvidenceSha256 invalid")

    dependencies = doc["dependencies"]
    if not isinstance(dependencies, dict) or set(dependencies) != {
        "T004",
        "T007",
        "T012",
        "T018",
    }:
        raise PreflightValidationError("dependency set mismatch")
    for task_id, item in dependencies.items():
        if not isinstance(item, dict) or item.get("verified") is not True:
            raise PreflightValidationError(f"dependency {task_id} is not verified")

    observation = doc["runtimeObservation"]
    if not isinstance(observation, dict):
        raise PreflightValidationError("runtimeObservation must be an object")
    for key in ("processCount", "listenerCount", "restartCount"):
        if not isinstance(observation.get(key), int) or observation[key] < 0:
            raise PreflightValidationError(f"runtimeObservation.{key} invalid")
    if observation["listenerExposure"] != "loopback_only":
        raise PreflightValidationError("listener exposure must remain loopback-only")
    if (
        observation["observedRuntimeVersion"]
        == observation["repositoryRuntimeContractVersion"]
    ):
        raise PreflightValidationError(
            "preflight must preserve the observed runtime contract drift"
        )

    drift = doc["contractDrift"]
    if drift != {
        "detected": True,
        "existingAuditPassed": False,
        "firstFailureClass": "local_wrapper_drift",
        "repairRecommendation": "do_not_rebase_catalog_on_external_runtime; use_retirement_preflight",
    }:
        raise PreflightValidationError("contractDrift record mismatch")

    decision = doc["decision"]
    if decision.get("readOnlyPreflightComplete") is not True:
        raise PreflightValidationError("read-only preflight completion missing")
    if decision.get("runtimeEffectAuthorized") is not False:
        raise PreflightValidationError("runtime effect must remain unauthorized")
    if decision.get("repositoryRenameAuthorized") is not False:
        raise PreflightValidationError("repository rename must remain unauthorized")
    required_effects = {
        "bounded_service_stop_test",
        "service_disablement",
        "runtime_file_quarantine_or_removal",
        "versioned_runtime_surface_removal",
        "repository_rename",
    }
    if set(decision.get("requiresExplicitAuthorization", [])) != required_effects:
        raise PreflightValidationError("explicit authorization set mismatch")

    rollback = doc["rollbackPlan"]
    if not isinstance(rollback, dict):
        raise PreflightValidationError("rollbackPlan must be an object")
    for phase in ("phaseA", "phaseB", "phaseC", "phaseD"):
        item = rollback.get(phase)
        if not isinstance(item, dict) or item.get("executed") is not False:
            raise PreflightValidationError(
                f"rollback phase {phase} must remain unexecuted"
            )
        if not isinstance(item.get("rollback"), str) or not item["rollback"]:
            raise PreflightValidationError(f"rollback phase {phase} missing rollback")

    does_not = set(doc["doesNotEstablish"])
    required_nonclaims = {
        "safe_immediate_shutdown",
        "runtime_removal_permission",
        "private_data_deletion_permission",
        "backup_or_retention_change_permission",
        "repository_rename_permission",
    }
    if not required_nonclaims.issubset(does_not):
        raise PreflightValidationError("required non-claims missing")

    for key, value in _walk(doc):
        if re.sub(r"[^a-z0-9]", "", key.lower()) in FORBIDDEN_KEYS:
            raise PreflightValidationError(
                f"public preflight contains private-detail key: {key}"
            )
        if isinstance(value, str) and any(
            pattern.search(value) for pattern in PRIVATE_STRING_PATTERNS
        ):
            raise PreflightValidationError(
                "public preflight contains private runtime detail"
            )

    footprints = observation.get("footprints")
    if not isinstance(footprints, dict) or set(footprints) != {
        "externalApp",
        "cliDistribution",
        "privateStateExcludingEvidence",
        "privateConfig",
    }:
        raise PreflightValidationError("runtime footprint roles mismatch")

    return {
        "valid": True,
        "task": doc["task"],
        "processCount": observation["processCount"],
        "listenerCount": observation["listenerCount"],
        "runtimeEffectAuthorized": False,
        "repositoryRenameAuthorized": False,
        "contractDrift": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(args.input), sort_keys=True))
        return 0
    except (OSError, PreflightValidationError, ValueError) as exc:
        print(f"runtime retirement preflight: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
