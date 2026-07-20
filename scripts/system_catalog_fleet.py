#!/usr/bin/env python3
"""Fleet membership and repository-reference contract for Systemkatalog."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

COVERAGE_REL = Path("registry/ecosystem/fleet-coverage.v1.json")
MEMBERSHIPS = {"fleet", "related", "catalog-only", "archived-reference"}
REPOSITORY_RE = re.compile(r"^heimgewebe/([A-Za-z0-9_.-]+)$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    membership_authority = coverage["membershipAuthority"]
    if not isinstance(membership_authority, dict) or set(membership_authority) != {
        "repository",
        "commit",
        "path",
        "contentSha256",
        "scope",
    }:
        raise FleetCoverageError("Fleet membership authority fields mismatch")
    if (
        membership_authority["repository"] != "heimgewebe/metarepo"
        or membership_authority["path"] != "fleet/repos.yml"
        or membership_authority["scope"] != "fleet_membership_only"
        or not isinstance(membership_authority["commit"], str)
        or COMMIT_RE.fullmatch(membership_authority["commit"]) is None
        or not isinstance(membership_authority["contentSha256"], str)
        or SHA256_RE.fullmatch(membership_authority["contentSha256"]) is None
    ):
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


def parse_fleet_source(
    path: Path, *, expected_sha256: str | None = None
) -> tuple[dict[str, str], dict[str, str]]:
    """Parse and optionally hash-bind the small `fleet/repos.yml` contract."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise FleetCoverageError(f"Fleet authority missing: {path}") from None
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        if not isinstance(expected_sha256, str) or SHA256_RE.fullmatch(expected_sha256) is None:
            raise FleetCoverageError("Fleet authority expected SHA-256 invalid")
        if actual_sha256 != expected_sha256:
            raise FleetCoverageError(
                f"Fleet authority SHA-256 mismatch; expected={expected_sha256}, "
                f"actual={actual_sha256}"
            )
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise FleetCoverageError(f"Fleet authority is not UTF-8: {path}") from exc

    section = ""
    item: dict[str, str | bool] | None = None
    included: dict[str, str] = {}
    excluded: dict[str, str] = {}

    def finish() -> None:
        nonlocal item
        if item is None:
            return
        name = item.get("name")
        if not isinstance(name, str) or not name or name in included or name in excluded:
            raise FleetCoverageError(f"invalid or duplicated Fleet item: {name}")
        status = item.get("status")
        if item.get("fleet") is False:
            excluded[name] = (
                "archived-reference" if status == "archived-reference" else "excluded"
            )
        else:
            if status == "archived-reference":
                raise FleetCoverageError(
                    f"archived-reference Fleet item must set fleet: false: {name}"
                )
            included[name] = "related" if status == "related" else "fleet"
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
    coverage: dict[str, Any], source: tuple[dict[str, str], dict[str, str]]
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
    if catalog_exclusions != set(excluded):
        raise FleetCoverageError(
            f"Fleet exclusion drift; source={sorted(excluded)}, catalog={sorted(catalog_exclusions)}"
        )
    source_archived = {
        name for name, status in excluded.items() if status == "archived-reference"
    }
    catalog_archived = {
        row["repository"].split("/", 1)[1]
        for row in coverage["repositories"]
        if row["membership"] == "archived-reference"
    }
    if catalog_archived != source_archived:
        raise FleetCoverageError(
            f"Fleet archived-reference drift; source={sorted(source_archived)}, "
            f"catalog={sorted(catalog_archived)}"
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
    expected_archived = {
        item["repository"]: item["membership"] == "archived-reference"
        for item in coverage["repositories"]
    }
    missing = sorted(set(expected_archived) - set(remote))
    archived_mismatch = sorted(
        name
        for name, should_be_archived in expected_archived.items()
        if (remote.get(name, {}).get("isArchived") is True) != should_be_archived
    )
    if missing or archived_mismatch:
        raise FleetCoverageError(
            f"GitHub reference drift; missing={missing}, archived_mismatch={archived_mismatch}"
        )
    return len(expected_archived)
