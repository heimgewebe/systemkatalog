#!/usr/bin/env python3
"""Hand a verified private Cabinet archive to an encrypted Restic repository.

The command has an explicit read-only ``plan`` mode and a separately gated
``execute`` mode. Plaintext staging is allowed only on tmpfs; the only
persistent copy is the encrypted Restic snapshot. The tool never runs Restic
retention commands and never mutates the Cabinet service or source data.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import private_cabinet_archive as archive  # noqa: E402

SCHEMA_VERSION = 1
RECEIPT_KIND = "private_cabinet_restic_handoff_receipt"
EXECUTION_CONFIRMATION = "CREATE_PRIVATE_CABINET_RESTIC_SNAPSHOT_AND_VERIFY"
DEFAULT_TMPFS_ROOT = Path("/dev/shm")  # noqa: S108 - intentional RAM-backed staging
DEFAULT_RESTIC_BINARY = Path("/usr/bin/restic")
DEFAULT_HOST = "cabinet-migration"
MIN_FREE_MULTIPLIER = 3
SNAPSHOT_ID_RE = re.compile(r"^[0-9a-f]{64}$")
SNAPSHOT_SUMMARY_ID_RE = re.compile(r"^[0-9a-f]{8,64}$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")


class HandoffError(RuntimeError):
    """Fail-closed error carrying only public-safe metadata."""

    def __init__(
        self,
        code: str,
        *,
        snapshot_may_exist: bool = False,
        snapshot_id_sha256: str | None = None,
        staging_cleanup_required: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.snapshot_may_exist = snapshot_may_exist
        self.snapshot_id_sha256 = snapshot_id_sha256
        self.staging_cleanup_required = staging_cleanup_required


@dataclass(frozen=True)
class StageIdentity:
    device: int
    inode: int


@dataclass(frozen=True)
class ResticContext:
    binary: Path
    password_file: Path
    binary_identity: tuple[int, ...]
    password_identity: tuple[int, ...]
    environment: dict[str, str]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise HandoffError("manifest_read_failed") from exc
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _owner_only_regular_file(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and metadata.st_uid == os.geteuid()
        and stat.S_IMODE(metadata.st_mode) & 0o077 == 0
        and metadata.st_size > 0
    )


def _file_identity(path: Path) -> tuple[int, ...]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise HandoffError("restic_file_identity_failed") from exc
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        metadata.st_mode,
        metadata.st_uid,
    )


def _restic_context(restic_binary: Path) -> ResticContext:
    if not restic_binary.is_absolute():
        raise HandoffError("restic_binary_must_be_absolute")
    if restic_binary.is_symlink() or not restic_binary.is_file():
        raise HandoffError("restic_binary_invalid")
    if not os.access(restic_binary, os.X_OK):
        raise HandoffError("restic_binary_not_executable")

    repository = os.environ.get("RESTIC_REPOSITORY", "")
    password_file_text = os.environ.get("RESTIC_PASSWORD_FILE", "")
    if not repository:
        raise HandoffError("restic_repository_missing")
    if os.environ.get("RESTIC_REPOSITORY_FILE"):
        raise HandoffError("restic_repository_file_rejected")
    if os.environ.get("RESTIC_PASSWORD"):
        raise HandoffError("inline_restic_password_rejected")
    if os.environ.get("RESTIC_PASSWORD_COMMAND"):
        raise HandoffError("restic_password_command_rejected")
    if not password_file_text:
        raise HandoffError("restic_password_file_missing")
    password_file = Path(password_file_text).expanduser()
    if not password_file.is_absolute():
        raise HandoffError("restic_password_file_invalid")
    for ancestor in (password_file.parent, *password_file.parent.parents):
        if ancestor.is_symlink():
            raise HandoffError("restic_password_parent_symlink_rejected")
    try:
        password_file = password_file.resolve(strict=True)
    except OSError as exc:
        raise HandoffError("restic_password_file_invalid") from exc
    if not _owner_only_regular_file(password_file):
        raise HandoffError("restic_password_file_invalid")

    environment = dict(os.environ)
    environment.pop("RESTIC_PASSWORD", None)
    environment["RESTIC_PASSWORD_FILE"] = str(password_file)
    return ResticContext(
        binary=restic_binary,
        password_file=password_file,
        binary_identity=_file_identity(restic_binary),
        password_identity=_file_identity(password_file),
        environment=environment,
    )


def _context_with_tmpdir(context: ResticContext, tmpdir: Path) -> ResticContext:
    if tmpdir.is_symlink() or not tmpdir.is_dir():
        raise HandoffError("restic_tmpdir_invalid")
    metadata = tmpdir.stat()
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise HandoffError("restic_tmpdir_permissions_invalid")
    environment = dict(context.environment)
    environment["TMPDIR"] = str(tmpdir)
    return ResticContext(
        binary=context.binary,
        password_file=context.password_file,
        binary_identity=context.binary_identity,
        password_identity=context.password_identity,
        environment=environment,
    )


@contextmanager
def _temporary_process_tmpdir(tmpdir: Path) -> Iterator[None]:
    if tmpdir.is_symlink() or not tmpdir.is_dir():
        raise HandoffError("process_tmpdir_invalid")
    metadata = tmpdir.stat()
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise HandoffError("process_tmpdir_permissions_invalid")
    keys = ("TMPDIR", "TEMP", "TMP", "SQLITE_TMPDIR")
    previous = {key: os.environ.get(key) for key in keys}
    previous_tempdir = tempfile.tempdir
    try:
        for key in keys:
            os.environ[key] = str(tmpdir)
        tempfile.tempdir = None
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        tempfile.tempdir = previous_tempdir


def _disable_core_dumps() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (OSError, ValueError) as exc:
        raise HandoffError("core_dump_disable_failed") from exc


def _run_restic(
    context: ResticContext,
    arguments: list[str],
    *,
    read_only: bool,
    timeout_seconds: int = 120,
) -> subprocess.CompletedProcess[str]:
    if _file_identity(context.binary) != context.binary_identity:
        raise HandoffError("restic_binary_changed")
    if _file_identity(
        context.password_file
    ) != context.password_identity or not _owner_only_regular_file(
        context.password_file
    ):
        raise HandoffError("restic_password_file_changed")
    prefix = [str(context.binary), "--no-cache"]
    if read_only:
        prefix.append("--no-lock")
    try:
        return subprocess.run(  # noqa: S603
            [*prefix, *arguments],
            check=False,
            capture_output=True,
            text=True,
            env=context.environment,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HandoffError("restic_command_failed") from exc


def _filesystem_type(path: Path) -> str:
    findmnt = shutil.which("findmnt")
    if findmnt is None:
        raise HandoffError("filesystem_probe_unavailable")
    try:
        result = subprocess.run(  # noqa: S603
            [findmnt, "-no", "FSTYPE", "--target", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HandoffError("filesystem_probe_failed") from exc
    if result.returncode != 0:
        raise HandoffError("filesystem_probe_failed")
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""


def _active_swap_is_safe() -> bool:
    swapon = shutil.which("swapon")
    lsblk = shutil.which("lsblk")
    if swapon is None or lsblk is None:
        raise HandoffError("swap_probe_unavailable")
    try:
        swaps = subprocess.run(  # noqa: S603
            [swapon, "--show=NAME", "--noheadings", "--raw"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HandoffError("swap_probe_failed") from exc
    if swaps.returncode != 0:
        raise HandoffError("swap_probe_failed")
    devices = [line.strip() for line in swaps.stdout.splitlines() if line.strip()]
    if not devices:
        return True
    for device in devices:
        if Path(device).name.startswith("zram"):
            continue
        try:
            probe = subprocess.run(  # noqa: S603
                [lsblk, "-no", "TYPE", device],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HandoffError("swap_probe_failed") from exc
        if probe.returncode != 0 or "crypt" not in probe.stdout.split():
            return False
    return True


def _validate_tmpfs(tmpfs_root: Path, max_total_bytes: int) -> dict[str, Any]:
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise HandoffError("safe_staging_cleanup_unavailable")
    if not tmpfs_root.is_absolute():
        raise HandoffError("tmpfs_root_must_be_absolute")
    if tmpfs_root.is_symlink() or not tmpfs_root.is_dir():
        raise HandoffError("tmpfs_root_invalid")
    resolved = tmpfs_root.resolve()
    if _filesystem_type(resolved) != "tmpfs":
        raise HandoffError("staging_not_tmpfs")
    if not _active_swap_is_safe():
        raise HandoffError("unencrypted_swap_active")
    try:
        stats = os.statvfs(resolved)
    except OSError as exc:
        raise HandoffError("tmpfs_capacity_probe_failed") from exc
    free_bytes = stats.f_bavail * stats.f_frsize
    required_bytes = max_total_bytes * MIN_FREE_MULTIPLIER
    if free_bytes < required_bytes:
        raise HandoffError("tmpfs_capacity_insufficient")
    return {
        "filesystem": "tmpfs",
        "swap_policy": "none_or_encrypted",
        "capacity_sufficient": True,
    }


def _snapshot_count_bucket(count: int) -> str:
    if count <= 0:
        return "zero"
    if count < 10:
        return "single_digit"
    if count < 100:
        return "double_digit"
    return "large"


def _restic_snapshot_ids_for_tag(
    context: ResticContext,
    tag: str,
) -> list[str]:
    result = _run_restic(
        context,
        ["snapshots", "--tag", tag, "--json"],
        read_only=True,
    )
    if result.returncode != 0:
        raise HandoffError("restic_tag_probe_failed")
    try:
        snapshots = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HandoffError("restic_tag_response_invalid") from exc
    if not isinstance(snapshots, list):
        raise HandoffError("restic_tag_response_invalid")
    identifiers: list[str] = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            raise HandoffError("restic_tag_response_invalid")
        identifier = snapshot.get("id")
        if not isinstance(identifier, str) or not SNAPSHOT_ID_RE.fullmatch(
            identifier.lower()
        ):
            raise HandoffError("restic_tag_response_invalid")
        identifiers.append(identifier.lower())
    return sorted(identifiers)


def _restic_tag_is_unused(context: ResticContext, tag: str) -> bool:
    return not _restic_snapshot_ids_for_tag(context, tag)


def _restic_read_probe(context: ResticContext) -> dict[str, Any]:
    result = _run_restic(context, ["snapshots", "--json"], read_only=True)
    if result.returncode != 0:
        raise HandoffError("restic_repository_unavailable")
    try:
        snapshots = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HandoffError("restic_snapshot_response_invalid") from exc
    if not isinstance(snapshots, list):
        raise HandoffError("restic_snapshot_response_invalid")
    return {
        "accessible": True,
        "encrypted_repository": True,
        "snapshot_count_bucket": _snapshot_count_bucket(len(snapshots)),
    }


def _public_receipt(
    *,
    status: str,
    archive_receipt: dict[str, Any],
    restic: dict[str, Any],
    staging: dict[str, Any],
    snapshot_id: str | None = None,
    tag: str | None = None,
    staging_removed: bool = False,
    staging_created: bool = False,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": RECEIPT_KIND,
        "status": status,
        "classification": "private_runtime_preservation",
        "archive_scope": archive_receipt.get("scope", {}),
        "archive_integrity": {
            "manifest_present": bool(
                archive_receipt.get("backup_status", {}).get("manifest_present")
            ),
            "verified": bool(
                archive_receipt.get("backup_status", {}).get("integrity_verified")
            ),
            "live_database_method": archive_receipt.get("backup_status", {}).get(
                "live_database_method"
            ),
        },
        "restic": restic,
        "staging": {
            **staging,
            "persistent_plaintext": False,
            "created": staging_created,
            "removed": staging_removed,
        },
        "service_mutated": False,
        "retention_mutated": False,
        "coverage_gaps": list(archive_receipt.get("coverage_gaps") or []),
        "does_not_establish": [
            "safe_service_shutdown",
            "complete_remote_consumer_coverage",
            "semantic_application_restore",
            "data_deletion_permission",
            "repository_rename_permission",
        ],
    }
    if snapshot_id is not None:
        receipt["snapshot"] = {
            "created": True,
            "id_sha256": _sha256_text(snapshot_id),
            "tag_sha256": _sha256_text(tag or ""),
            "exact_restore_verified": status == "snapshot_verified",
            "locator": "unique_precommitted_tag",
        }
    return receipt


def plan_handoff(
    *,
    home: Path,
    repo: Path,
    app_root: Path | None,
    tmpfs_root: Path,
    restic_binary: Path,
    max_file_bytes: int,
    max_total_bytes: int,
) -> dict[str, Any]:
    staging = _validate_tmpfs(tmpfs_root, max_total_bytes)
    context = _restic_context(restic_binary)
    restic = _restic_read_probe(context)
    archive_receipt = archive.plan_archive(
        home=home,
        repo=repo,
        app_root=app_root,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )
    status = "ready" if not archive_receipt.get("coverage_gaps") else "blocked"
    return _public_receipt(
        status=status,
        archive_receipt=archive_receipt,
        restic=restic,
        staging=staging,
    )


def _stage_identity(path: Path) -> StageIdentity:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise HandoffError("staging_identity_failed") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise HandoffError("staging_identity_invalid")
    return StageIdentity(metadata.st_dev, metadata.st_ino)


def _create_stage(tmpfs_root: Path) -> tuple[Path, StageIdentity]:
    old_umask = os.umask(0o077)
    path: Path | None = None
    try:
        path = Path(tempfile.mkdtemp(prefix="cabinet-private-restic-", dir=tmpfs_root))
        os.chmod(path, 0o700)
        identity = _stage_identity(path)
    except (OSError, HandoffError) as exc:
        cleanup_failed = False
        if path is not None:
            try:
                path.rmdir()
            except OSError:
                cleanup_failed = True
        if cleanup_failed:
            raise HandoffError(
                "staging_create_cleanup_failed",
                staging_cleanup_required=True,
            ) from exc
        if isinstance(exc, HandoffError):
            raise
        raise HandoffError("staging_create_failed") from exc
    finally:
        os.umask(old_umask)
    return path, identity


def _remove_stage(path: Path, root: Path, identity: StageIdentity) -> bool:
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        return False
    try:
        if path.is_symlink() or not path.is_dir():
            return False
        if not _is_relative_to(path.resolve(), root.resolve()):
            return False
        current = _stage_identity(path)
        if current != identity:
            return False
        shutil.rmtree(path)
        return not path.exists()
    except (OSError, HandoffError):
        return False


def _parse_snapshot_summary_id(output: str) -> str:
    candidates: list[str] = []
    for line in output.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or record.get("message_type") != "summary":
            continue
        candidate = record.get("snapshot_id")
        if not isinstance(candidate, str):
            raise HandoffError("restic_snapshot_id_invalid")
        normalized = candidate.lower()
        if not SNAPSHOT_SUMMARY_ID_RE.fullmatch(normalized):
            raise HandoffError("restic_snapshot_id_invalid")
        candidates.append(normalized)
    unique = sorted(set(candidates))
    if not unique:
        raise HandoffError("restic_snapshot_id_missing")
    if len(unique) != 1:
        raise HandoffError("restic_snapshot_id_ambiguous")
    return unique[0]


def _resolve_full_snapshot_id(
    summary_snapshot_id: str,
    tagged_snapshot_ids: list[str],
) -> str:
    if len(tagged_snapshot_ids) != 1:
        raise HandoffError("snapshot_tag_binding_failed")
    snapshot_id = tagged_snapshot_ids[0]
    if not SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise HandoffError("snapshot_tag_binding_failed")
    if not snapshot_id.startswith(summary_snapshot_id):
        raise HandoffError("snapshot_summary_id_mismatch")
    return snapshot_id


def _validate_tag(tag: str) -> None:
    if not TAG_RE.fullmatch(tag):
        raise HandoffError("snapshot_tag_invalid")


def _find_restored_archive(restore_root: Path) -> Path:
    if restore_root.is_symlink() or not restore_root.is_dir():
        raise HandoffError("restore_root_invalid")
    resolved_root = restore_root.resolve()
    candidates: list[Path] = []
    for directory, dirnames, filenames in os.walk(restore_root, followlinks=False):
        directory_path = Path(directory)
        for dirname in sorted(dirnames):
            if (directory_path / dirname).is_symlink():
                raise HandoffError("restored_archive_symlink_rejected")
        for filename in filenames:
            if (directory_path / filename).is_symlink():
                raise HandoffError("restored_archive_symlink_rejected")
        if (
            "manifest.json" in filenames
            and (directory_path / "manifest.sha256").is_file()
            and (directory_path / "payload").is_dir()
        ):
            candidates.append(directory_path)
    if len(candidates) != 1:
        raise HandoffError("restored_archive_ambiguous")
    candidate = candidates[0]
    if not _is_relative_to(candidate.resolve(), resolved_root):
        raise HandoffError("restored_archive_invalid")
    return candidate


@contextmanager
def _exclusive_execution_lock(tmpfs_root: Path) -> Iterator[None]:
    if _filesystem_type(tmpfs_root) != "tmpfs":
        raise HandoffError("execution_lock_not_tmpfs")
    lock_path = tmpfs_root / ".cabinet-private-restic-handoff.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    locked = False
    try:
        descriptor = os.open(lock_path, flags, 0o600)
        metadata = os.fstat(descriptor)
        root_metadata = tmpfs_root.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) & 0o077
            or metadata.st_nlink != 1
            or metadata.st_dev != root_metadata.st_dev
        ):
            raise HandoffError("execution_lock_invalid")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HandoffError("handoff_already_running") from exc
        locked = True
        yield
    except HandoffError:
        raise
    except OSError as exc:
        raise HandoffError("execution_lock_failed") from exc
    finally:
        if descriptor is not None:
            if locked:
                with suppress(OSError):
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def _execute_handoff_locked(
    *,
    home: Path,
    repo: Path,
    app_root: Path | None,
    tmpfs_root: Path,
    restic_binary: Path,
    max_file_bytes: int,
    max_total_bytes: int,
    tag: str,
    host: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    context = _restic_context(restic_binary)
    if not _restic_tag_is_unused(context, tag):
        raise HandoffError("snapshot_tag_already_exists")
    stage_root, identity = _create_stage(tmpfs_root.resolve())
    snapshot_id: str | None = None
    snapshot_was_created = False
    result_receipt: dict[str, Any] | None = None
    pending_error: Exception | None = None
    try:
        restic_tmpdir = stage_root / "restic-tmp"
        restic_tmpdir.mkdir(mode=0o700)
        process_tmpdir = stage_root / "process-tmp"
        process_tmpdir.mkdir(mode=0o700)
        context = _context_with_tmpdir(context, restic_tmpdir)
        with _temporary_process_tmpdir(process_tmpdir):
            archive_root = stage_root / "archive"
            archive.export_archive(
                home=home,
                repo=repo,
                app_root=app_root,
                destination=archive_root,
                max_file_bytes=max_file_bytes,
                max_total_bytes=max_total_bytes,
            )
            original_manifest_sha256 = _sha256_file(archive_root / "manifest.json")
            try:
                backup = _run_restic(
                    context,
                    [
                        "backup",
                        "--json",
                        "--host",
                        host,
                        "--tag",
                        tag,
                        str(archive_root),
                    ],
                    read_only=False,
                    timeout_seconds=900,
                )
            except HandoffError as exc:
                if exc.code == "restic_command_failed":
                    raise HandoffError(exc.code, snapshot_may_exist=True) from exc
                raise
            snapshot_was_created = True
            if backup.returncode != 0:
                raise HandoffError("restic_backup_failed", snapshot_may_exist=True)
            try:
                summary_snapshot_id = _parse_snapshot_summary_id(backup.stdout)
            except HandoffError as exc:
                raise HandoffError(exc.code, snapshot_may_exist=True) from exc
            try:
                tagged_snapshot_ids = _restic_snapshot_ids_for_tag(context, tag)
                snapshot_id = _resolve_full_snapshot_id(
                    summary_snapshot_id,
                    tagged_snapshot_ids,
                )
            except HandoffError as exc:
                raise HandoffError(
                    exc.code,
                    snapshot_may_exist=True,
                    snapshot_id_sha256=(
                        _sha256_text(summary_snapshot_id)
                        if SNAPSHOT_ID_RE.fullmatch(summary_snapshot_id)
                        else None
                    ),
                ) from exc

            restore_root = stage_root / "restored"
            restore_root.mkdir(mode=0o700)
            restore = _run_restic(
                context,
                ["restore", snapshot_id, "--target", str(restore_root)],
                read_only=False,
                timeout_seconds=900,
            )
            if restore.returncode != 0:
                raise HandoffError("restic_restore_failed", snapshot_may_exist=True)
            restored_archive = _find_restored_archive(restore_root)
            restored_manifest_sha256 = _sha256_file(restored_archive / "manifest.json")
            if restored_manifest_sha256 != original_manifest_sha256:
                raise HandoffError(
                    "restored_manifest_mismatch", snapshot_may_exist=True
                )
            restored_receipt = archive.verify_archive(restored_archive)
            result_receipt = _public_receipt(
                status="snapshot_verified",
                archive_receipt=restored_receipt,
                restic={
                    "accessible": True,
                    "encrypted_repository": True,
                    "snapshot_count_bucket": plan["restic"]["snapshot_count_bucket"],
                },
                staging={
                    "filesystem": "tmpfs",
                    "swap_policy": "none_or_encrypted",
                    "capacity_sufficient": True,
                },
                snapshot_id=snapshot_id,
                tag=tag,
                staging_created=True,
            )
    except Exception as exc:
        pending_error = exc
    cleaned = _remove_stage(stage_root, tmpfs_root.resolve(), identity)
    if not cleaned:
        raise HandoffError(
            "staging_cleanup_failed",
            snapshot_may_exist=snapshot_was_created,
            snapshot_id_sha256=(
                _sha256_text(snapshot_id) if snapshot_id is not None else None
            ),
            staging_cleanup_required=True,
        )
    if pending_error is not None:
        if isinstance(pending_error, HandoffError):
            raise HandoffError(
                pending_error.code,
                snapshot_may_exist=pending_error.snapshot_may_exist
                or snapshot_was_created,
                snapshot_id_sha256=(
                    pending_error.snapshot_id_sha256
                    or (_sha256_text(snapshot_id) if snapshot_id is not None else None)
                ),
                staging_cleanup_required=False,
            ) from pending_error
        if isinstance(pending_error, archive.ArchiveError):
            raise HandoffError(
                f"archive_{pending_error.code}",
                snapshot_may_exist=snapshot_was_created,
                snapshot_id_sha256=(
                    _sha256_text(snapshot_id) if snapshot_id is not None else None
                ),
            ) from pending_error
        raise HandoffError(
            "unexpected_failure",
            snapshot_may_exist=snapshot_was_created,
            snapshot_id_sha256=(
                _sha256_text(snapshot_id) if snapshot_id is not None else None
            ),
        ) from pending_error
    if result_receipt is None:
        raise HandoffError(
            "unexpected_failure",
            snapshot_may_exist=snapshot_was_created,
            snapshot_id_sha256=(
                _sha256_text(snapshot_id) if snapshot_id is not None else None
            ),
        )
    result_receipt["staging"]["removed"] = True
    return result_receipt


def execute_handoff(
    *,
    home: Path,
    repo: Path,
    app_root: Path | None,
    tmpfs_root: Path,
    restic_binary: Path,
    max_file_bytes: int,
    max_total_bytes: int,
    confirmation: str,
    tag: str,
    host: str = DEFAULT_HOST,
) -> dict[str, Any]:
    if confirmation != EXECUTION_CONFIRMATION:
        raise HandoffError("execution_confirmation_missing")
    _disable_core_dumps()
    _validate_tag(tag)
    if not TAG_RE.fullmatch(host):
        raise HandoffError("restic_host_invalid")

    plan = plan_handoff(
        home=home,
        repo=repo,
        app_root=app_root,
        tmpfs_root=tmpfs_root,
        restic_binary=restic_binary,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )
    if plan["status"] != "ready":
        raise HandoffError("handoff_plan_blocked")

    with _exclusive_execution_lock(tmpfs_root.resolve()):
        _validate_tmpfs(tmpfs_root.resolve(), max_total_bytes)
        return _execute_handoff_locked(
            home=home,
            repo=repo,
            app_root=app_root,
            tmpfs_root=tmpfs_root,
            restic_binary=restic_binary,
            max_file_bytes=max_file_bytes,
            max_total_bytes=max_total_bytes,
            tag=tag,
            host=host,
            plan=plan,
        )


def _path_argument(value: str) -> Path:
    return Path(value).expanduser()


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--home", required=True, type=_path_argument)
    parser.add_argument("--repo", required=True, type=_path_argument)
    parser.add_argument("--app-root", type=_path_argument)
    parser.add_argument("--tmpfs-root", type=_path_argument, default=DEFAULT_TMPFS_ROOT)
    parser.add_argument(
        "--restic-binary", type=_path_argument, default=DEFAULT_RESTIC_BINARY
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=archive.DEFAULT_MAX_FILE_BYTES,
    )
    parser.add_argument(
        "--max-total-bytes",
        type=int,
        default=archive.DEFAULT_MAX_TOTAL_BYTES,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="read-only capability and scope check")
    _add_common_arguments(plan)
    execute = subparsers.add_parser(
        "execute", help="create one encrypted snapshot and verify exact restore"
    )
    _add_common_arguments(execute)
    execute.add_argument("--confirm", required=True)
    execute.add_argument("--tag", required=True)
    execute.add_argument("--host", default=DEFAULT_HOST)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            receipt = plan_handoff(
                home=args.home,
                repo=args.repo,
                app_root=args.app_root,
                tmpfs_root=args.tmpfs_root,
                restic_binary=args.restic_binary,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
            )
        else:
            receipt = execute_handoff(
                home=args.home,
                repo=args.repo,
                app_root=args.app_root,
                tmpfs_root=args.tmpfs_root,
                restic_binary=args.restic_binary,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
                confirmation=args.confirm,
                tag=args.tag,
                host=args.host,
            )
    except HandoffError as exc:
        error_receipt: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "kind": RECEIPT_KIND,
            "status": "error",
            "error_code": exc.code,
            "snapshot_may_exist": exc.snapshot_may_exist,
            "staging_cleanup_required": exc.staging_cleanup_required,
        }
        if exc.snapshot_id_sha256 is not None:
            error_receipt["snapshot_id_sha256"] = exc.snapshot_id_sha256
        if args.command == "execute" and exc.snapshot_may_exist:
            error_receipt["tag_sha256"] = _sha256_text(args.tag)
        print(json.dumps(error_receipt, sort_keys=True), file=sys.stderr)
        return 2
    except archive.ArchiveError as exc:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "kind": RECEIPT_KIND,
                    "status": "error",
                    "error_code": f"archive_{exc.code}",
                    "snapshot_may_exist": False,
                    "staging_cleanup_required": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except Exception:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "kind": RECEIPT_KIND,
                    "status": "error",
                    "error_code": "unexpected_failure",
                    "snapshot_may_exist": False,
                    "staging_cleanup_required": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
