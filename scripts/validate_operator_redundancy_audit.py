#!/usr/bin/env python3
"""Strict dependency-free validator for the operator redundancy audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "registry/ecosystem/operator-redundancy-audit.v1.json"
REQUIRED_ORGANS = {
    "bureau",
    "grabowski",
    "repobrief_lenskit",
    "cabinet",
    "steuerboard",
    "leitstand",
    "schauwerk",
    "chronik",
    "heimlern",
    "vibe_lab",
    "wgx",
    "github_ci_runtime",
}
REQUIRED_NON_CLAIMS = {
    "safe_immediate_shutdown",
    "complete_remote_runtime_inventory",
    "consumer_semantic_correctness",
    "automatic_task_approval",
    "merge_readiness",
    "runtime_health",
}


class AuditError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def strings(value: Any, path: str, *, nonempty: bool = True) -> list[str]:
    require(isinstance(value, list), f"{path} must be an array")
    require(all(isinstance(item, str) and item for item in value), f"{path} must contain non-empty strings")
    if nonempty:
        require(bool(value), f"{path} must not be empty")
    return value


def validate(payload: dict[str, Any]) -> None:
    require(payload.get("schemaVersion") == 1, "schemaVersion must be 1")
    require(payload.get("kind") == "operator_ecosystem_redundancy_audit", "unexpected kind")
    require(isinstance(payload.get("observedAt"), str) and payload["observedAt"], "observedAt missing")
    require(isinstance(payload.get("scope"), dict), "scope must be an object")
    require(isinstance(payload.get("summary"), dict), "summary must be an object")

    evidence_refs = payload.get("evidenceRefs")
    require(isinstance(evidence_refs, list) and evidence_refs, "evidenceRefs must be a non-empty array")
    evidence_ids: set[str] = set()
    for index, evidence in enumerate(evidence_refs):
        path = f"evidenceRefs[{index}]"
        require(isinstance(evidence, dict), f"{path} must be an object")
        evidence_id = evidence.get("id")
        require(isinstance(evidence_id, str) and evidence_id, f"{path}.id missing")
        require(evidence_id not in evidence_ids, f"duplicate evidence id: {evidence_id}")
        evidence_ids.add(evidence_id)
        for field in ("kind", "reference", "observedAt"):
            require(isinstance(evidence.get(field), str) and evidence[field], f"{path}.{field} missing")

    organs = payload.get("organs")
    require(isinstance(organs, list) and organs, "organs must be a non-empty array")
    seen: set[str] = set()
    for index, organ in enumerate(organs):
        path = f"organs[{index}]"
        require(isinstance(organ, dict), f"{path} must be an object")
        organ_id = organ.get("id")
        require(isinstance(organ_id, str) and organ_id, f"{path}.id missing")
        require(organ_id not in seen, f"duplicate organ id: {organ_id}")
        seen.add(organ_id)
        for field in ("authority", "recommendation"):
            require(isinstance(organ.get(field), str) and organ[field], f"{path}.{field} missing")
        strings(organ.get("observedConsumers"), f"{path}.observedConsumers")
        strings(organ.get("duplicateData"), f"{path}.duplicateData")
        strings(organ.get("evidenceClass"), f"{path}.evidenceClass")
        confidence = organ.get("confidence")
        require(isinstance(confidence, (int, float)) and 0 <= confidence <= 1, f"{path}.confidence outside 0..1")
        maintenance = organ.get("manualMaintenance")
        require(isinstance(maintenance, dict), f"{path}.manualMaintenance must be an object")
        require(isinstance(maintenance.get("level"), str) and maintenance["level"], f"{path}.manualMaintenance.level missing")
        strings(maintenance.get("drivers"), f"{path}.manualMaintenance.drivers")
        shutdown = organ.get("shutdown")
        require(isinstance(shutdown, dict), f"{path}.shutdown must be an object")
        require(isinstance(shutdown.get("class"), str) and shutdown["class"], f"{path}.shutdown.class missing")
        strings(shutdown.get("conditions"), f"{path}.shutdown.conditions")
        require(isinstance(shutdown.get("partialShutdown"), str) and shutdown["partialShutdown"], f"{path}.shutdown.partialShutdown missing")

    require(seen == REQUIRED_ORGANS, f"organ set mismatch: missing={sorted(REQUIRED_ORGANS-seen)} unexpected={sorted(seen-REQUIRED_ORGANS)}")

    actions = payload.get("actions")
    require(isinstance(actions, list) and actions, "actions must be a non-empty array")
    action_ids: set[str] = set()
    for index, action in enumerate(actions):
        path = f"actions[{index}]"
        require(isinstance(action, dict), f"{path} must be an object")
        require(action.get("priority") in {"P0", "P1", "P2", "P3"}, f"{path}.priority invalid")
        action_id = action.get("id")
        require(isinstance(action_id, str) and action_id, f"{path}.id missing")
        require(action_id not in action_ids, f"duplicate action id: {action_id}")
        action_ids.add(action_id)
        require(isinstance(action.get("owner"), str) and action["owner"], f"{path}.owner missing")
        require(isinstance(action.get("decision"), str) and action["decision"], f"{path}.decision missing")

    non_claims = set(strings(payload.get("doesNotEstablish"), "doesNotEstablish"))
    require(non_claims == REQUIRED_NON_CLAIMS, "doesNotEstablish must contain the fixed non-claims")

    signals = payload["summary"].get("liveSignals")
    require(isinstance(signals, dict), "summary.liveSignals must be an object")
    require(signals.get("bureauActiveTimers", 0) >= 1, "bureau timer observation missing")
    require(signals.get("grabowskiWorktrees", 0) >= 1, "Grabowski worktree observation missing")
    require(signals.get("grabowskiFailedTransientUnits", 0) >= 1, "Grabowski failed-unit observation missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "audit root must be an object")
        validate(payload)
    except (OSError, json.JSONDecodeError, AuditError) as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"INVALID: {exc}")
        return 1
    result = {"status": "valid", "organCount": len(payload["organs"]), "actionCount": len(payload["actions"])}
    print(json.dumps(result, ensure_ascii=False) if args.json else f"VALID: organs={result['organCount']} actions={result['actionCount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
