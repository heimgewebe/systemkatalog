#!/usr/bin/env python3
"""Create a proposal-only drift report for the static Systemkatalog."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Canonical drift runs execute on the operator host and must not leave local
# bytecode artifacts in the versioned checkout. This is set before the lazy
# import of system_catalog_fleet in build_report().
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _active_repositories(raw: Any) -> dict[str, dict[str, Any]]:
    items = raw.get("repositories") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("GitHub inventory must be an array or contain repositories")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or item.get("isArchived") is True or item.get("isFork") is True:
            continue
        repo = item.get("nameWithOwner")
        if not isinstance(repo, str):
            name = item.get("name")
            repo = f"heimgewebe/{name}" if isinstance(name, str) else None
        if not repo:
            continue
        result[repo] = item
    return result


def _observation_key(repository: str, locator: dict[str, Any]) -> tuple[str, str, str]:
    return repository, str(locator.get("kind")), str(locator.get("path") or "")


def build_report(root: Path, github_data: dict[str, Any] | list[Any], *, fleet_file: Path | None = None) -> dict[str, Any]:
    scope = _load(root / "registry/ecosystem/organization-scope.v1.json")
    bindings = _load(root / "registry/ecosystem/source-bindings.v1.json")
    expected = {item["repository"]: item for item in scope["repositories"]}
    actual = _active_repositories(github_data)
    changes: list[dict[str, Any]] = []

    for repository in sorted(set(actual) - set(expected)):
        changes.append({"kind": "repository_unclassified", "repository": repository})
    for repository in sorted(set(expected) - set(actual)):
        changes.append({"kind": "repository_missing_or_archived", "repository": repository})
    for repository in sorted(set(expected) & set(actual)):
        expected_visibility = expected[repository].get("visibility")
        actual_visibility = str(actual[repository].get("visibility") or "").lower()
        if expected_visibility != actual_visibility:
            changes.append({
                "kind": "repository_visibility_changed",
                "repository": repository,
                "expected": expected_visibility,
                "actual": actual_visibility,
            })

    observations_raw = github_data.get("observations", []) if isinstance(github_data, dict) else []
    observations = {
        _observation_key(item["repository"], item["locator"]): item
        for item in observations_raw
        if isinstance(item, dict) and isinstance(item.get("repository"), str) and isinstance(item.get("locator"), dict)
    }
    for binding in bindings["systems"]:
        source = binding["source"]
        locator = source["locator"]
        if locator["kind"] == "json_pointer":
            continue
        key = _observation_key(source["repository"], locator)
        observed = observations.get(key)
        if observed is None:
            changes.append({
                "kind": "source_observation_missing",
                "system": binding["system"],
                "repository": source["repository"],
                "locator": locator,
            })
            continue
        if observed.get("defaultBranch") != source.get("defaultBranch"):
            changes.append({
                "kind": "default_branch_changed",
                "system": binding["system"],
                "repository": source["repository"],
                "expected": source.get("defaultBranch"),
                "actual": observed.get("defaultBranch"),
            })
        if observed.get("contentSha256") != locator["contentSha256"]:
            changes.append({
                "kind": "primary_source_changed",
                "system": binding["system"],
                "repository": source["repository"],
                "locatorKind": locator["kind"],
                "path": locator.get("path"),
                "boundCommit": source["commit"],
                "observedCommit": observed.get("commit"),
                "boundSha256": locator["contentSha256"],
                "observedSha256": observed.get("contentSha256"),
            })

    if fleet_file is not None:
        try:
            from system_catalog_fleet import compare_with_source, load_coverage, parse_fleet_source
            compare_with_source(load_coverage(root), parse_fleet_source(fleet_file))
        except Exception as exc:
            changes.append({"kind": "fleet_membership_drift", "detail": str(exc)})

    material = bool(changes)
    generated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proposal = {
        "kind": "system_catalog_update_proposal",
        "proposalOnly": True,
        "autoMerge": False,
        "candidateId": "SYSTEMKATALOG-DRIFT-CLOSED-LOOP-V1",
        "suggestedActions": [
            "verify each change at its primary source",
            "update canonical registry or source binding only after semantic review",
            "render deterministic projections",
            "publish the map manifest in a second commit",
            "merge only through normal review gates",
        ] if material else [],
    }
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_drift_report",
        "generatedAt": generated,
        "materialDrift": material,
        "changeCount": len(changes),
        "changes": changes,
        "bureauCandidate": {
            "candidateId": "SYSTEMKATALOG-DRIFT-CLOSED-LOOP-V1",
            "repo": "repo.systemkatalog",
            "title": "Systemkatalog-Drift prüfen und proposal-only aktualisieren",
            "dedupeKey": "systemkatalog-drift-v1",
        } if material else None,
        "proposal": proposal,
        "doesNotEstablish": ["semantic_truth", "merge_readiness", "automatic_update_authority"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--github-observations", type=Path, required=True)
    parser.add_argument("--fleet-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--proposal-output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args.root.resolve(), _load(args.github_observations), fleet_file=args.fleet_file)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    if args.proposal_output:
        args.proposal_output.parent.mkdir(parents=True, exist_ok=True)
        args.proposal_output.write_text(json.dumps(report["proposal"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 2 if args.check and report["materialDrift"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
