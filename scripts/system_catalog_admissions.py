#!/usr/bin/env python3
"""Validate admission evidence for newly introduced durable Systemkatalog components."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_POLICY_REL = Path("policy/component-admission.v1.json")
ADMISSIONS_REL = Path("registry/ecosystem/component-admissions.v1.json")
FROZEN_GRANDFATHERED_BASELINE_SHA256 = "691223849841ced5ed0f360c6d829da28f79eaaa85f3078ce165ac7a2b92ae91"


class ComponentAdmissionError(ValueError):
    pass


def _load_object(root: Path, relative: Path) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ComponentAdmissionError(f"{relative}: root must be an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComponentAdmissionError(f"{label} must be a non-empty string")
    return value


def _strings(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "possibly empty " if allow_empty else "non-empty "
        raise ComponentAdmissionError(f"{label} must be a {qualifier}string array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ComponentAdmissionError(f"{label} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise ComponentAdmissionError(f"{label} must not contain duplicates")
    return value


def _string_list_sha256(values: list[str]) -> str:
    payload = json.dumps(sorted(values), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _iso_date(value: Any, label: str) -> str:
    raw = _string(value, label)
    try:
        date.fromisoformat(raw)
    except ValueError as exc:
        raise ComponentAdmissionError(f"{label} must be an ISO date") from exc
    return raw


def validate_component_admissions(
    root: Path = ROOT,
    nodes: list[dict[str, Any]] | None = None,
    *,
    expected_grandfathered_sha256: str = FROZEN_GRANDFATHERED_BASELINE_SHA256,
) -> dict[str, Any]:
    root = root.resolve()
    policy = _load_object(root, ADMISSION_POLICY_REL)
    registry = _load_object(root, ADMISSIONS_REL)

    if policy.get("schemaVersion") != 1 or policy.get("kind") != "system_catalog_component_admission_policy":
        raise ComponentAdmissionError("component admission policy contract mismatch")
    if policy.get("owner") != "repo:systemkatalog":
        raise ComponentAdmissionError("component admission policy owner mismatch")
    if policy.get("role") != "admission_gate_for_new_durable_components":
        raise ComponentAdmissionError("component admission policy role mismatch")

    in_scope_types = set(_strings(policy.get("inScopeNodeTypes"), "inScopeNodeTypes"))
    expected_types = {"repository", "service", "background_process", "operator_surface"}
    if in_scope_types != expected_types:
        raise ComponentAdmissionError("inScopeNodeTypes mismatch")

    classes = set(_strings(policy.get("admissionClasses"), "admissionClasses"))
    if classes != {"replace", "reduce", "enable", "experimental"}:
        raise ComponentAdmissionError("admissionClasses mismatch")

    required_fields = set(_strings(policy.get("requiredAdmissionFields"), "requiredAdmissionFields"))
    expected_required = {
        "componentId",
        "componentKind",
        "admissionClass",
        "purpose",
        "consumers",
        "truthAuthority",
        "operatingDependencies",
        "maintenanceBurden",
        "reviewOrRetirementPath",
        "source",
        "doesNotEstablish",
    }
    if required_fields != expected_required:
        raise ComponentAdmissionError("requiredAdmissionFields mismatch")

    experimental_fields = set(
        _strings(policy.get("experimentalRequiredFields"), "experimentalRequiredFields")
    )
    if experimental_fields != {"successCriterion", "reviewBy"}:
        raise ComponentAdmissionError("experimentalRequiredFields mismatch")

    grandfathered_values = _strings(
        policy.get("grandfatheredNodeIds"), "grandfatheredNodeIds", allow_empty=True
    )
    declared_grandfathered_sha256 = _string(
        policy.get("grandfatheredBaselineSha256"), "grandfatheredBaselineSha256"
    )
    observed_grandfathered_sha256 = _string_list_sha256(grandfathered_values)
    if declared_grandfathered_sha256 != observed_grandfathered_sha256:
        raise ComponentAdmissionError("grandfathered baseline digest does not match grandfatheredNodeIds")
    if declared_grandfathered_sha256 != expected_grandfathered_sha256:
        raise ComponentAdmissionError("grandfathered baseline expansion or replacement requires an explicit contract change")
    grandfathered = set(grandfathered_values)

    boundary = policy.get("authorityBoundary")
    if not isinstance(boundary, dict):
        raise ComponentAdmissionError("authorityBoundary must be an object")
    if boundary.get("stableSemantics") != "Systemkatalog":
        raise ComponentAdmissionError("stable semantics authority must remain Systemkatalog")
    if boundary.get("taskPriorityAndCloseout") != "Bureau":
        raise ComponentAdmissionError("task priority and closeout authority must remain Bureau")
    _string(boundary.get("runtimeAndExecution"), "authorityBoundary.runtimeAndExecution")
    _strings(boundary.get("doesNotEstablish"), "authorityBoundary.doesNotEstablish")

    if registry.get("schemaVersion") != 1 or registry.get("kind") != "system_catalog_component_admissions":
        raise ComponentAdmissionError("component admissions registry contract mismatch")
    if registry.get("owner") != "repo:systemkatalog":
        raise ComponentAdmissionError("component admissions registry owner mismatch")
    if registry.get("policy") != str(ADMISSION_POLICY_REL):
        raise ComponentAdmissionError("component admissions policy binding mismatch")
    _strings(registry.get("doesNotEstablish"), "component admissions doesNotEstablish")

    if nodes is None:
        nodes_doc = _load_object(root, Path("registry/ecosystem/nodes.json"))
        raw_nodes = nodes_doc.get("nodes")
        if not isinstance(raw_nodes, list):
            raise ComponentAdmissionError("system catalog nodes missing")
        nodes = raw_nodes

    node_by_id: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ComponentAdmissionError(f"nodes[{index}] must be an object")
        node_id = _string(node.get("id"), f"nodes[{index}].id")
        node_type = _string(node.get("type"), f"nodes[{index}].type")
        if node_id in node_by_id:
            raise ComponentAdmissionError(f"duplicate node id: {node_id}")
        node_by_id[node_id] = node
        if node_type in {"background_process", "operator_surface"} and not node_id.startswith(
            ("process:", "surface:")
        ):
            raise ComponentAdmissionError(
                f"{node_id}: {node_type} ids must use process: or surface: prefixes"
            )

    admissions = registry.get("admissions")
    if not isinstance(admissions, list):
        raise ComponentAdmissionError("admissions must be an array")

    admission_by_id: dict[str, dict[str, Any]] = {}
    for index, admission in enumerate(admissions):
        label = f"admissions[{index}]"
        if not isinstance(admission, dict):
            raise ComponentAdmissionError(f"{label} must be an object")
        component_id = _string(admission.get("componentId"), f"{label}.componentId")
        if component_id in admission_by_id:
            raise ComponentAdmissionError(f"duplicate admission for {component_id}")
        node = node_by_id.get(component_id)
        if node is None:
            raise ComponentAdmissionError(f"{label} references unknown component: {component_id}")
        if node.get("type") not in in_scope_types:
            raise ComponentAdmissionError(f"{component_id} is not an in-scope durable component")
        if component_id in grandfathered:
            raise ComponentAdmissionError(
                f"{component_id} is grandfathered and must not carry redundant admission evidence"
            )

        admission_class = _string(admission.get("admissionClass"), f"{label}.admissionClass")
        if admission_class not in classes:
            raise ComponentAdmissionError(f"{label}.admissionClass is unsupported")

        expected_fields = set(required_fields)
        if admission_class == "experimental":
            expected_fields |= experimental_fields
        if set(admission) != expected_fields:
            raise ComponentAdmissionError(f"{label} fields mismatch for {admission_class}")

        component_kind = _string(admission.get("componentKind"), f"{label}.componentKind")
        if component_kind != node.get("type"):
            raise ComponentAdmissionError(f"{component_id}: componentKind differs from catalog node")
        purpose = _string(admission.get("purpose"), f"{label}.purpose")
        if purpose != node.get("purpose"):
            raise ComponentAdmissionError(f"{component_id}: purpose differs from catalog node")
        _strings(admission.get("consumers"), f"{label}.consumers")
        _string(admission.get("truthAuthority"), f"{label}.truthAuthority")
        _strings(
            admission.get("operatingDependencies"),
            f"{label}.operatingDependencies",
            allow_empty=True,
        )
        _string(admission.get("maintenanceBurden"), f"{label}.maintenanceBurden")
        _string(admission.get("reviewOrRetirementPath"), f"{label}.reviewOrRetirementPath")
        source = admission.get("source")
        if not isinstance(source, dict) or set(source) != {"kind", "ref"}:
            raise ComponentAdmissionError(f"{label}.source must contain exactly kind and ref")
        _string(source.get("kind"), f"{label}.source.kind")
        _string(source.get("ref"), f"{label}.source.ref")
        _strings(admission.get("doesNotEstablish"), f"{label}.doesNotEstablish")

        if admission_class == "experimental":
            _string(admission.get("successCriterion"), f"{label}.successCriterion")
            review_by = _iso_date(admission.get("reviewBy"), f"{label}.reviewBy")
            if date.fromisoformat(review_by) < date.today():
                raise ComponentAdmissionError(f"{label}.reviewBy is expired")

        admission_by_id[component_id] = admission

    in_scope_node_ids = {
        node_id
        for node_id, node in node_by_id.items()
        if node.get("type") in in_scope_types
    }
    uncovered = sorted(in_scope_node_ids - grandfathered - set(admission_by_id))
    if uncovered:
        raise ComponentAdmissionError(
            "new durable components lack admission evidence: " + ", ".join(uncovered)
        )

    return {
        "status": "valid",
        "inScopeComponents": len(in_scope_node_ids),
        "grandfatheredComponentsPresent": len(in_scope_node_ids & grandfathered),
        "admittedComponents": len(admission_by_id),
        "admissionClasses": sorted(classes),
    }


if __name__ == "__main__":
    print(json.dumps(validate_component_admissions(), ensure_ascii=False, sort_keys=True))
