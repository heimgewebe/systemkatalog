#!/usr/bin/env python3
"""Read GitHub repository and source-document observations for drift checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _run(argv: list[str]) -> str:
    result = subprocess.run(argv, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(argv)}: {result.stderr.strip()}")
    return result.stdout


def _gh_json(path: str) -> dict[str, Any]:
    value = json.loads(_run(["gh", "api", path]))
    if not isinstance(value, dict):
        raise RuntimeError(f"GitHub API returned non-object: {path}")
    return value


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_digest(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def observe(root: Path, organization: str = "heimgewebe") -> dict[str, Any]:
    bindings = json.loads((root / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8"))
    scope = json.loads((root / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8"))
    repositories = json.loads(_run([
        "gh", "repo", "list", organization, "--limit", "200",
        "--json", "name,nameWithOwner,isArchived,isFork,visibility,defaultBranchRef,description",
    ]))
    if not isinstance(repositories, list):
        raise RuntimeError("gh repo list returned non-array")
    by_repo = {item["nameWithOwner"]: item for item in repositories if isinstance(item, dict) and isinstance(item.get("nameWithOwner"), str)}
    scope_by_repo = {item["repository"]: item for item in scope["repositories"]}
    observations = []
    for binding in bindings["systems"]:
        source = binding["source"]
        locator = source["locator"]
        if locator["kind"] == "json_pointer":
            continue
        repository = source["repository"]
        meta = by_repo.get(repository)
        if meta is None:
            continue
        branch_info = meta.get("defaultBranchRef")
        default_branch = branch_info.get("name") if isinstance(branch_info, dict) else None
        commit = branch_info.get("target", {}).get("oid") if isinstance(branch_info, dict) and isinstance(branch_info.get("target"), dict) else None
        if not isinstance(commit, str) or len(commit) != 40:
            api_meta = _gh_json(f"repos/{repository}")
            default_branch = api_meta["default_branch"]
            commit = _gh_json(f"repos/{repository}/commits/{default_branch}")["sha"]
        kind = locator["kind"]
        if kind == "file":
            result = subprocess.run([
                "gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                f"repos/{repository}/contents/{locator['path']}?ref={commit}",
            ], capture_output=True)
            if result.returncode != 0:
                continue
            content_sha = _digest(result.stdout)
            observed_commit: str = commit
        elif kind == "repository_metadata":
            safe = {
                "full_name": repository,
                "description": meta.get("description") or None,
                "default_branch": default_branch,
                "visibility": str(meta.get("visibility") or "").lower(),
                "archived": bool(meta.get("isArchived")),
            }
            content_sha = _canonical_digest(safe)
            observed_commit = commit
        elif kind == "private_repository_metadata":
            projected = scope_by_repo.get(repository)
            if projected is None:
                continue
            safe = {key: projected.get(key) for key in ("repository", "visibility", "classification", "node")}
            content_sha = _canonical_digest(safe)
            observed_commit = "redacted"
        else:
            continue
        observations.append({
            "repository": repository,
            "commit": observed_commit,
            "defaultBranch": default_branch,
            "locator": {"kind": kind, **({"path": locator["path"]} if "path" in locator else {})},
            "contentSha256": content_sha,
        })
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_github_observations",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "organization": organization,
        "repositories": repositories,
        "observations": observations,
        "doesNotEstablish": ["semantic_truth", "runtime_health", "merge_readiness"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--organization", default="heimgewebe")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = observe(args.root.resolve(), args.organization)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
