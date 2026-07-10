#!/usr/bin/env python3
"""Create and verify a bounded private archive for the external Cabinet app.

The tool is deliberately separate from ``cabinet-safe-export.sh``.  The safe
export is portable and excludes private runtime data; this archive is private,
create-only and designed for preservation before runtime retirement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

SCHEMA_VERSION = 1
ARCHIVE_KIND = "private_cabinet_archive"
DEFAULT_MAX_FILE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 512 * 1024 * 1024
COPY_CHUNK_BYTES = 1024 * 1024

EXCLUDED_PATH_PARTS = frozenset(
    {
        ".git",
        ".next",
        ".venv",
        "__pycache__",
        "artifacts",
        "build",
        "cache",
        "dist",
        "external",
        "node_modules",
        "snapshots",
        "target",
        "vendor",
        "venv",
    }
)
EXCLUDED_NAME_MARKERS = (
    "_merge",
    ".bundle.",
    ".citation_map.",
    ".claim_evidence_map.",
    ".chunk_index.",
    ".diff",
    ".dump.",
    ".patch",
    ".reading_pack.",
    ".retrieval_eval.",
    ".snapshot.",
)
REPOSITORY_PRIVATE_ROOTS = (
    ".agents",
    ".cabinet-state",
    ".chat",
    ".conversations",
    ".global-agents",
    ".home",
    ".jobs",
    ".memory",
    ".messages",
    ".runtime",
    "songs",
)
APP_PRIVATE_DIR_NAMES = frozenset(
    {
        ".agents",
        ".cabinet-state",
        ".chat",
        ".conversations",
        ".global-agents",
        ".jobs",
        ".memory",
        ".messages",
        ".runtime",
        "conversations",
        "data",
        "memory",
        "messages",
        "state",
    }
)
SQLITE_NAMES = frozenset({".cabinet.db", "cabinet.db"})
SQLITE_SUFFIXES = frozenset({".db", ".sqlite", ".sqlite3"})
SQLITE_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")


class ArchiveError(RuntimeError):
    """Fail-closed error with a public-safe code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CaptureItem:
    source_class: str
    source_root: Path
    source_path: Path
    source_relative_path: PurePosixPath
    archive_path: PurePosixPath
    kind: str


@dataclass
class Discovery:
    items: list[CaptureItem]
    coverage_gaps: list[str]
    excluded_sqlite_sidecars: int = 0


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(COPY_CHUNK_BYTES):
                digest.update(chunk)
    except OSError as exc:
        raise ArchiveError("archive_read_failed") from exc
    return digest.hexdigest()


def _fingerprint(stat_result: os.stat_result) -> tuple[int, int, int, int]:
    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        stat_result.st_mtime_ns,
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolve_source_directory(
    path: Path,
    *,
    error_code: str,
    allow_missing: bool = False,
) -> Path:
    if path.is_symlink():
        raise ArchiveError(error_code)
    resolved = path.resolve(strict=False)
    if allow_missing and not path.exists():
        return resolved
    if not path.is_dir():
        raise ArchiveError(error_code)
    return resolved


def _validate_limits(max_file_bytes: int, max_total_bytes: int) -> None:
    if max_file_bytes <= 0 or max_total_bytes <= 0:
        raise ArchiveError("archive_limit_invalid")
    if max_file_bytes > max_total_bytes:
        raise ArchiveError("file_limit_exceeds_total_limit")


def _validate_absolute_create_only_destination(
    destination: Path,
    *,
    forbidden_roots: Iterable[Path],
) -> Path:
    if not destination.is_absolute():
        raise ArchiveError("destination_must_be_absolute")
    if destination.exists() or destination.is_symlink():
        raise ArchiveError("destination_must_not_exist")
    original_parent = destination.parent
    for ancestor in (original_parent, *original_parent.parents):
        if ancestor.is_symlink():
            raise ArchiveError("destination_parent_symlink_rejected")
    resolved = destination.resolve(strict=False)
    parent = resolved.parent
    if not parent.is_dir():
        raise ArchiveError("destination_parent_invalid")
    for root in forbidden_roots:
        if root.exists() and _is_relative_to(resolved, root.resolve()):
            raise ArchiveError("destination_inside_source")
    for ancestor in (parent, *parent.parents):
        if (ancestor / ".git").exists():
            raise ArchiveError("destination_inside_repository")
    return resolved


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        path_stat = path.lstat()
    except OSError as exc:
        raise ArchiveError("destination_stat_failed") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise ArchiveError("destination_identity_invalid")
    return path_stat.st_dev, path_stat.st_ino


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ArchiveError("archive_sync_failed") from exc


def _reserve_create_only_directory(path: Path) -> tuple[int, int]:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ArchiveError("destination_must_not_exist") from exc
    except OSError as exc:
        raise ArchiveError("destination_create_failed") from exc

    identity = _directory_identity(path)
    try:
        os.chmod(path, 0o700)
        marker = path / ".incomplete"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(marker, flags, 0o600), "wb", closefd=True) as handle:
            handle.write(b"incomplete\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(marker, 0o600)
        _fsync_directory(path)
        _fsync_directory(path.parent)
    except Exception:
        _cleanup_reserved_directory(path, identity)
        raise
    return identity


def _cleanup_reserved_directory(path: Path, identity: tuple[int, int]) -> None:
    try:
        if path.is_symlink() or not path.is_dir():
            return
        if _directory_identity(path) != identity:
            return
        shutil.rmtree(path)
        _fsync_directory(path.parent)
    except (ArchiveError, OSError):
        return


def _complete_reserved_directory(path: Path, identity: tuple[int, int]) -> None:
    if _directory_identity(path) != identity:
        raise ArchiveError("destination_identity_changed")
    marker = path / ".incomplete"
    try:
        marker_stat = marker.lstat()
        if stat.S_ISLNK(marker_stat.st_mode) or not stat.S_ISREG(marker_stat.st_mode):
            raise ArchiveError("archive_incomplete_marker_invalid")
        marker.unlink()
        _fsync_directory(path)
        _fsync_directory(path.parent)
    except ArchiveError:
        raise
    except OSError as exc:
        raise ArchiveError("archive_completion_failed") from exc


def _safe_relative(path: PurePosixPath) -> PurePosixPath:
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ArchiveError("unsafe_relative_path")
    return path


def _safe_archive_file(archive_root: Path, relative: PurePosixPath) -> Path:
    safe = _safe_relative(relative)
    candidate = archive_root.joinpath(*safe.parts)
    if not _is_relative_to(candidate.resolve(strict=False), archive_root.resolve()):
        raise ArchiveError("archive_path_escape")
    return candidate


def _looks_like_sqlite(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(16) == b"SQLite format 3\x00"
    except OSError as exc:
        raise ArchiveError("source_read_failed") from exc


def _is_sqlite_sidecar(path: Path) -> bool:
    lowered = path.name.lower()
    return lowered.endswith(SQLITE_SIDECAR_SUFFIXES) and (
        ".db" in lowered or ".sqlite" in lowered
    )


def _classify_regular_file(path: Path) -> str:
    if _is_sqlite_sidecar(path):
        return "sqlite_sidecar"
    lowered = path.name.lower()
    if lowered in SQLITE_NAMES or path.suffix.lower() in SQLITE_SUFFIXES:
        return "sqlite" if _looks_like_sqlite(path) else "regular"
    return "sqlite" if _looks_like_sqlite(path) else "regular"


def _capture_file(
    *,
    source_class: str,
    source_root: Path,
    source_path: Path,
    archive_prefix: PurePosixPath,
    source_relative: PurePosixPath | None = None,
) -> CaptureItem | None:
    try:
        source_stat = source_path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ArchiveError("source_stat_failed") from exc
    if stat.S_ISLNK(source_stat.st_mode):
        raise ArchiveError("source_symlink_rejected")
    if not stat.S_ISREG(source_stat.st_mode):
        raise ArchiveError("source_special_file_rejected")
    relative = source_relative or PurePosixPath(
        source_path.relative_to(source_root).as_posix()
    )
    kind = _classify_regular_file(source_path)
    if kind == "sqlite_sidecar":
        return None
    return CaptureItem(
        source_class=source_class,
        source_root=source_root,
        source_path=source_path,
        source_relative_path=_safe_relative(relative),
        archive_path=_safe_relative(archive_prefix / relative),
        kind=kind,
    )


def _walk_source_tree(
    *,
    source_class: str,
    source_root: Path,
    archive_prefix: PurePosixPath,
    max_file_bytes: int,
) -> tuple[list[CaptureItem], int]:
    try:
        root_stat = source_root.lstat()
    except FileNotFoundError:
        return [], 0
    except OSError as exc:
        raise ArchiveError("source_stat_failed") from exc
    if stat.S_ISLNK(root_stat.st_mode):
        raise ArchiveError("source_symlink_rejected")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ArchiveError("source_root_not_directory")

    items: list[CaptureItem] = []
    sidecars = 0
    for directory, dirnames, filenames in os.walk(source_root, followlinks=False):
        directory_path = Path(directory)
        dirnames.sort()
        filenames.sort()
        kept_dirs: list[str] = []
        for dirname in dirnames:
            if dirname.lower() in EXCLUDED_PATH_PARTS:
                continue
            child = directory_path / dirname
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise ArchiveError("source_stat_failed") from exc
            if stat.S_ISLNK(child_stat.st_mode):
                raise ArchiveError("source_symlink_rejected")
            if not stat.S_ISDIR(child_stat.st_mode):
                raise ArchiveError("source_special_file_rejected")
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            source_path = directory_path / filename
            try:
                source_stat = source_path.lstat()
            except OSError as exc:
                raise ArchiveError("source_stat_failed") from exc
            if stat.S_ISLNK(source_stat.st_mode):
                raise ArchiveError("source_symlink_rejected")
            if not stat.S_ISREG(source_stat.st_mode):
                raise ArchiveError("source_special_file_rejected")
            kind = _classify_regular_file(source_path)
            if kind == "sqlite_sidecar":
                sidecars += 1
                continue
            if kind != "sqlite" and source_stat.st_size > max_file_bytes:
                raise ArchiveError("selected_file_too_large")
            relative = PurePosixPath(source_path.relative_to(source_root).as_posix())
            items.append(
                CaptureItem(
                    source_class=source_class,
                    source_root=source_root,
                    source_path=source_path,
                    source_relative_path=_safe_relative(relative),
                    archive_path=_safe_relative(archive_prefix / relative),
                    kind=kind,
                )
            )
    return items, sidecars


def _path_is_excluded(relative: PurePosixPath) -> bool:
    lowered_parts = {part.lower() for part in relative.parts}
    if lowered_parts & EXCLUDED_PATH_PARTS:
        return True
    lowered_name = relative.name.lower()
    return any(marker in lowered_name for marker in EXCLUDED_NAME_MARKERS)


def _discover_git_local_files(
    repo: Path, max_file_bytes: int
) -> tuple[list[CaptureItem], list[str]]:
    git_binary = shutil.which("git")
    if git_binary is None:
        raise ArchiveError("git_inventory_unavailable")
    command_variants = (
        [
            git_binary,
            "-C",
            str(repo),
            "ls-files",
            "-z",
            "--others",
            "--exclude-standard",
        ],
        [
            git_binary,
            "-C",
            str(repo),
            "ls-files",
            "-z",
            "--others",
            "--ignored",
            "--exclude-standard",
        ],
    )
    names: set[str] = set()
    for command in command_variants:
        try:
            # The executable is resolved once and every argument is internally fixed.
            result = subprocess.run(  # noqa: S603
                command, capture_output=True, check=False
            )
        except OSError as exc:
            raise ArchiveError("git_inventory_unavailable") from exc
        if result.returncode != 0:
            return [], ["repository_local_file_inventory_unavailable"]
        names.update(os.fsdecode(item) for item in result.stdout.split(b"\0") if item)

    items: list[CaptureItem] = []
    for name in sorted(names):
        relative = PurePosixPath(name)
        if _path_is_excluded(relative):
            continue
        source = repo.joinpath(*relative.parts)
        try:
            source_stat = source.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ArchiveError("source_stat_failed") from exc
        if stat.S_ISDIR(source_stat.st_mode):
            continue
        if stat.S_ISLNK(source_stat.st_mode):
            raise ArchiveError("source_symlink_rejected")
        if not stat.S_ISREG(source_stat.st_mode):
            raise ArchiveError("source_special_file_rejected")
        kind = _classify_regular_file(source)
        if kind == "sqlite_sidecar":
            continue
        if kind != "sqlite" and source_stat.st_size > max_file_bytes:
            raise ArchiveError("selected_file_too_large")
        items.append(
            CaptureItem(
                source_class="repository_local",
                source_root=repo,
                source_path=source,
                source_relative_path=_safe_relative(relative),
                archive_path=_safe_relative(
                    PurePosixPath("payload/repository-local") / relative
                ),
                kind=kind,
            )
        )
    return items, []


def _discover_app_private_items(
    app_root: Path,
    *,
    max_file_bytes: int,
) -> tuple[list[CaptureItem], int]:
    if not app_root.exists():
        return [], 0
    if app_root.is_symlink() or not app_root.is_dir():
        raise ArchiveError("app_root_invalid")

    items: list[CaptureItem] = []
    sidecars = 0
    captured_roots: list[Path] = []
    for directory, dirnames, filenames in os.walk(app_root, followlinks=False):
        directory_path = Path(directory)
        filtered: list[str] = []
        for dirname in sorted(dirnames):
            child = directory_path / dirname
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise ArchiveError("source_stat_failed") from exc
            if stat.S_ISLNK(child_stat.st_mode):
                if dirname.lower() in {"current", "latest"}:
                    continue
                raise ArchiveError("source_symlink_rejected")
            if dirname.lower() in EXCLUDED_PATH_PARTS:
                continue
            if dirname.lower() in APP_PRIVATE_DIR_NAMES:
                captured_roots.append(child)
                continue
            filtered.append(dirname)
        dirnames[:] = filtered

        for filename in sorted(filenames):
            source = directory_path / filename
            lowered = filename.lower()
            if _is_sqlite_sidecar(source):
                sidecars += 1
                continue
            if lowered not in SQLITE_NAMES:
                continue
            relative = PurePosixPath(source.relative_to(app_root).as_posix())
            item = _capture_file(
                source_class="application_private",
                source_root=app_root,
                source_path=source,
                archive_prefix=PurePosixPath("payload/application-private"),
                source_relative=relative,
            )
            if item is not None:
                items.append(item)

    for root in sorted(captured_roots):
        relative = PurePosixPath(root.relative_to(app_root).as_posix())
        tree_items, tree_sidecars = _walk_source_tree(
            source_class="application_private",
            source_root=root,
            archive_prefix=PurePosixPath("payload/application-private") / relative,
            max_file_bytes=max_file_bytes,
        )
        sidecars += tree_sidecars
        for item in tree_items:
            items.append(
                CaptureItem(
                    source_class=item.source_class,
                    source_root=app_root,
                    source_path=item.source_path,
                    source_relative_path=relative / item.source_relative_path,
                    archive_path=item.archive_path,
                    kind=item.kind,
                )
            )
    return items, sidecars


def discover(
    *,
    home: Path,
    repo: Path,
    app_root: Path | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> Discovery:
    _validate_limits(max_file_bytes, max_total_bytes)
    home = _resolve_source_directory(home, error_code="home_root_invalid")
    repo = _resolve_source_directory(repo, error_code="repository_root_invalid")
    if not (repo / ".git").exists():
        raise ArchiveError("repository_root_invalid")
    app_root = _resolve_source_directory(
        app_root or home / ".cabinet/app",
        error_code="app_root_invalid",
        allow_missing=True,
    )

    items: list[CaptureItem] = []
    coverage_gaps: list[str] = []
    sidecars = 0

    fixed_roots = (
        (
            "runtime_config",
            home / ".config/cabinet",
            PurePosixPath("payload/runtime-config"),
        ),
        (
            "runtime_state",
            home / ".local/state/cabinet",
            PurePosixPath("payload/runtime-state"),
        ),
    )
    for source_class, root, prefix in fixed_roots:
        if not root.exists():
            coverage_gaps.append(f"{source_class}_missing")
            continue
        tree_items, tree_sidecars = _walk_source_tree(
            source_class=source_class,
            source_root=root,
            archive_prefix=prefix,
            max_file_bytes=max_file_bytes,
        )
        items.extend(tree_items)
        sidecars += tree_sidecars

    active_database = repo / ".cabinet.db"
    sidecars += sum(
        (repo / f".cabinet.db{suffix}").is_file() for suffix in SQLITE_SIDECAR_SUFFIXES
    )
    database_item = _capture_file(
        source_class="repository_private",
        source_root=repo,
        source_path=active_database,
        archive_prefix=PurePosixPath("payload/repository-private"),
    )
    if database_item is None:
        coverage_gaps.append("active_database_missing")
    else:
        items.append(database_item)

    for name in REPOSITORY_PRIVATE_ROOTS:
        root = repo / name
        if not root.exists():
            continue
        tree_items, tree_sidecars = _walk_source_tree(
            source_class="repository_private",
            source_root=root,
            archive_prefix=PurePosixPath("payload/repository-private") / name,
            max_file_bytes=max_file_bytes,
        )
        sidecars += tree_sidecars
        for item in tree_items:
            items.append(
                CaptureItem(
                    source_class=item.source_class,
                    source_root=repo,
                    source_path=item.source_path,
                    source_relative_path=PurePosixPath(name)
                    / item.source_relative_path,
                    archive_path=item.archive_path,
                    kind=item.kind,
                )
            )

    local_items, local_gaps = _discover_git_local_files(repo, max_file_bytes)
    items.extend(local_items)
    coverage_gaps.extend(local_gaps)

    app_items, app_sidecars = _discover_app_private_items(
        app_root,
        max_file_bytes=max_file_bytes,
    )
    items.extend(app_items)
    sidecars += app_sidecars
    if not app_root.exists():
        coverage_gaps.append("application_root_missing")

    deduplicated: dict[Path, CaptureItem] = {}
    archive_paths: set[PurePosixPath] = set()
    for item in items:
        try:
            source_key = item.source_path.resolve(strict=True)
        except OSError as exc:
            raise ArchiveError("source_resolution_failed") from exc
        if source_key in deduplicated:
            continue
        if item.archive_path in archive_paths:
            raise ArchiveError("archive_path_collision")
        deduplicated[source_key] = item
        archive_paths.add(item.archive_path)

    selected_items = sorted(
        deduplicated.values(), key=lambda item: item.archive_path.as_posix()
    )
    try:
        selected_bytes = sum(
            item.source_path.lstat().st_size for item in selected_items
        )
    except OSError as exc:
        raise ArchiveError("source_stat_failed") from exc
    if selected_bytes > max_total_bytes:
        raise ArchiveError("selected_total_too_large")

    return Discovery(
        items=selected_items,
        coverage_gaps=sorted(set(coverage_gaps)),
        excluded_sqlite_sidecars=sidecars,
    )


def _copy_regular_file(
    source: Path,
    destination: Path,
    *,
    max_output_bytes: int | None = None,
) -> dict[str, Any]:
    try:
        before = source.lstat()
    except OSError as exc:
        raise ArchiveError("source_stat_failed") from exc
    if stat.S_ISLNK(before.st_mode):
        raise ArchiveError("source_symlink_rejected")
    if not stat.S_ISREG(before.st_mode):
        raise ArchiveError("source_special_file_rejected")

    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination.parent, 0o700)
    digest = hashlib.sha256()
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        with (
            os.fdopen(os.open(source, flags), "rb", closefd=True) as source_handle,
            os.fdopen(
                os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                "wb",
                closefd=True,
            ) as destination_handle,
        ):
            copied_bytes = 0
            while chunk := source_handle.read(COPY_CHUNK_BYTES):
                copied_bytes += len(chunk)
                if max_output_bytes is not None and copied_bytes > max_output_bytes:
                    raise ArchiveError("selected_total_too_large")
                destination_handle.write(chunk)
                digest.update(chunk)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
            after = os.fstat(source_handle.fileno())
    except FileExistsError as exc:
        raise ArchiveError("archive_entry_exists") from exc
    except OSError as exc:
        raise ArchiveError("file_copy_failed") from exc
    if _fingerprint(before) != _fingerprint(after):
        raise ArchiveError("source_drift_detected")
    os.chmod(destination, 0o600)
    return {
        "size_bytes": after.st_size,
        "sha256": digest.hexdigest(),
        "source_mode": stat.S_IMODE(before.st_mode),
        "stored_mode": 0o600,
    }


def _sqlite_uri(path: Path) -> str:
    return f"file:{quote(str(path))}?mode=ro"


def _backup_sqlite(
    source: Path,
    destination: Path,
    *,
    max_output_bytes: int | None = None,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination.parent, 0o700)
    if destination.exists():
        raise ArchiveError("archive_entry_exists")
    try:
        source_stat = source.lstat()
        if stat.S_ISLNK(source_stat.st_mode) or not stat.S_ISREG(source_stat.st_mode):
            raise ArchiveError("sqlite_source_invalid")
        with (
            closing(
                sqlite3.connect(_sqlite_uri(source), uri=True, timeout=10)
            ) as source_connection,
            closing(sqlite3.connect(destination)) as destination_connection,
        ):
            page_size = int(source_connection.execute("PRAGMA page_size").fetchone()[0])
            page_count = int(
                source_connection.execute("PRAGMA page_count").fetchone()[0]
            )
            if (
                max_output_bytes is not None
                and page_size * page_count > max_output_bytes
            ):
                raise ArchiveError("selected_total_too_large")

            def check_backup_size(_status: int, _remaining: int, total: int) -> None:
                if (
                    max_output_bytes is not None
                    and page_size * total > max_output_bytes
                ):
                    raise ArchiveError("selected_total_too_large")

            source_connection.backup(
                destination_connection,
                pages=256,
                progress=check_backup_size,
            )
            destination_connection.commit()
            journal_mode = destination_connection.execute(
                "PRAGMA journal_mode=DELETE"
            ).fetchone()
            quick_check = destination_connection.execute(
                "PRAGMA quick_check"
            ).fetchone()
    except ArchiveError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise ArchiveError("sqlite_backup_failed") from exc
    try:
        source_after = source.lstat()
    except OSError as exc:
        raise ArchiveError("sqlite_source_stat_failed") from exc
    if (
        stat.S_ISLNK(source_after.st_mode)
        or not stat.S_ISREG(source_after.st_mode)
        or (source_after.st_dev, source_after.st_ino)
        != (source_stat.st_dev, source_stat.st_ino)
    ):
        raise ArchiveError("sqlite_source_replaced")
    if not journal_mode or str(journal_mode[0]).lower() != "delete":
        raise ArchiveError("sqlite_archive_mode_failed")
    if not quick_check or quick_check[0] != "ok":
        raise ArchiveError("sqlite_integrity_failed")
    os.chmod(destination, 0o600)
    output_size = destination.stat().st_size
    if max_output_bytes is not None and output_size > max_output_bytes:
        raise ArchiveError("selected_total_too_large")
    return {
        "size_bytes": output_size,
        "sha256": _sha256_file(destination),
        "source_mode": stat.S_IMODE(source_stat.st_mode),
        "stored_mode": 0o600,
        "database_integrity": "ok",
        "capture_method": "sqlite_online_backup",
    }


def _public_receipt(
    *,
    status: str,
    entries: list[dict[str, Any]],
    coverage_gaps: list[str],
    excluded_sqlite_sidecars: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "private_cabinet_archive_receipt",
        "status": status,
        "classification": "private_runtime_preservation",
        "scope": {
            "entries": len(entries),
            "databases": sum(entry.get("kind") == "sqlite" for entry in entries),
            "bytes": sum(int(entry.get("size_bytes", 0)) for entry in entries),
            "source_classes": sorted({str(entry["source_class"]) for entry in entries}),
        },
        "backup_status": {
            "manifest_present": status in {"exported", "verified", "restored"},
            "integrity_verified": status in {"exported", "verified", "restored"},
            "service_mutated": False,
            "live_database_method": "sqlite_online_backup",
            "excluded_live_sqlite_sidecars": excluded_sqlite_sidecars,
        },
        "coverage_gaps": sorted(set(coverage_gaps)),
        "does_not_establish": [
            "safe_service_shutdown",
            "complete_remote_consumer_coverage",
            "semantic_application_restore",
            "data_deletion_permission",
            "repository_rename_permission",
        ],
    }


def plan_archive(
    *,
    home: Path,
    repo: Path,
    app_root: Path | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    discovery = discover(
        home=home,
        repo=repo,
        app_root=app_root,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )
    entries = [
        {
            "source_class": item.source_class,
            "kind": item.kind,
            "size_bytes": item.source_path.stat().st_size,
        }
        for item in discovery.items
    ]
    receipt = _public_receipt(
        status="planned",
        entries=entries,
        coverage_gaps=discovery.coverage_gaps,
        excluded_sqlite_sidecars=discovery.excluded_sqlite_sidecars,
    )
    receipt["backup_status"]["manifest_present"] = False
    receipt["backup_status"]["integrity_verified"] = False
    return receipt


def export_archive(
    *,
    home: Path,
    repo: Path,
    destination: Path,
    app_root: Path | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    _validate_limits(max_file_bytes, max_total_bytes)
    home = _resolve_source_directory(home, error_code="home_root_invalid")
    repo = _resolve_source_directory(repo, error_code="repository_root_invalid")
    if not (repo / ".git").exists():
        raise ArchiveError("repository_root_invalid")
    resolved_app_root = _resolve_source_directory(
        app_root or home / ".cabinet/app",
        error_code="app_root_invalid",
        allow_missing=True,
    )
    destination = _validate_absolute_create_only_destination(
        destination,
        forbidden_roots=(
            home / ".config/cabinet",
            home / ".local/state/cabinet",
            repo,
            resolved_app_root,
        ),
    )
    discovery = discover(
        home=home,
        repo=repo,
        app_root=resolved_app_root,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )
    if discovery.coverage_gaps:
        raise ArchiveError("coverage_gaps_present")
    if not discovery.items:
        raise ArchiveError("no_private_data_discovered")

    old_umask = os.umask(0o077)
    identity: tuple[int, int] | None = None
    try:
        identity = _reserve_create_only_directory(destination)
        entries: list[dict[str, Any]] = []
        written_bytes = 0
        for item in discovery.items:
            target = _safe_archive_file(destination, item.archive_path)
            remaining_bytes = max_total_bytes - written_bytes
            if remaining_bytes <= 0:
                raise ArchiveError("selected_total_too_large")
            metadata = (
                _backup_sqlite(
                    item.source_path,
                    target,
                    max_output_bytes=remaining_bytes,
                )
                if item.kind == "sqlite"
                else _copy_regular_file(
                    item.source_path,
                    target,
                    max_output_bytes=remaining_bytes,
                )
            )
            written_bytes += int(metadata["size_bytes"])
            if written_bytes > max_total_bytes:
                raise ArchiveError("selected_total_too_large")
            entries.append(
                {
                    "archive_path": item.archive_path.as_posix(),
                    "source_class": item.source_class,
                    "source_relative_path": item.source_relative_path.as_posix(),
                    "kind": item.kind,
                    **metadata,
                }
            )

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "kind": ARCHIVE_KIND,
            "created_at": _utc_now(),
            "capture_policy": {
                "database": "sqlite_online_backup",
                "regular_files": "create_only_copy_with_source_drift_check",
                "symlinks": "rejected",
                "service_mutated": False,
                "application_payload": "reinstallable_payload_excluded",
            },
            "entries": entries,
            "coverage_gaps": discovery.coverage_gaps,
            "excluded_sqlite_sidecars": discovery.excluded_sqlite_sidecars,
        }
        manifest_path = destination / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(manifest_path, 0o600)
        manifest_digest = _sha256_file(manifest_path)
        digest_path = destination / "manifest.sha256"
        digest_path.write_text(manifest_digest + "\n", encoding="ascii")
        os.chmod(digest_path, 0o600)
        _fsync_tree(destination)
        verify_receipt = _verify_archive(destination, allow_incomplete=True)
        _complete_reserved_directory(destination, identity)
        verify_receipt["status"] = "exported"
        return verify_receipt
    except Exception:
        if identity is not None:
            _cleanup_reserved_directory(destination, identity)
        raise
    finally:
        os.umask(old_umask)


def _fsync_tree(root: Path) -> None:
    try:
        for directory, _, filenames in os.walk(root):
            for filename in filenames:
                path = Path(directory) / filename
                with path.open("rb") as handle:
                    os.fsync(handle.fileno())
        descriptor = os.open(root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ArchiveError("archive_sync_failed") from exc


def _load_manifest(
    archive: Path,
    *,
    allow_incomplete: bool = False,
) -> tuple[dict[str, Any], str]:
    if archive.is_symlink() or not archive.is_dir():
        raise ArchiveError("archive_root_invalid")
    incomplete = archive / ".incomplete"
    if not allow_incomplete and (incomplete.exists() or incomplete.is_symlink()):
        raise ArchiveError("archive_incomplete")
    manifest_path = archive / "manifest.json"
    digest_path = archive / "manifest.sha256"
    if manifest_path.is_symlink() or digest_path.is_symlink():
        raise ArchiveError("archive_symlink_rejected")
    try:
        expected_digest = digest_path.read_text(encoding="ascii").strip()
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveError("manifest_read_failed") from exc
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_digest:
        raise ArchiveError("manifest_digest_mismatch")
    if not isinstance(manifest, dict):
        raise ArchiveError("manifest_shape_invalid")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("kind") != ARCHIVE_KIND
    ):
        raise ArchiveError("manifest_contract_mismatch")
    return manifest, expected_digest


def _verify_archive(
    archive: Path,
    *,
    allow_incomplete: bool,
) -> dict[str, Any]:
    if archive.is_symlink():
        raise ArchiveError("archive_symlink_rejected")
    archive = archive.resolve()
    manifest, _ = _load_manifest(archive, allow_incomplete=allow_incomplete)
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ArchiveError("manifest_entries_invalid")
    expected_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ArchiveError("manifest_entry_invalid")
        relative_text = entry.get("archive_path")
        if not isinstance(relative_text, str):
            raise ArchiveError("manifest_entry_path_invalid")
        relative = _safe_relative(PurePosixPath(relative_text))
        if not relative.parts or relative.parts[0] != "payload":
            raise ArchiveError("manifest_entry_path_invalid")
        if relative_text in expected_paths:
            raise ArchiveError("manifest_entry_duplicate")
        expected_paths.add(relative_text)
        target = _safe_archive_file(archive, relative)
        try:
            target_stat = target.lstat()
        except OSError as exc:
            raise ArchiveError("archive_entry_missing") from exc
        if stat.S_ISLNK(target_stat.st_mode):
            raise ArchiveError("archive_symlink_rejected")
        if not stat.S_ISREG(target_stat.st_mode):
            raise ArchiveError("archive_entry_type_invalid")
        if stat.S_IMODE(target_stat.st_mode) & 0o077:
            raise ArchiveError("archive_permissions_too_open")
        if target_stat.st_size != entry.get("size_bytes"):
            raise ArchiveError("archive_size_mismatch")
        if _sha256_file(target) != entry.get("sha256"):
            raise ArchiveError("archive_hash_mismatch")
        if entry.get("kind") == "sqlite":
            try:
                with closing(
                    sqlite3.connect(_sqlite_uri(target), uri=True, timeout=10)
                ) as connection:
                    quick_check = connection.execute("PRAGMA quick_check").fetchone()
            except sqlite3.Error as exc:
                raise ArchiveError("archive_sqlite_read_failed") from exc
            if not quick_check or quick_check[0] != "ok":
                raise ArchiveError("archive_sqlite_integrity_failed")

    actual_payload_files: set[str] = set()
    payload = archive / "payload"
    if payload.exists():
        for directory, dirnames, filenames in os.walk(payload, followlinks=False):
            directory_path = Path(directory)
            if stat.S_IMODE(directory_path.stat().st_mode) & 0o077:
                raise ArchiveError("archive_permissions_too_open")
            for dirname in dirnames:
                child = directory_path / dirname
                if child.is_symlink():
                    raise ArchiveError("archive_symlink_rejected")
                if stat.S_IMODE(child.stat().st_mode) & 0o077:
                    raise ArchiveError("archive_permissions_too_open")
            for filename in filenames:
                child = directory_path / filename
                if child.is_symlink():
                    raise ArchiveError("archive_symlink_rejected")
                actual_payload_files.add(child.relative_to(archive).as_posix())
    if actual_payload_files != expected_paths:
        raise ArchiveError("archive_payload_set_mismatch")

    for metadata_name in ("manifest.json", "manifest.sha256"):
        mode = stat.S_IMODE((archive / metadata_name).stat().st_mode)
        if mode & 0o077:
            raise ArchiveError("archive_permissions_too_open")
    if stat.S_IMODE(archive.stat().st_mode) & 0o077:
        raise ArchiveError("archive_permissions_too_open")

    return _public_receipt(
        status="verified",
        entries=entries,
        coverage_gaps=list(manifest.get("coverage_gaps") or []),
        excluded_sqlite_sidecars=int(manifest.get("excluded_sqlite_sidecars") or 0),
    )


def verify_archive(archive: Path) -> dict[str, Any]:
    return _verify_archive(archive, allow_incomplete=False)


def restore_archive(*, archive: Path, target: Path) -> dict[str, Any]:
    if archive.is_symlink():
        raise ArchiveError("archive_symlink_rejected")
    archive = archive.resolve()
    receipt = verify_archive(archive)
    manifest, _ = _load_manifest(archive)
    target = _validate_absolute_create_only_destination(
        target, forbidden_roots=(archive,)
    )
    old_umask = os.umask(0o077)
    identity: tuple[int, int] | None = None
    try:
        identity = _reserve_create_only_directory(target)
        for entry in manifest["entries"]:
            relative = _safe_relative(PurePosixPath(entry["archive_path"]))
            source = _safe_archive_file(archive, relative)
            restored_relative = PurePosixPath(*relative.parts[1:])
            destination = _safe_archive_file(target, restored_relative)
            copied = _copy_regular_file(source, destination)
            if copied["sha256"] != entry["sha256"]:
                raise ArchiveError("restore_hash_mismatch")
            if entry.get("kind") == "sqlite":
                try:
                    with closing(
                        sqlite3.connect(_sqlite_uri(destination), uri=True, timeout=10)
                    ) as connection:
                        quick_check = connection.execute(
                            "PRAGMA quick_check"
                        ).fetchone()
                except sqlite3.Error as exc:
                    raise ArchiveError("restore_sqlite_read_failed") from exc
                if not quick_check or quick_check[0] != "ok":
                    raise ArchiveError("restore_sqlite_integrity_failed")
        restore_manifest = {
            "schema_version": SCHEMA_VERSION,
            "kind": "private_cabinet_isolated_restore",
            "created_at": _utc_now(),
            "source_manifest_verified": True,
            "entries": len(manifest["entries"]),
            "semantic_application_restore_established": False,
        }
        restore_manifest_path = target / "restore-verification.json"
        restore_manifest_path.write_text(
            json.dumps(restore_manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        os.chmod(restore_manifest_path, 0o600)
        _fsync_tree(target)
        _complete_reserved_directory(target, identity)
        receipt["status"] = "restored"
        return receipt
    except Exception:
        if identity is not None:
            _cleanup_reserved_directory(target, identity)
        raise
    finally:
        os.umask(old_umask)


def _path_argument(value: str) -> Path:
    return Path(value).expanduser()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("plan", "export"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--home", required=True, type=_path_argument)
        subparser.add_argument("--repo", required=True, type=_path_argument)
        subparser.add_argument("--app-root", type=_path_argument)
        subparser.add_argument(
            "--max-file-bytes",
            type=int,
            default=DEFAULT_MAX_FILE_BYTES,
        )
        subparser.add_argument(
            "--max-total-bytes",
            type=int,
            default=DEFAULT_MAX_TOTAL_BYTES,
        )
        if command == "export":
            subparser.add_argument("--destination", required=True, type=_path_argument)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--archive", required=True, type=_path_argument)

    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("--archive", required=True, type=_path_argument)
    restore_parser.add_argument("--target", required=True, type=_path_argument)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            receipt = plan_archive(
                home=args.home,
                repo=args.repo,
                app_root=args.app_root,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
            )
        elif args.command == "export":
            receipt = export_archive(
                home=args.home,
                repo=args.repo,
                app_root=args.app_root,
                destination=args.destination,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
            )
        elif args.command == "verify":
            receipt = verify_archive(args.archive)
        else:
            receipt = restore_archive(archive=args.archive, target=args.target)
    except ArchiveError as exc:
        error_code = exc.code
    except Exception:
        error_code = "unexpected_failure"
    else:
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "kind": "private_cabinet_archive_receipt",
                "status": "error",
                "error_code": error_code,
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
