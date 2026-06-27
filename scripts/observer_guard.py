"""Git-index and execution guard for local repository observations."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import repository_observer as observer


class ObserverGuardError(observer.CollectorError):
    """Raised when an observation input or execution context is unsafe."""


@dataclass(frozen=True)
class IndexEntry:
    path: str
    object_id: str
    mode: str
    stage: str


_GIT_ROUTING_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_EXEC_PATH",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
}
_SAFE_GIT_CONFIG = (
    ("core.fsmonitor", "false"),
    ("core.untrackedCache", "false"),
    ("submodule.recurse", "false"),
    ("diff.ignoreSubmodules", "all"),
)


def install_safe_git_environment() -> None:
    """Remove ambient Git routing and install deterministic local overrides."""
    for key in list(os.environ):
        if key in _GIT_ROUTING_VARIABLES:
            os.environ.pop(key, None)
        elif key == "GIT_CONFIG_COUNT":
            os.environ.pop(key, None)
        elif key.startswith("GIT_CONFIG_KEY_") or key.startswith("GIT_CONFIG_VALUE_"):
            os.environ.pop(key, None)
    os.environ.pop("GIT_CONFIG_SYSTEM", None)
    os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
    os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
    os.environ["GIT_CONFIG_COUNT"] = str(len(_SAFE_GIT_CONFIG))
    for index, (key, value) in enumerate(_SAFE_GIT_CONFIG):
        os.environ[f"GIT_CONFIG_KEY_{index}"] = key
        os.environ[f"GIT_CONFIG_VALUE_{index}"] = value


def require_external_output_path(
    output: Path,
    repo_root: Path,
    source_root: Path,
) -> None:
    """Prevent observer output from mutating Cabinet or a source repository tree."""
    output_path = observer.absolute(output)
    for label, root in (
        ("Cabinet repository", observer.absolute(repo_root)),
        ("repository source root", observer.absolute(source_root)),
    ):
        if output_path == root or output_path.is_relative_to(root):
            raise ObserverGuardError(
                f"output path must be outside {label}: {output_path}"
            )


def run_git(repo_root: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=observer.git_env(),
        )
    except FileNotFoundError as exc:
        raise ObserverGuardError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ObserverGuardError(
            f"git {' '.join(arguments)} failed: {detail}"
        ) from exc
    return completed.stdout


def index_entry(repo_root: Path, relative: Path, label: str) -> IndexEntry:
    observer.safe_relative(relative, label)
    raw_path = relative.as_posix()
    if any(character in raw_path for character in ("\x00", "\n", "\r")):
        raise ObserverGuardError(f"{label} contains an unsafe path character")
    raw = run_git(
        repo_root,
        "ls-files",
        "-s",
        "-z",
        "--error-unmatch",
        "--",
        f":(literal){raw_path}",
    )
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        raise ObserverGuardError(
            f"{label} must resolve to exactly one Git index entry"
        )
    try:
        metadata, encoded_path = entries[0].split(b"\t", 1)
        mode, object_id, stage = metadata.split(b" ", 2)
        entry = IndexEntry(
            path=encoded_path.decode("utf-8"),
            object_id=object_id.decode("ascii"),
            mode=mode.decode("ascii"),
            stage=stage.decode("ascii"),
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise ObserverGuardError(f"malformed Git index entry for {label}") from exc
    if entry.path != raw_path:
        raise ObserverGuardError(
            f"{label} Git index path mismatch: {entry.path!r} != {raw_path!r}"
        )
    if entry.mode not in {"100644", "100755"} or entry.stage != "0":
        raise ObserverGuardError(
            f"{label} must be a regular Git blob at stage 0; "
            f"found mode {entry.mode}, stage {entry.stage}"
        )
    return entry


def require_index_identical(
    repo_root: Path,
    relative: Path,
    label: str,
) -> None:
    entry = index_entry(repo_root, relative, label)
    working_path = observer.require_file(repo_root, relative, label)
    working_bytes = working_path.read_bytes()
    indexed_bytes = run_git(repo_root, "cat-file", "blob", entry.object_id)
    if working_bytes != indexed_bytes:
        raise ObserverGuardError(
            f"{label} differs from its indexed Git blob: {relative.as_posix()}"
        )


def require_strict_remote(remote: str, label: str) -> None:
    canonical = observer.canonicalize_remote(remote)
    path = canonical.removeprefix("github.com:")
    components = path.split("/")
    if len(components) != 2 or any(
        component in {"", ".", ".."} for component in components
    ):
        raise ObserverGuardError(f"{label} contains an unsafe remote path")


def load_verified_policy(
    repo_root: Path,
    policy_relative: Path,
) -> observer.Policy:
    repo_root = observer.require_directory(repo_root, "repository root")
    policy = observer.load_policy(repo_root, policy_relative)
    require_index_identical(
        repo_root,
        policy_relative,
        "versioned observation policy",
    )
    for entry in policy.entries:
        require_strict_remote(
            entry.expected_remote,
            f"repository {entry.id!r} expected remote",
        )
        require_index_identical(
            repo_root,
            Path(entry.reference),
            f"repository {entry.id!r} versioned reference",
        )
    return policy
