from __future__ import annotations

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

TARGET_ROOM = "steuerung"
WORKSPACE_RELATIVE = Path(".agents/.config/workspace.json")
HOME_RELATIVE = Path(".home/home.json")
POLICY_RELATIVE = Path("policy/cabinet-layout.json")
BACKUP_SCHEMA = "cabinet.workspace-cutover.v1"
BACKUP_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
Validator = Callable[[Path], None]


class CutoverError(RuntimeError):
    """Raised when the workspace cutover contract cannot be satisfied."""


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def backup_id(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)


def safe_relative_path(value: Path, label: str) -> tuple[str, ...]:
    if value.is_absolute() or not value.parts:
        raise CutoverError(f"{label} must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in value.parts):
        raise CutoverError(f"{label} contains an unsafe path component: {value}")
    return value.parts


def require_regular_file(root: Path, relative: Path, label: str) -> Path:
    parts = safe_relative_path(relative, label)
    current = root
    for index, component in enumerate(parts):
        current = current / component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError as exc:
            raise CutoverError(f"{label} is missing: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise CutoverError(f"{label} may not contain symlinks: {relative}")
        if index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise CutoverError(
                f"{label} parent is not a directory: {current.relative_to(root)}"
            )
        if index == len(parts) - 1 and not stat.S_ISREG(metadata.st_mode):
            raise CutoverError(f"{label} is not a regular file: {relative}")
    return current


def load_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CutoverError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CutoverError(f"{label} must contain a JSON object")
    return value


def read_json_file(root: Path, relative: Path, label: str) -> dict[str, Any]:
    path = require_regular_file(root, relative, label)
    return load_json_bytes(path.read_bytes(), label)


def verify_versioned_contract(repo_root: Path) -> None:
    policy = read_json_file(repo_root, POLICY_RELATIVE, "Cabinet layout policy")
    home = read_json_file(repo_root, HOME_RELATIVE, "Cabinet home configuration")
    if policy.get("defaultRoom") != TARGET_ROOM:
        raise CutoverError(
            "versioned layout policy does not declare steuerung as defaultRoom"
        )
    rooms = policy.get("rooms")
    if not isinstance(rooms, dict) or TARGET_ROOM not in rooms:
        raise CutoverError("versioned layout policy does not declare room steuerung")
    if home.get("defaultRoom") != TARGET_ROOM:
        raise CutoverError(
            "versioned home configuration does not declare steuerung as defaultRoom"
        )
    if home.get("lastActiveRoom") != TARGET_ROOM:
        raise CutoverError(
            "versioned home configuration does not declare steuerung as lastActiveRoom"
        )
    require_regular_file(
        repo_root,
        Path(TARGET_ROOM) / ".cabinet",
        "target room manifest",
    )


def read_workspace(repo_root: Path) -> tuple[Path, bytes, int, dict[str, Any]]:
    path = require_regular_file(
        repo_root,
        WORKSPACE_RELATIVE,
        "local workspace configuration",
    )
    raw = path.read_bytes()
    mode = stat.S_IMODE(os.lstat(path).st_mode)
    data = load_json_bytes(raw, "local workspace configuration")
    room = data.get("room")
    if not isinstance(room, dict):
        raise CutoverError("local workspace configuration requires object room")
    slug = room.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise CutoverError("local workspace configuration requires non-empty room.slug")
    return path, raw, mode, data


def atomic_write_bytes(path: Path, content: bytes, mode: int) -> None:
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
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def serialize_json(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def ensure_state_root(state_root: Path) -> Path:
    state_root = state_root.expanduser().resolve(strict=False)
    state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    metadata = os.lstat(state_root)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CutoverError(f"backup state root is unsafe: {state_root}")
    os.chmod(state_root, 0o700)
    return state_root


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    atomic_write_bytes(path, serialize_json(manifest), 0o600)


def save_copy(path: Path, content: bytes) -> None:
    atomic_write_bytes(path, content, 0o600)


def run_layout_validator(repo_root: Path) -> None:
    validator = repo_root / "scripts/check-cabinet-layout.py"
    if not validator.is_file() or validator.is_symlink():
        raise CutoverError("layout validator is missing or unsafe")
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
