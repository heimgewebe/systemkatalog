#!/usr/bin/env python3
"""Validate Systemkatalog organization classification and optional GitHub drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from system_catalog_fleet import validate_coverage
from system_catalog_scope import (
    OrganizationScopeError,
    load_scope,
    validate_github_inventory,
    validate_scope,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--github-inventory", type=Path)
    parser.add_argument("--visibility", choices=("public", "private", "internal"))
    args = parser.parse_args()
    try:
        nodes = json.loads(
            (args.repo_root / "registry/ecosystem/nodes.json").read_text(
                encoding="utf-8"
            )
        )["nodes"]
        repository_nodes = {
            item["id"] for item in nodes if item.get("type") == "repository"
        }
        coverage = validate_coverage(args.repo_root, repository_nodes)
        scope = validate_scope(args.repo_root, repository_nodes, coverage)
        result = {
            "status": "valid",
            "organization": scope["source"]["organization"],
            "repositories": len(scope["repositories"]),
            "catalogRepositories": sum(
                row["classification"] == "catalog" for row in scope["repositories"]
            ),
            "archivedReferenceRepositories": sum(
                row["classification"] == "archived_reference"
                for row in scope["repositories"]
            ),
            "excludedRepositories": sum(
                row["classification"] == "excluded" for row in scope["repositories"]
            ),
        }
        if args.github_inventory:
            inventory = json.loads(args.github_inventory.read_text(encoding="utf-8"))
            result["githubRepositories"] = validate_github_inventory(
                scope, inventory, visibility=args.visibility
            )
            result["githubVisibility"] = args.visibility or "all"
    except (
        OrganizationScopeError,
        json.JSONDecodeError,
        OSError,
        UnicodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
