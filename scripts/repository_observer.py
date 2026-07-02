#!/usr/bin/env python3
"""Deterministic, read-only observation of approved local repositories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

POLICY_SCHEMA = "cabinet.repository-collector-policy.v1"
OUTPUT_SCHEMA = "cabinet.repository-collection.v1"
POLICY_KEYS = {"schema", "repositories"}
ENTRY_KEYS = {"id", "directory", "expected_remote", "reference"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REMOTE_RE = re.compile(r"^github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$")


class CollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyEntry:
    id: str
    directory: str
    expected_remote: str
    reference: str


@dataclass(frozen=True)
class Policy:
    entries: tuple[PolicyEntry, ...]
    sha256: str


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def reject_symlinks(path: Path, label: str) -> None:
    path = absolute(path)
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            break
        if stat.S_ISLNK(mode):
            raise CollectorError(f"{label} may not contain symlinks: {current}")


def require_directory(path: Path, label: str) -> Path:
    path = absolute(path)
    reject_symlinks(path, label)
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError as exc:
        raise CollectorError(f"{label} is missing: {path}") from exc
    if not stat.S_ISDIR(mode):
        raise CollectorError(f"{label} is not a directory: {path}")
    return path


def safe_relative(path: Path, label: str) -> None:
    if path.is_absolute() or not path.parts:
        raise CollectorError(f"{label} uses an unsafe relative path: {path}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise CollectorError(f"{label} uses an unsafe relative path: {path}")
    if path.parts[0] == ".git":
        raise CollectorError(f"{label} may not read Git internals: {path}")


def require_file(root: Path, relative: Path, label: str) -> Path:
    safe_relative(relative, label)
    root = require_directory(root, f"{label} root")
    path = root / relative
    reject_symlinks(path, label)
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError as exc:
        raise CollectorError(f"{label} is missing: {relative.as_posix()}") from exc
    if not stat.S_ISREG(mode):
        raise CollectorError(f"{label} is not a regular file: {relative.as_posix()}")
    return path


def normalize_observed_at(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise CollectorError("observed_at must be a non-empty RFC3339 timestamp")
    if re.search(r"T\d{2}:\d{2}:\d{2}\.", value):
        raise CollectorError("observed_at must use whole seconds")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise CollectorError("observed_at must be valid RFC3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CollectorError("observed_at must include a timezone")
    if parsed.microsecond:
        raise CollectorError("observed_at must use whole seconds")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def canonicalize_remote(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CollectorError("repository remote must be a non-empty string")
    remote = value.strip()
    github_scp_user = re.fullmatch(
        r"[A-Za-z0-9_.-]+@" + "github" + r"\.com:(.+)", remote
    )
    if github_scp_user is not None:
        path = github_scp_user.group(1)
    else:
        prefixes = (
            "git@github.com:",
            "ssh://git@github.com/",
            "https://github.com/",
            "github.com:",
        )
        path = next(
            (remote[len(prefix) :] for prefix in prefixes if remote.startswith(prefix)),
            None,
        )
    if path is None or any(token in path for token in ("?", "#", "\\")):
        raise CollectorError(f"unsupported repository remote: {remote}")
    path = path.rstrip("/")
    if not path.endswith(".git"):
        path += ".git"
    if len(path.split("/")) != 2:
        raise CollectorError(f"unsupported repository remote: {remote}")
    canonical = f"github.com:{path}"
    if not REMOTE_RE.fullmatch(canonical):
        raise CollectorError(f"unsupported repository remote: {remote}")
    return canonical


def validate_reference(repo_root: Path, entry: PolicyEntry) -> None:
    if not entry.reference.endswith("Repository Reference.md"):
        raise CollectorError(f"repository {entry.id!r} has an invalid reference path")
    text = require_file(
        repo_root, Path(entry.reference), f"repository {entry.id!r} reference"
    ).read_text(encoding="utf-8", errors="strict")
    if f"| Repository | `{entry.id}` |" not in text:
        raise CollectorError(f"repository {entry.id!r} reference does not confirm its id")
    if f"| Remote | `{entry.expected_remote}` |" not in text:
        raise CollectorError(
            f"repository {entry.id!r} reference does not confirm its canonical remote"
        )


def load_policy(repo_root: Path, policy_relative: Path) -> Policy:
    repo_root = require_directory(repo_root, "repository root")
    raw = require_file(repo_root, policy_relative, "observation policy").read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectorError("observation policy must be strict UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != POLICY_KEYS:
        raise CollectorError(f"observation policy keys must be {sorted(POLICY_KEYS)}")
    if value["schema"] != POLICY_SCHEMA:
        raise CollectorError("observation policy has an unsupported schema")
    repositories = value["repositories"]
    if not isinstance(repositories, list) or not repositories:
        raise CollectorError("observation policy repositories must be a non-empty array")

    entries: list[PolicyEntry] = []
    ids: set[str] = set()
    directories: set[str] = set()
    references: set[str] = set()
    for index, item in enumerate(repositories):
        label = f"repositories[{index}]"
        if not isinstance(item, dict) or set(item) != ENTRY_KEYS:
            raise CollectorError(f"{label} keys must be {sorted(ENTRY_KEYS)}")
        values = [item.get(key) for key in ("id", "directory", "expected_remote", "reference")]
        if any(not isinstance(value, str) or not value for value in values):
            raise CollectorError(f"{label} values must be non-empty strings")
        repository_id, directory, expected_remote, reference = values
        assert isinstance(repository_id, str)
        assert isinstance(directory, str)
        assert isinstance(expected_remote, str)
        assert isinstance(reference, str)
        if not ID_RE.fullmatch(repository_id):
            raise CollectorError(f"{label}.id is invalid: {repository_id!r}")
        if not DIR_RE.fullmatch(directory) or directory in {".", ".."}:
            raise CollectorError(f"{label}.directory is invalid: {directory!r}")
        if canonicalize_remote(expected_remote) != expected_remote:
            raise CollectorError(f"{label}.expected_remote is not canonical")
        safe_relative(Path(reference), f"{label}.reference")
        if repository_id in ids:
            raise CollectorError(f"duplicate repository id: {repository_id}")
        if directory in directories:
            raise CollectorError(f"duplicate repository directory: {directory}")
        if reference in references:
            raise CollectorError(f"duplicate repository reference: {reference}")
        ids.add(repository_id)
        directories.add(directory)
        references.add(reference)
        entry = PolicyEntry(repository_id, directory, expected_remote, reference)
        validate_reference(repo_root, entry)
        entries.append(entry)
    entries.sort(key=lambda entry: entry.id)
    return Policy(tuple(entries), hashlib.sha256(raw).hexdigest())


def git_env() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", LANG="C", LC_ALL="C"
    )
    return environment


def run_git(
    repository: Path,
    arguments: Sequence[str],
    allowed: set[int] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    allowed = {0} if allowed is None else allowed
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=git_env(),
            check=False,
        )
    except FileNotFoundError as exc:
        raise CollectorError("git executable not found") from exc
    if completed.returncode not in allowed:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise CollectorError(
            f"git {' '.join(arguments)} failed for {repository.name}: {detail}"
        )
    return completed


def decode_line(value: bytes, label: str) -> str:
    try:
        decoded = value.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise CollectorError(f"{label} is not valid UTF-8") from exc
    if not decoded:
        raise CollectorError(f"{label} is empty")
    return decoded


def current_branch(repository: Path) -> str | None:
    result = run_git(
        repository, ["symbolic-ref", "--quiet", "--short", "HEAD"], {0, 1}
    )
    return None if result.returncode == 1 else decode_line(result.stdout, "branch")


def current_upstream(repository: Path) -> str | None:
    arguments = ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]
    result = run_git(repository, arguments, {0, 128})
    if result.returncode == 0:
        return decode_line(result.stdout, "upstream")
    detail = result.stderr.decode("utf-8", errors="replace").lower()
    if any(token in detail for token in ("no upstream configured", "no upstream branch", "does not point to a branch")):
        return None
    raise CollectorError(
        f"git {' '.join(arguments)} failed for {repository.name}: {detail.strip()}"
    )


def count_status(raw: bytes) -> int:
    fields = raw.split(b"\0")
    index = count = 0
    while index < len(fields):
        record = fields[index]
        if not record:
            if any(fields[index + 1 :]):
                raise CollectorError("malformed porcelain-v2 status stream")
            break
        marker = record[:2]
        if marker not in {b"1 ", b"2 ", b"u ", b"? ", b"! "}:
            raise CollectorError("unsupported porcelain-v2 status record")
        count += 1
        index += 1
        if marker == b"2 ":
            if index >= len(fields) or not fields[index]:
                raise CollectorError("malformed porcelain-v2 rename record")
            index += 1
    return count


def repository_path(source_root: Path, directory: str) -> Path:
    source_root = require_directory(source_root, "source root")
    path = source_root / directory
    reject_symlinks(path, f"repository {directory!r}")
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError as exc:
        raise CollectorError(f"approved repository is missing: {directory}") from exc
    if not stat.S_ISDIR(mode):
        raise CollectorError(f"approved repository is not a directory: {directory}")
    top = decode_line(run_git(path, ["rev-parse", "--show-toplevel"]).stdout, "top-level")
    if absolute(Path(top)) != absolute(path):
        raise CollectorError(f"approved path is not the repository top-level: {directory}")
    return absolute(path)


def collect_entry(source_root: Path, entry: PolicyEntry) -> dict[str, Any]:
    repository = repository_path(source_root, entry.directory)
    origin = canonicalize_remote(
        decode_line(run_git(repository, ["remote", "get-url", "origin"]).stdout, "origin")
    )
    if origin != entry.expected_remote:
        raise CollectorError(
            f"repository {entry.id!r} origin mismatch: {origin!r} != {entry.expected_remote!r}"
        )
    head = decode_line(
        run_git(repository, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout,
        "HEAD",
    ).lower()
    if not SHA_RE.fullmatch(head):
        raise CollectorError(f"repository {entry.id!r} HEAD is not a full commit id")
    branch = current_branch(repository)
    upstream = current_upstream(repository)
    upstream_head: str | None = None
    if upstream is not None:
        upstream_head = decode_line(
            run_git(repository, ["rev-parse", "--verify", "@{upstream}^{commit}"]).stdout,
            "upstream HEAD",
        ).lower()
        if not SHA_RE.fullmatch(upstream_head):
            raise CollectorError(f"repository {entry.id!r} upstream HEAD is invalid")
    status = run_git(
        repository, ["status", "--porcelain=v2", "-z", "--untracked-files=all"]
    ).stdout
    changes = count_status(status)
    return {
        "branch": branch,
        "directory": entry.directory,
        "head": head,
        "head_state": "branch" if branch is not None else "detached",
        "id": entry.id,
        "origin": origin,
        "reference": entry.reference,
        "upstream": upstream,
        "upstream_head": upstream_head,
        "worktree": {
            "change_count": changes,
            "state": "clean" if changes == 0 else "dirty",
            "status_sha256": hashlib.sha256(status).hexdigest(),
        },
    }


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def collect(
    repo_root: Path,
    policy_relative: Path,
    source_root: Path,
    observed_at: str,
) -> dict[str, Any]:
    policy = load_policy(repo_root, policy_relative)
    body: dict[str, Any] = {
        "observed_at": normalize_observed_at(observed_at),
        "path_scope": "source-root-relative",
        "policy_sha256": policy.sha256,
        "repositories": [collect_entry(source_root, entry) for entry in policy.entries],
        "schema": OUTPUT_SCHEMA,
    }
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    body["collection_id"] = f"repository-collection-{digest[:16]}"
    return body


def render_collection(value: Mapping[str, Any]) -> bytes:
    return canonical_json(value)


def write_atomic(path: Path, data: bytes) -> None:
    output = absolute(path)
    parent = require_directory(output.parent, "output parent")
    reject_symlinks(output, "output path")
    if output.exists() and not stat.S_ISREG(os.lstat(output).st_mode):
        raise CollectorError(f"output path is not a regular file: {output}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".observation-", dir=parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        directory_descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
