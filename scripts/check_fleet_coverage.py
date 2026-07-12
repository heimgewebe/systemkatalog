#!/usr/bin/env python3
"""Compare Systemkatalog repository coverage with metarepo Fleet truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from system_catalog_fleet import (
    FleetCoverageError,
    compare_with_source,
    load_coverage,
    parse_fleet_source,
    validate_github_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--fleet-file", type=Path, required=True)
    parser.add_argument("--github-inventory", type=Path)
    args = parser.parse_args()
    try:
        coverage = load_coverage(args.repo_root)
        result = compare_with_source(coverage, parse_fleet_source(args.fleet_file))
        if args.github_inventory:
            inventory = json.loads(args.github_inventory.read_text(encoding="utf-8"))
            result["githubRepositories"] = validate_github_inventory(
                coverage, inventory
            )
    except (FleetCoverageError, json.JSONDecodeError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
