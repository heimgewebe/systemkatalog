#!/usr/bin/env python3
"""Safely align Cabinet's local workspace with the versioned default room."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

EXPECTED_TARGET = "steuerung"
WORKSPACE_RELATIVE = Path(".agents/.config/workspace.json")
HOME_RELATIVE = Path(".home/home.json")
POLICY_RELATIVE = Path("policy/cabinet-layout.json")
VALIDATOR_RELATIVE = Path("scripts/check-cabinet-layout.py")
BACKUP_SCHEMA = "cabinet.workspace-cutover.v1"
BACKUP_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
Validator = Callable[[Path], None]


class CutoverError(RuntimeError):
    """Raised when the local workspace transition cannot be completed safely."""


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def _reject_symlink_components(path: Path, label: str) -> None:
    path = _absolute(path)
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            break
        if stat.S_ISLNK(metadata.st_mode):
            raise CutoverError(f"{label} may not contain symlinks: {current}")


def _require_directory(path: Path, label: str) -> Path:
    path = _absolute(path)
    _reject_symlink_components(path, label)
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise CutoverError(f"{label} is missing: {path}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise CutoverError(f"{label} is not a directory: {path}")
    return path


def _require_regular_file(root: Path, relative: Path, label: str) -> Path:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise CutoverError(f"{label} uses an unsafe relative path: {relative}")
    root = _require_directory(root, f"{label} root")
    path = root / relative
    _reject_symlink_components(path, label)
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise CutoverError(f"{label} is missing: {relative}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise CutoverError(f"{label} is not a regular file: {relative}")
    return path


def _load_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CutoverError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CutoverError(f"{label} must contain a JSON object")
    return value


def _read_json_file(root: Path, relative: Path, label: str) -> dict[str, Any]:
    return _load_json(_require_regular_file(root, relative, label).read_bytes(), label)


def _read_contract(repo_root: Path) -> str:
    policy = _read_json_file(repo_root, POLICY_RELATIVE, "layout policy")
    home = _read_json_file(repo_root, HOME_RELATIVE, "home configuration")
    target = policy.get("defaultRoom")
    if target != EXPECTED_TARGET:
        raise CutoverError(
            f"layout policy defaultRoom is {target!r}; expected {EXPECTED_TARGET!r}"
        )
    rooms = policy.get("rooms")
    if not isinstance(rooms, dict) or target not in rooms:
        raise CutoverError(f"layout policy does not declare room {target!r}")
    if home.get("defaultRoom") != target:
        raise CutoverError("home defaultRoom does not match layout policy")
    if home.get("lastActiveRoom") != target:
        raise CutoverError("home lastActiveRoom does not match layout policy")
    _require_regular_file(repo_root, Path(target) / ".cabinet", "target room manifest")
    return target


def _read_workspace(
    repo_root: Path,
) -> tuple[Path, bytes, int, dict[str, Any], str]:
    path = _require_regular_file(
        repo_root, WORKSPACE_RELATIVE, "local workspace configuration"
    )
    raw = path.read_bytes()
    mode = stat.S_IMODE(os.lstat(path).st_mode)
    value = _load_json(raw, "local workspace configuration")
    room = value.get("room")
    if not isinstance(room, dict):
        raise CutoverError("local workspace configuration requires object room")
    slug = room.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise CutoverError("local workspace configuration requires non-empty room.slug")
    return path, raw, mode, value, slug


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _serialize_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    _reject_symlink_components(path.parent, "write parent")
    _require_regular_file(path.parent, Path(path.name), "write target")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _require_regular_file(path.parent, Path(path.name), "write target")
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _exclusive_create(path: Path, content: bytes, mode: int) -> None:
    _reject_symlink_components(path.parent, "create parent")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _ensure_state_root(state_root: Path, repo_root: Path) -> Path:
    state_root = _absolute(state_root)
    repo_root = _absolute(repo_root)
    if state_root == repo_root or repo_root in state_root.parents:
        raise CutoverError("backup state root must be outside the repository")
    _reject_symlink_components(state_root.parent, "backup state root parent")
    state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    _reject_symlink_components(state_root, "backup state root")
    metadata = os.lstat(state_root)
    if not stat.S_ISDIR(metadata.st_mode):
        raise CutoverError(f"backup state root is not a directory: {state_root}")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode & 0o077:
        raise CutoverError(
            f"backup state root permissions are too broad: {mode:04o}; expected 0700"
        )
    return state_root


def _backup_id(now: datetime) -> str:
    normalized = now.astimezone(timezone.utc)
    return normalized.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)


def _write_manifest(path: Path, manifest: dict[str, Any], *, create: bool) -> None:
    content = _serialize_json(manifest)
    if create:
        _exclusive_create(path, content, 0o600)
    else:
        _atomic_write(path, content, 0o600)


def _create_backup(
    state_root: Path,
    repo_root: Path,
    original: bytes,
    original_mode: int,
    previous_room: str,
    target_room: str,
    now: datetime,
) -> tuple[str, Path, dict[str, Any]]:
    state_root = _ensure_state_root(state_root, repo_root)
    backup_id = _backup_id(now)
    backup_dir = state_root / backup_id
    try:
        backup_dir.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise CutoverError(f"backup already exists: {backup_id}") from exc
    backup_file = backup_dir / "workspace.json"
    manifest_file = backup_dir / "manifest.json"
    manifest: dict[str, Any] = {
        "schema": BACKUP_SCHEMA,
        "backup_id": backup_id,
        "created_at": now.astimezone(timezone.utc).isoformat(),
        "repository_root": str(_absolute(repo_root)),
        "workspace_relative_path": WORKSPACE_RELATIVE.as_posix(),
        "previous_room": previous_room,
        "target_room": target_room,
        "original_sha256": _sha256(original),
        "original_mode": f"{original_mode:04o}",
        "status": "prepared",
    }
    try:
        _exclusive_create(backup_file, original, 0o600)
        _write_manifest(manifest_file, manifest, create=True)
    except Exception:
        manifest_file.unlink(missing_ok=True)
        backup_file.unlink(missing_ok=True)
        backup_dir.rmdir()
        raise
    return backup_id, backup_dir, manifest


def run_layout_validator(repo_root: Path) -> None:
    validator = _require_regular_file(
        repo_root, VALIDATOR_RELATIVE, "layout validator"
    )
    completed = subprocess.run(
        [sys.executable, str(validator), "--mode", "local", str(repo_root)],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stdout.strip()
        if len(detail) > 4000:
            detail = detail[-4000:]
        raise CutoverError(f"local layout validation failed: {detail}")


def check_cutover(repo_root: Path, validator: Validator = run_layout_validator) -> None:
    repo_root = _require_directory(repo_root, "repository root")
    target = _read_contract(repo_root)
    _, _, _, _, current = _read_workspace(repo_root)
    if current != target:
        raise CutoverError(
            f"local workspace room.slug is {current!r}; expected {target!r}"
        )
    validator(repo_root)


def apply_cutover(
    repo_root: Path,
    state_root: Path,
    validator: Validator = run_layout_validator,
    now: datetime | None = None,
) -> str | None:
    repo_root = _require_directory(repo_root, "repository root")
    target = _read_contract(repo_root)
    workspace_path, original, original_mode, workspace, previous = _read_workspace(
        repo_root
    )
    if previous == target:
        validator(repo_root)
        return None

    updated = copy.deepcopy(workspace)
    updated["room"]["slug"] = target
    replacement = _serialize_json(updated)
    backup_id, backup_dir, manifest = _create_backup(
        state_root,
        repo_root,
        original,
        original_mode,
        previous,
        target,
        now or datetime.now(timezone.utc),
    )
    manifest_path = backup_dir / "manifest.json"
    if (
        workspace_path.read_bytes() != original
        or stat.S_IMODE(os.lstat(workspace_path).st_mode) != original_mode
    ):
        manifest["status"] = "aborted-concurrent-change"
        manifest["failure"] = "workspace changed after backup was prepared"
        _write_manifest(manifest_path, manifest, create=False)
        raise CutoverError("workspace changed concurrently; no mutation was applied")

    try:
        _atomic_write(workspace_path, replacement, original_mode)
        validator(repo_root)
        manifest["status"] = "applied"
        manifest["applied_at"] = datetime.now(timezone.utc).isoformat()
        manifest["applied_sha256"] = _sha256(replacement)
        _write_manifest(manifest_path, manifest, create=False)
    except Exception as exc:
        restore_error: Exception | None = None
        try:
            _atomic_write(workspace_path, original, original_mode)
        except Exception as rollback_exc:  # pragma: no cover
            restore_error = rollback_exc
        manifest["status"] = "rollback-failed" if restore_error else "rolled-back"
        manifest["failure"] = str(exc)
        manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        try:
            _write_manifest(manifest_path, manifest, create=False)
        except Exception as manifest_exc:  # pragma: no cover
            if restore_error is None:
                restore_error = manifest_exc
        if restore_error is not None:
            raise CutoverError(
                "workspace cutover failed and recovery was incomplete: "
                f"failure={exc}; recovery={restore_error}"
            ) from exc
        raise CutoverError(
            f"workspace cutover failed; original state restored: {exc}"
        ) from exc
    return backup_id


def _load_backup(
    repo_root: Path,
    state_root: Path,
    backup_id: str,
) -> tuple[Path, dict[str, Any], bytes, int]:
    if not BACKUP_ID_RE.fullmatch(backup_id):
        raise CutoverError(f"invalid backup id: {backup_id!r}")
    state_root = _ensure_state_root(state_root, repo_root)
    backup_dir = _require_directory(state_root / backup_id, "backup directory")
    manifest_path = _require_regular_file(
        backup_dir, Path("manifest.json"), "backup manifest"
    )
    backup_file = _require_regular_file(
        backup_dir, Path("workspace.json"), "workspace backup"
    )
    manifest = _load_json(manifest_path.read_bytes(), "backup manifest")
    if manifest.get("schema") != BACKUP_SCHEMA:
        raise CutoverError("backup manifest has an unsupported schema")
    if manifest.get("backup_id") != backup_id:
        raise CutoverError("backup manifest id does not match directory")
    if manifest.get("repository_root") != str(_absolute(repo_root)):
        raise CutoverError("backup manifest belongs to a different repository root")
    if manifest.get("workspace_relative_path") != WORKSPACE_RELATIVE.as_posix():
        raise CutoverError("backup manifest targets an unexpected workspace path")
    original = backup_file.read_bytes()
    if _sha256(original) != manifest.get("original_sha256"):
        raise CutoverError("workspace backup hash does not match manifest")
    raw_mode = manifest.get("original_mode")
    if not isinstance(raw_mode, str) or not re.fullmatch(r"0[0-7]{3}", raw_mode):
        raise CutoverError("backup manifest contains an invalid original mode")
    return manifest_path, manifest, original, int(raw_mode, 8)


def rollback_cutover(repo_root: Path, state_root: Path, backup_id: str) -> None:
    repo_root = _require_directory(repo_root, "repository root")
    manifest_path, manifest, original, original_mode = _load_backup(
        repo_root, state_root, backup_id
    )
    workspace_path, current, current_mode, _, _ = _read_workspace(repo_root)

    if current == original and current_mode == original_mode:
        manifest["status"] = "rolled-back-explicitly"
        manifest["explicit_rollback_at"] = datetime.now(timezone.utc).isoformat()
        _write_manifest(manifest_path, manifest, create=False)
        return

    applied_sha = manifest.get("applied_sha256")
    if manifest.get("status") != "applied" or not isinstance(applied_sha, str):
        raise CutoverError("backup does not describe an applied cutover")
    if not SHA256_RE.fullmatch(applied_sha):
        raise CutoverError("backup manifest contains an invalid applied hash")
    if _sha256(current) != applied_sha or current_mode != original_mode:
        raise CutoverError(
            "workspace changed since cutover; refusing rollback to avoid data loss"
        )

    _atomic_write(workspace_path, original, original_mode)
    if workspace_path.read_bytes() != original:
        raise CutoverError("rollback did not restore exact workspace bytes")
    if stat.S_IMODE(os.lstat(workspace_path).st_mode) != original_mode:
        raise CutoverError("rollback did not restore the original workspace mode")
    manifest["status"] = "rolled-back-explicitly"
    manifest["explicit_rollback_at"] = datetime.now(timezone.utc).isoformat()
    _write_manifest(manifest_path, manifest, create=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "apply", "rollback"))
    parser.add_argument("backup_id", nargs="?")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path("~/.local/state/cabinet/workspace-cutovers"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "rollback" and not args.backup_id:
        print("ERROR: rollback requires backup_id", file=sys.stderr)
        return 2
    if args.action != "rollback" and args.backup_id:
        print("ERROR: backup_id is accepted only for rollback", file=sys.stderr)
        return 2
    try:
        if args.action == "check":
            check_cutover(args.repo_root)
            print("TARGET-PROOF: CABINET WORKSPACE DEFAULT IS STEUERUNG")
        elif args.action == "apply":
            backup_id = apply_cutover(args.repo_root, args.state_root)
            if backup_id is None:
                print("Workspace already points to steuerung.")
            else:
                print(f"Workspace changed to steuerung. Backup: {backup_id}")
            print("TARGET-PROOF: CABINET WORKSPACE DEFAULT IS STEUERUNG")
        else:
            assert args.backup_id is not None
            rollback_cutover(args.repo_root, args.state_root, args.backup_id)
            print(f"Workspace backup restored: {args.backup_id}")
            print("NOTE: local layout validation may now report intentional drift.")
        return 0
    except (CutoverError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
