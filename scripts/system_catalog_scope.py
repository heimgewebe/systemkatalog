#!/usr/bin/env python3
"""Organization-wide repository classification contract for Systemkatalog."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCOPE_REL = Path("registry/ecosystem/organization-scope.v1.json")
REPOSITORY_RE = re.compile(r"^heimgewebe/([A-Za-z0-9_.-]+)$")
VISIBILITIES = {"public", "private", "internal"}
CLASSIFICATIONS = {"catalog", "archived_reference", "excluded"}


class OrganizationScopeError(ValueError):
    pass


def load_scope(root: Path) -> dict[str, Any]:
    path = root.resolve() / SCOPE_REL
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise OrganizationScopeError(f"organization scope missing: {path}") from None
    except json.JSONDecodeError as exc:
        raise OrganizationScopeError(f"invalid organization scope JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise OrganizationScopeError("organization scope root must be an object")
    return value


def validate_scope(
    root: Path,
    repository_nodes: set[str],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    scope = load_scope(root)
    if set(scope) != {
        "schemaVersion",
        "kind",
        "updatedAt",
        "source",
        "repositories",
        "doesNotEstablish",
    }:
        raise OrganizationScopeError("organization scope fields mismatch")
    if (scope["schemaVersion"], scope["kind"]) != (
        1,
        "system_catalog_organization_scope",
    ):
        raise OrganizationScopeError("organization scope identity mismatch")
    if not isinstance(scope["updatedAt"], str) or not scope["updatedAt"].strip():
        raise OrganizationScopeError("organization scope updatedAt missing")

    source = scope["source"]
    if not isinstance(source, dict) or set(source) != {
        "provider",
        "organization",
        "observedAt",
        "selection",
        "repositoryCount",
    }:
        raise OrganizationScopeError("organization scope source fields mismatch")
    if source["provider"] != "github" or source["organization"] != "heimgewebe":
        raise OrganizationScopeError("organization scope source identity mismatch")
    if source["selection"] != {"archived": "include", "fork": False}:
        raise OrganizationScopeError("organization scope selection mismatch")
    if not isinstance(source["observedAt"], str) or not source["observedAt"].strip():
        raise OrganizationScopeError("organization scope observedAt missing")

    rows = scope["repositories"]
    if not isinstance(rows, list) or not rows:
        raise OrganizationScopeError("organization scope repositories missing")
    if source["repositoryCount"] != len(rows):
        raise OrganizationScopeError("organization scope repositoryCount mismatch")

    expected_fields = {
        "name",
        "repository",
        "visibility",
        "classification",
        "node",
        "reason",
    }
    names: list[str] = []
    catalog_nodes: set[str] = set()
    exclusions: set[str] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != expected_fields:
            raise OrganizationScopeError(f"organization scope row {index} fields mismatch")
        name = row["name"]
        repository = row["repository"]
        match = REPOSITORY_RE.fullmatch(repository) if isinstance(repository, str) else None
        if not isinstance(name, str) or not name or match is None or match.group(1) != name:
            raise OrganizationScopeError(f"organization scope row {index} identity mismatch")
        if row["visibility"] not in VISIBILITIES:
            raise OrganizationScopeError(f"organization scope row {index} visibility invalid")
        if row["classification"] not in CLASSIFICATIONS:
            raise OrganizationScopeError(f"organization scope row {index} classification invalid")
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            raise OrganizationScopeError(f"organization scope row {index} reason missing")
        if row["classification"] in {"catalog", "archived_reference"}:
            expected_node = f"repo:{name}"
            if row["node"] != expected_node or expected_node not in repository_nodes:
                raise OrganizationScopeError(
                    f"organization scope row {index} catalog node mismatch"
                )
            catalog_nodes.add(expected_node)
        else:
            if row["node"] is not None:
                raise OrganizationScopeError(
                    f"organization scope row {index} excluded node must be null"
                )
            exclusions.add(name)
        names.append(name)

    if names != sorted(names, key=str.casefold) or len(names) != len(set(names)):
        raise OrganizationScopeError("organization scope rows must be unique and sorted")
    if catalog_nodes != repository_nodes:
        raise OrganizationScopeError(
            f"organization catalog coverage mismatch; missing={sorted(repository_nodes - catalog_nodes)}, "
            f"extra={sorted(catalog_nodes - repository_nodes)}"
        )
    mapped_nodes = {row["node"] for row in coverage["repositories"]}
    if mapped_nodes != catalog_nodes:
        raise OrganizationScopeError("organization scope differs from repository coverage")
    if exclusions & {node.split(":", 1)[1] for node in repository_nodes}:
        raise OrganizationScopeError("organization exclusions overlap catalog repositories")

    non_claims = scope["doesNotEstablish"]
    if (
        not isinstance(non_claims, list)
        or not non_claims
        or not all(isinstance(item, str) and item for item in non_claims)
    ):
        raise OrganizationScopeError("organization scope doesNotEstablish invalid")
    return scope


def validate_github_inventory(
    scope: dict[str, Any],
    inventory: Any,
    *,
    visibility: str | None = None,
) -> int:
    if visibility is not None and visibility not in VISIBILITIES:
        raise OrganizationScopeError(f"unsupported visibility filter: {visibility}")
    if not isinstance(inventory, list):
        raise OrganizationScopeError("GitHub organization inventory must be an array")

    remote: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if not isinstance(item, dict):
            continue
        if item.get("isFork") is True:
            continue
        name = item.get("name")
        owner = item.get("nameWithOwner")
        raw_visibility = item.get("visibility")
        if not isinstance(name, str) or owner != f"heimgewebe/{name}":
            continue
        normalized_visibility = (
            raw_visibility.lower() if isinstance(raw_visibility, str) else None
        )
        if normalized_visibility not in VISIBILITIES:
            raise OrganizationScopeError(f"GitHub visibility missing for {owner}")
        if visibility is None or normalized_visibility == visibility:
            remote[name] = {
                "repository": owner,
                "visibility": normalized_visibility,
                "archived": item.get("isArchived") is True,
            }

    expected = {
        row["name"]: {
            "repository": row["repository"],
            "visibility": row["visibility"],
            "archived": row["classification"] == "archived_reference",
        }
        for row in scope["repositories"]
        if visibility is None or row["visibility"] == visibility
    }
    if set(remote) != set(expected):
        raise OrganizationScopeError(
            f"GitHub organization scope drift; missing={sorted(set(expected) - set(remote))}, "
            f"unexpected={sorted(set(remote) - set(expected))}"
        )
    wrong = sorted(name for name in expected if expected[name] != remote[name])
    if wrong:
        raise OrganizationScopeError(
            f"GitHub organization identity or visibility drift: {wrong}"
        )
    return len(expected)
