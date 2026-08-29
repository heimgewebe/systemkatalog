#!/usr/bin/env python3
"""Read GitHub repository and source-document observations for drift checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMMAND_TIMEOUT_SECONDS = 20
COMMAND_ATTEMPTS = 3
OBSERVATION_BUDGET_SECONDS = 25.0
MAX_CONCURRENT_REQUESTS = 8


class ObservationBudgetExceeded(RuntimeError):
    """The global GitHub observation budget was exhausted."""


def _error_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return value.strip()


def _remaining_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ObservationBudgetExceeded("GitHub observation budget exhausted")
    return remaining


def _run_result(
    argv: list[str], *, text: bool, deadline: float | None = None
) -> subprocess.CompletedProcess[Any]:
    failures: list[str] = []
    for attempt in range(1, COMMAND_ATTEMPTS + 1):
        timeout = COMMAND_TIMEOUT_SECONDS
        if deadline is not None:
            timeout = min(float(COMMAND_TIMEOUT_SECONDS), _remaining_seconds(deadline))
        try:
            result = subprocess.run(
                argv,
                text=text,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"attempt {attempt}: timed out after {timeout:.3f}s")
            if deadline is not None and time.monotonic() >= deadline:
                detail = "; ".join(failures)
                raise ObservationBudgetExceeded(
                    f"GitHub observation budget exhausted while running {' '.join(argv)}: {detail}"
                )
        else:
            if result.returncode == 0:
                return result
            failures.append(
                f"attempt {attempt}: exit {result.returncode}: {_error_text(result.stderr)}"
            )
        if attempt < COMMAND_ATTEMPTS:
            delay = float(attempt)
            if deadline is not None:
                remaining = _remaining_seconds(deadline)
                if remaining <= delay:
                    detail = "; ".join(failures)
                    raise ObservationBudgetExceeded(
                        f"GitHub observation budget exhausted before retrying {' '.join(argv)}: {detail}"
                    )
            time.sleep(delay)
    detail = "; ".join(failures)
    raise RuntimeError(
        f"command failed after {COMMAND_ATTEMPTS} attempts: {' '.join(argv)}: {detail}"
    )


def _run(argv: list[str], *, deadline: float | None = None) -> str:
    result = _run_result(argv, text=True, deadline=deadline)
    if not isinstance(result.stdout, str):
        raise RuntimeError(f"command returned non-text output: {' '.join(argv)}")
    return result.stdout


def _run_bytes(argv: list[str], *, deadline: float | None = None) -> bytes:
    result = _run_result(argv, text=False, deadline=deadline)
    if not isinstance(result.stdout, bytes):
        raise RuntimeError(f"command returned non-bytes output: {' '.join(argv)}")
    return result.stdout


def _gh_json(path: str, *, deadline: float | None = None) -> dict[str, Any]:
    value = json.loads(_run(["gh", "api", path], deadline=deadline))
    if not isinstance(value, dict):
        raise RuntimeError(f"GitHub API returned non-object: {path}")
    return value


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_digest(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _repository_head(
    repository: str, meta: dict[str, Any], *, deadline: float
) -> tuple[str, str]:
    branch_info = meta.get("defaultBranchRef")
    default_branch = branch_info.get("name") if isinstance(branch_info, dict) else None
    commit = (
        branch_info.get("target", {}).get("oid")
        if isinstance(branch_info, dict) and isinstance(branch_info.get("target"), dict)
        else None
    )
    if not isinstance(default_branch, str) or not default_branch:
        api_meta = _gh_json(f"repos/{repository}", deadline=deadline)
        default_branch = api_meta.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise RuntimeError(f"GitHub repository has no default branch: {repository}")
    if not isinstance(commit, str) or len(commit) != 40:
        commit = _gh_json(
            f"repos/{repository}/commits/{default_branch}", deadline=deadline
        ).get("sha")
    if not isinstance(commit, str) or len(commit) != 40:
        raise RuntimeError(f"GitHub default branch commit is invalid: {repository}")
    return default_branch, commit


def _resolve_repository_heads(
    bindings: list[dict[str, Any]], by_repo: dict[str, dict[str, Any]], *, deadline: float
) -> dict[str, tuple[str, str]]:
    repositories = sorted(
        {
            source["repository"]
            for binding in bindings
            if isinstance(binding, dict)
            and isinstance((source := binding.get("source")), dict)
            and isinstance(source.get("locator"), dict)
            and source["locator"].get("kind") in {
                "file", "repository_metadata", "private_repository_metadata"
            }
            and source.get("repository") in by_repo
        }
    )
    if not repositories:
        return {}
    workers = min(MAX_CONCURRENT_REQUESTS, len(repositories))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="systemkatalog-gh-head") as executor:
        futures = {
            repository: executor.submit(
                _repository_head, repository, by_repo[repository], deadline=deadline
            )
            for repository in repositories
        }
        return {repository: futures[repository].result() for repository in repositories}


def _fetch_file_observation(
    *, repository: str, default_branch: str, commit: str, path: str, deadline: float
) -> dict[str, Any]:
    raw = _run_bytes(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw+json",
            f"repos/{repository}/contents/{path}?ref={commit}",
        ],
        deadline=deadline,
    )
    return {
        "repository": repository,
        "commit": commit,
        "defaultBranch": default_branch,
        "locator": {"kind": "file", "path": path},
        "contentSha256": _digest(raw),
    }


def observe(
    root: Path,
    organization: str = "heimgewebe",
    *,
    budget_seconds: float = OBSERVATION_BUDGET_SECONDS,
) -> dict[str, Any]:
    if budget_seconds <= 0:
        raise ValueError("budget_seconds must be positive")
    deadline = time.monotonic() + budget_seconds
    bindings = json.loads(
        (root / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8")
    )
    scope = json.loads(
        (root / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8")
    )
    repositories = json.loads(
        _run(
            [
                "gh",
                "repo",
                "list",
                organization,
                "--limit",
                "200",
                "--json",
                "name,nameWithOwner,isArchived,isFork,visibility,defaultBranchRef,description",
            ],
            deadline=deadline,
        )
    )
    if not isinstance(repositories, list):
        raise RuntimeError("gh repo list returned non-array")
    by_repo = {
        item["nameWithOwner"]: item
        for item in repositories
        if isinstance(item, dict) and isinstance(item.get("nameWithOwner"), str)
    }
    scope_by_repo = {item["repository"]: item for item in scope["repositories"]}
    systems = bindings["systems"]
    heads = _resolve_repository_heads(systems, by_repo, deadline=deadline)
    ordered: list[dict[str, Any] | None] = [None] * len(systems)
    file_jobs: list[tuple[int, str, str, str, str]] = []

    for index, binding in enumerate(systems):
        source = binding["source"]
        locator = source["locator"]
        kind = locator["kind"]
        if kind == "json_pointer":
            continue
        repository = source["repository"]
        meta = by_repo.get(repository)
        if meta is None:
            continue
        if kind == "file":
            default_branch, commit = heads[repository]
            file_jobs.append((index, repository, default_branch, commit, locator["path"]))
        elif kind == "repository_metadata":
            default_branch, commit = heads[repository]
            safe = {
                "full_name": repository,
                "description": meta.get("description") or None,
                "default_branch": default_branch,
                "visibility": str(meta.get("visibility") or "").lower(),
                "archived": bool(meta.get("isArchived")),
            }
            ordered[index] = {
                "repository": repository,
                "commit": commit,
                "defaultBranch": default_branch,
                "locator": {"kind": kind},
                "contentSha256": _canonical_digest(safe),
            }
        elif kind == "private_repository_metadata":
            projected = scope_by_repo.get(repository)
            if projected is None:
                continue
            default_branch, _commit = heads[repository]
            safe = {
                key: projected.get(key)
                for key in ("repository", "visibility", "classification", "node")
            }
            ordered[index] = {
                "repository": repository,
                "commit": "redacted",
                "defaultBranch": default_branch,
                "locator": {"kind": kind},
                "contentSha256": _canonical_digest(safe),
            }

    if file_jobs:
        workers = min(MAX_CONCURRENT_REQUESTS, len(file_jobs))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="systemkatalog-gh-file") as executor:
            futures = {
                index: executor.submit(
                    _fetch_file_observation,
                    repository=repository,
                    default_branch=default_branch,
                    commit=commit,
                    path=path,
                    deadline=deadline,
                )
                for index, repository, default_branch, commit, path in file_jobs
            }
            for index, *_ in file_jobs:
                ordered[index] = futures[index].result()

    _remaining_seconds(deadline)
    observations = [item for item in ordered if item is not None]
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
    parser.add_argument(
        "--budget-seconds",
        type=float,
        default=OBSERVATION_BUDGET_SECONDS,
        help=(
            "global fail-closed runtime budget for all GitHub observations "
            f"(default: {OBSERVATION_BUDGET_SECONDS:g}s)"
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = observe(
        args.root.resolve(), args.organization, budget_seconds=args.budget_seconds
    )
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
