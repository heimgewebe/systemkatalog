"""Raw origin verification for Repository Observer v1."""

from __future__ import annotations

from pathlib import Path

import observer_guard
import repository_observer as observer


def require_expected_origin(
    source_root: Path,
    entry: observer.PolicyEntry,
) -> None:
    repository = observer.repository_path(source_root, entry.directory)
    raw_origin = observer.decode_line(
        observer.run_git(
            repository,
            ["config", "--local", "--get", "remote.origin.url"],
        ).stdout,
        "raw origin",
    )
    canonical = observer.canonicalize_remote(raw_origin)
    observer_guard.require_strict_remote(
        canonical,
        f"repository {entry.id!r} raw origin",
    )
    if canonical != entry.expected_remote:
        raise observer.CollectorError(
            f"repository {entry.id!r} raw origin mismatch: "
            f"{canonical!r} != {entry.expected_remote!r}"
        )
