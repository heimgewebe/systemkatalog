#!/usr/bin/env python3
"""Fleet membership and repository-reference contract for Systemkatalog."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

COVERAGE_REL = Path("registry/ecosystem/fleet-coverage.v1.json")
MEMBERSHIPS = {"fleet", "related", "catalog-only"}
REPOSITORY_RE = re.compile(r"^heimgewebe/([A-Za-z0-9_.-]+)$")


class FleetCoverageError(ValueError):
    pass


def load_coverage(root: Path) -> dict[str, Any]:
    path = root.resolve() / COVERAGE_REL
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FleetCoverageError(f"missing Fleet coverage file: {path}") from None
    except json.JSONDecodeError as exc:
        raise FleetCoverageError(f"invalid Fleet coverage JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise FleetCoverageError("Fleet coverage root must be an object")
    return value


def validate_coverage(root: Path, repository_nodes: set[str]) -> dict[str, Any]:
    coverage = load_coverage(root)
    if set(coverage) != {
        "schemaVersion",
        "kind",
        "updatedAt",
        "membershipAuthority",
        "catalogAuthority",
        "repositories",
        "sourceExclusions",
        "doesNotEstablish",
    }:
        raise FleetCoverageError("Fleet coverage fields mismatch")
    if (coverage["schemaVersion"], coverage["kind"]) != (
        1,
        "system_catalog_fleet_coverage",
    ):
        raise FleetCoverageError("Fleet coverage identity mismatch")
    if coverage["membershipAuthority"] != {
        "repository": "heimgewebe/metarepo",
        "path": "fleet/repos.yml",
        "scope": "fleet_membership_only",
    }:
        raise FleetCoverageError("Fleet membership authority mismatch")
    if coverage["catalogAuthority"] != {
        "repository": "heimgewebe/systemkatalog",
        "inventory": "registry/ecosystem/nodes.json",
        "scope": "purpose_relations_authority_and_entrypoints",
    }:
        raise FleetCoverageError("catalog authority mismatch")

    rows = coverage["repositories"]
    if not isinstance(rows, list) or not rows:
        raise FleetCoverageError("Fleet repository mappings missing")
    mapped: set[str] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != {
            "node",
            "repository",
            "entrypoint",
            "membership",
        }:
            raise FleetCoverageError(f"Fleet mapping {index} fields mismatch")
        node, repository = row["node"], row["repository"]
        match = (
            REPOSITORY_RE.fullmatch(repository) if isinstance(repository, str) else None
        )
        if node not in repository_nodes or match is None:
            raise FleetCoverageError(
                f"Fleet mapping {index} references unknown repository"
            )
        if (
            node != f"repo:{match.group(1)}"
            or row["entrypoint"] != f"https://github.com/{repository}"
        ):
            raise FleetCoverageError(f"Fleet mapping {index} identity mismatch")
        if row["membership"] not in MEMBERSHIPS or node in mapped:
            raise FleetCoverageError(
                f"Fleet mapping {index} membership or duplicate invalid"
            )
        mapped.add(node)
    if mapped != repository_nodes:
        raise FleetCoverageError(
            f"repository coverage mismatch; missing={sorted(repository_nodes - mapped)}, "
            f"extra={sorted(mapped - repository_nodes)}"
        )

    exclusions = coverage["sourceExclusions"]
    if not isinstance(exclusions, list):
        raise FleetCoverageError("sourceExclusions must be an array")
    names: set[str] = set()
    for index, item in enumerate(exclusions, 1):
        if not isinstance(item, dict) or set(item) != {"name", "reason"}:
            raise FleetCoverageError(f"source exclusion {index} fields mismatch")
        if not all(
            isinstance(item[key], str) and item[key].strip()
            for key in ("name", "reason")
        ):
            raise FleetCoverageError(f"source exclusion {index} invalid")
        if item["name"] in names:
            raise FleetCoverageError(f"source exclusion duplicated: {item['name']}")
        names.add(item["name"])
    non_claims = coverage["doesNotEstablish"]
    if (
        not isinstance(non_claims, list)
        or not non_claims
        or not all(isinstance(item, str) and item for item in non_claims)
    ):
        raise FleetCoverageError("doesNotEstablish must be a non-empty string array")
    return coverage


def parse_fleet_source(path: Path) -> tuple[dict[str, str], set[str]]:
    """Parse the intentionally small `fleet/repos.yml` contract without a YAML dependency."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise FleetCoverageError(f"Fleet authority missing: {path}") from None

    section = ""
    item: dict[str, str | bool] | None = None
    included: dict[str, str] = {}
    excluded: set[str] = set()

    def finish() -> None:
        nonlocal item
        if item is None:
            return
        name = item.get("name")
        if not isinstance(name, str) or not name or name in included or name in excluded:
            raise FleetCoverageError(f"invalid or duplicated Fleet item: {name}")
        if item.get("fleet") is False:
            excluded.add(name)
        else:
            included[name] = "related" if item.get("status") == "related" else "fleet"
        item = None

    for raw in lines:
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip(" "))
        if not stripped or stripped.startswith(("#", "---")):
            continue
        if indent == 0 and stripped in {"static:", "repos:"}:
            finish()
            section = stripped[:-1]
        elif indent == 2 and stripped == "include:" and section == "static":
            continue
        elif stripped.startswith("- name:") and (
            (section == "repos" and indent == 2)
            or (section == "static" and indent == 4)
        ):
            finish()
            item = {"name": stripped.split(":", 1)[1].strip().strip("\"'")}
        elif item is not None and ":" in stripped and indent in {4, 6}:
            key, raw_value = (part.strip() for part in stripped.split(":", 1))
            value = raw_value.strip("\"'")
            item[key] = (
                value.lower() == "true" if value.lower() in {"true", "false"} else value
            )
        else:
            raise FleetCoverageError(f"unsupported Fleet YAML structure: {raw}")
    finish()
    return included, excluded


def compare_with_source(
    coverage: dict[str, Any], source: tuple[dict[str, str], set[str]]
) -> dict[str, Any]:
    included, excluded = source
    catalog = {
        row["repository"].split("/", 1)[1]: row["membership"]
        for row in coverage["repositories"]
        if row["membership"] in {"fleet", "related"}
    }
    if catalog != included:
        raise FleetCoverageError(
            f"Fleet membership drift; missing={sorted(set(included) - set(catalog))}, "
            f"unexpected={sorted(set(catalog) - set(included))}, "
            f"wrong_membership={sorted(name for name in set(catalog) & set(included) if catalog[name] != included[name])}"
        )
    catalog_exclusions = {item["name"] for item in coverage["sourceExclusions"]}
    if catalog_exclusions != excluded:
        raise FleetCoverageError(
            f"Fleet exclusion drift; source={sorted(excluded)}, catalog={sorted(catalog_exclusions)}"
        )
    return {
        "status": "valid",
        "fleetRepositories": len(included),
        "sourceExclusions": len(excluded),
        "membershipAuthority": "heimgewebe/metarepo:fleet/repos.yml",
        "catalogAuthority": "heimgewebe/systemkatalog:registry/ecosystem/nodes.json",
    }


def validate_github_inventory(coverage: dict[str, Any], inventory: Any) -> int:
    if not isinstance(inventory, list):
        raise FleetCoverageError("GitHub inventory must be an array")
    remote = {
        item.get("nameWithOwner"): item for item in inventory if isinstance(item, dict)
    }
    expected = {item["repository"] for item in coverage["repositories"]}
    missing = sorted(expected - set(remote))
    archived = sorted(
        name for name in expected if remote.get(name, {}).get("isArchived") is True
    )
    if missing or archived:
        raise FleetCoverageError(
            f"GitHub reference drift; missing={missing}, archived={archived}"
        )
    return len(expected)
