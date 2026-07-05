#!/usr/bin/env python3
"""Validate the Cabinet Maintenance Radar policy.

The validator checks the versioned policy shape and its non-effects. It does
not prove that external repositories, CI, runtime or Heimlern are currently
healthy.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policy" / "cabinet-maintenance-radar.json"

REQUIRED_SCAN_CLASSES = {
    "consistency",
    "structural_error",
    "freshness",
    "authority_order",
    "handoff_readiness",
    "effect_closure",
    "external_artifact_surface",
    "learning_feedback",
}

REQUIRED_FINDING_FIELDS = {
    "id",
    "scan_id",
    "rule_id",
    "subject",
    "finding_type",
    "severity",
    "evidence",
    "confidence",
    "status",
    "responsible_organ",
    "next_action",
    "created_at",
}

REQUIRED_OUTCOME_FIELDS = {
    "finding_id",
    "outcome",
    "evidence",
    "closed_at",
    "reviewer",
    "learning_allowed",
}

REQUIRED_OUTPUTS = {
    "cabinet.scan_finding.v1",
    "cabinet.maintenance_report.v1",
    "cabinet.maintenance_outcome.v1",
    "cabinet.handoff_candidate.v1",
    "heimlern.policy_adjustment.proposed.v1",
}

REQUIRED_PROHIBITED_EFFECTS = {
    "repobrief_or_lenskit_dump_generation",
    "automatic_bureau_task_creation",
    "automatic_grabowski_delegation",
    "merge_or_push_action",
    "runtime_mutation",
    "cleanup_action",
    "authority_inference_from_map",
    "direct_policy_weight_application",
}

REQUIRED_NON_CLAIMS = {
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "bureau_import_implemented",
    "autonomous_dispatch",
    "policy_change_approval",
    "dump_freshness_truth",
}

REQUIRED_ORGAN_ROLES = {
    "cabinet",
    "bureau",
    "grabowski_operator",
    "repobrief_lenskit",
    "heimlern",
    "chronik",
    "github_ci_runtime",
    "external_agents",
}

REQUIRED_PRIMARY_SOURCE_KEYS = {
    "git_pr_review",
    "ci_signal",
    "runtime_signal",
    "contract_invariant",
    "priority_release_stop",
    "context_dump",
    "learning_feedback",
}


class MaintenanceRadarPolicyError(ValueError):
    """Raised when the Cabinet Maintenance Radar policy is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise MaintenanceRadarPolicyError(f"missing policy file: {path}") from None
    except json.JSONDecodeError as exc:
        raise MaintenanceRadarPolicyError(f"invalid JSON in policy: {exc}") from None
    if not isinstance(payload, dict):
        raise MaintenanceRadarPolicyError("policy must be a JSON object")
    return payload


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise MaintenanceRadarPolicyError(f"{label} must be a non-empty string")
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise MaintenanceRadarPolicyError(f"{label} must be boolean")
    return value


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MaintenanceRadarPolicyError(f"{label} must be an object")
    return value


def _require_string_set(value: Any, label: str) -> set[str]:
    if not isinstance(value, list):
        raise MaintenanceRadarPolicyError(f"{label} must be a list")
    result: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item:
            raise MaintenanceRadarPolicyError(f"{label} item {index} must be a non-empty string")
        result.add(item)
    if len(result) != len(value):
        raise MaintenanceRadarPolicyError(f"{label} must not contain duplicates")
    return result


def _require_subset(required: set[str], actual: set[str], label: str) -> None:
    missing = sorted(required - actual)
    if missing:
        raise MaintenanceRadarPolicyError(f"{label} missing: {', '.join(missing)}")


def _require_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        raise MaintenanceRadarPolicyError(f"{key} must be false")


def validate_policy(repo_root: Path, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    raw_policy_path = policy_path
    if not raw_policy_path.is_absolute():
        raw_policy_path = repo_root / raw_policy_path
    policy = _load_json(raw_policy_path)

    if policy.get("schema_version") != 1:
        raise MaintenanceRadarPolicyError("schema_version must be 1")
    if policy.get("id") != "cabinet_maintenance_radar_v0":
        raise MaintenanceRadarPolicyError("id must be cabinet_maintenance_radar_v0")
    if policy.get("mode") != "read_only_quality_radar":
        raise MaintenanceRadarPolicyError("mode must be read_only_quality_radar")
    if policy.get("repobrief_lenskit_dump_generation") != "external_only":
        raise MaintenanceRadarPolicyError("RepoBrief/Lenskit dump generation must be external_only")
    _require_false(policy, "cabinet_generates_repobrief_lenskit_dumps")

    canonical_doc = _require_string(policy.get("canonical_doc"), "canonical_doc")
    canonical_path = (repo_root / canonical_doc).resolve()
    try:
        canonical_path.relative_to(repo_root)
    except ValueError:
        raise MaintenanceRadarPolicyError(f"canonical_doc escapes repository: {canonical_doc}") from None
    if not canonical_path.is_file():
        raise MaintenanceRadarPolicyError(f"canonical_doc missing: {canonical_doc}")

    _require_subset(
        REQUIRED_SCAN_CLASSES,
        _require_string_set(policy.get("allowed_scan_classes"), "allowed_scan_classes"),
        "allowed_scan_classes",
    )
    _require_subset(
        REQUIRED_FINDING_FIELDS,
        _require_string_set(policy.get("required_finding_fields"), "required_finding_fields"),
        "required_finding_fields",
    )
    _require_subset(
        REQUIRED_OUTCOME_FIELDS,
        _require_string_set(policy.get("required_outcome_fields"), "required_outcome_fields"),
        "required_outcome_fields",
    )
    _require_subset(
        REQUIRED_OUTPUTS,
        _require_string_set(policy.get("allowed_outputs"), "allowed_outputs"),
        "allowed_outputs",
    )
    _require_subset(
        REQUIRED_PROHIBITED_EFFECTS,
        _require_string_set(policy.get("prohibited_effects"), "prohibited_effects"),
        "prohibited_effects",
    )
    _require_subset(
        REQUIRED_NON_CLAIMS,
        _require_string_set(policy.get("does_not_establish"), "does_not_establish"),
        "does_not_establish",
    )

    primary_sources = _require_object(policy.get("primary_sources"), "primary_sources")
    _require_subset(REQUIRED_PRIMARY_SOURCE_KEYS, set(primary_sources), "primary_sources")
    for key, value in primary_sources.items():
        _require_string(key, "primary source key")
        _require_string(value, f"primary source {key}")

    organ_roles = _require_object(policy.get("organ_roles"), "organ_roles")
    _require_subset(REQUIRED_ORGAN_ROLES, set(organ_roles), "organ_roles")
    for key, value in organ_roles.items():
        _require_string(key, "organ role key")
        _require_string(value, f"organ role {key}")

    handoff = _require_object(policy.get("handoff"), "handoff")
    if handoff.get("bureau_mode") != "proposal_only":
        raise MaintenanceRadarPolicyError("handoff.bureau_mode must be proposal_only")
    if handoff.get("grabowski_mode") != "after_task_or_operator_release":
        raise MaintenanceRadarPolicyError("handoff.grabowski_mode must be after_task_or_operator_release")
    for key in (
        "requires_human_review",
        "task_creation_allowed",
        "dispatch_allowed",
        "queue_mutation_allowed",
        "runtime_mutation_allowed",
    ):
        _require_bool(handoff.get(key), f"handoff.{key}")
    if handoff["requires_human_review"] is not True:
        raise MaintenanceRadarPolicyError("handoff.requires_human_review must be true")
    for key in (
        "task_creation_allowed",
        "dispatch_allowed",
        "queue_mutation_allowed",
        "runtime_mutation_allowed",
    ):
        if handoff[key] is not False:
            raise MaintenanceRadarPolicyError(f"handoff.{key} must be false")

    heimlern = _require_object(policy.get("heimlern_bridge"), "heimlern_bridge")
    if heimlern.get("status") != "planned_after_contract_repair":
        raise MaintenanceRadarPolicyError("heimlern_bridge.status must be planned_after_contract_repair")
    _require_subset(
        {"cabinet.maintenance_outcome.v1", "decision.outcome.v1"},
        _require_string_set(heimlern.get("input_contracts"), "heimlern_bridge.input_contracts"),
        "heimlern_bridge.input_contracts",
    )
    _require_subset(
        {
            "policy.weight_adjustment.proposed.v1",
            "cabinet.scan_rule_weight_adjustment.proposed.v1",
            "cabinet.routing_policy_adjustment.proposed.v1",
        },
        _require_string_set(heimlern.get("output_contracts"), "heimlern_bridge.output_contracts"),
        "heimlern_bridge.output_contracts",
    )
    if heimlern.get("direct_policy_application_allowed") is not False:
        raise MaintenanceRadarPolicyError("heimlern_bridge.direct_policy_application_allowed must be false")
    if not isinstance(heimlern.get("minimum_outcomes_per_rule"), int) or heimlern["minimum_outcomes_per_rule"] < 1:
        raise MaintenanceRadarPolicyError("heimlern_bridge.minimum_outcomes_per_rule must be a positive integer")
    confidence = heimlern.get("minimum_confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise MaintenanceRadarPolicyError("heimlern_bridge.minimum_confidence must be numeric")
    if not 0 <= float(confidence) <= 1:
        raise MaintenanceRadarPolicyError("heimlern_bridge.minimum_confidence must be between 0 and 1")

    return policy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    args = parser.parse_args(argv)

    try:
        policy = validate_policy(Path(args.repo_root), Path(args.policy))
    except (MaintenanceRadarPolicyError, OSError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: cabinet maintenance radar policy "
        f"({policy['id']}, {len(policy['allowed_scan_classes'])} scan classes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
