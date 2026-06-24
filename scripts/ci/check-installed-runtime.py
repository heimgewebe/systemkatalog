#!/usr/bin/env python3
import argparse
import sys
import hashlib
from pathlib import Path
import os

def check_binary(path: Path, expected_mode: str, src_path: Path):
    if not path.is_file() or path.is_symlink():
        print(f"FAIL: not a regular file: {path}")
        sys.exit(1)
    actual_mode = oct(path.stat().st_mode)[-4:]
    if actual_mode != expected_mode:
        print(f"FAIL: mode mismatch for {path}: gefunden={actual_mode}, erwartet={expected_mode}")
        sys.exit(1)
    if path.read_bytes() != src_path.read_bytes():
        print(f"FAIL: content mismatch for {path}")
        sys.exit(1)

def check_template(path: Path, expected_mode: str, src_path: Path, temp_home: Path, temp_repo: Path):
    if not path.is_file() or path.is_symlink():
        print(f"FAIL: not a regular file: {path}")
        sys.exit(1)
    actual_mode = oct(path.stat().st_mode)[-4:]
    if actual_mode != expected_mode:
        print(f"FAIL: mode mismatch for {path}: gefunden={actual_mode}, erwartet={expected_mode}")
        sys.exit(1)

    content = src_path.read_text()
    expected_content = content.replace("@HOME@", str(temp_home)).replace("@CABINET_ROOT@", str(temp_repo))
    if path.read_text() != expected_content:
        print(f"FAIL: content mismatch for {path}")
        sys.exit(1)

def check_symlink(path: Path, target_path: Path):
    if not path.is_symlink():
        print(f"FAIL: not a symlink: {path}")
        sys.exit(1)
    raw_target = os.readlink(path)
    if raw_target != str(target_path):
        print(f"FAIL: symlink raw target mismatch: gefunden={raw_target}, erwartet={target_path}")
        sys.exit(1)
    if not path.exists() or not path.resolve().is_file():
        print(f"FAIL: symlink target is missing or not a regular file: {path}")
        sys.exit(1)

def check_env(path: Path, expected_mode: str, expected_hash: str):
    if not path.is_file() or path.is_symlink():
        print(f"FAIL: not a regular file: {path}")
        sys.exit(1)
    actual_mode = oct(path.stat().st_mode)[-4:]
    if actual_mode != expected_mode:
        print(f"FAIL: mode mismatch for {path}: gefunden={actual_mode}, erwartet={expected_mode}")
        sys.exit(1)
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    if h != expected_hash:
        print(f"FAIL: hash mismatch for {path}: gefunden={h}, erwartet={expected_hash}")
        sys.exit(1)

def check_systemctl(log_path: Path, expected_calls: int):
    if not log_path.exists():
        calls = []
    else:
        calls = log_path.read_text().splitlines()

    if len(calls) != expected_calls:
        print(f"FAIL: systemctl call count: gefunden={len(calls)}, erwartet={expected_calls}")
        sys.exit(1)

    for call in calls:
        if call != "--user daemon-reload":
            print(f"FAIL: invalid systemctl call: {call}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--systemctl-log", type=Path, required=True)
    parser.add_argument("--expected-systemctl-calls", type=int, required=True)
    parser.add_argument("--runtime-env-sha256", type=str, required=True)
    args = parser.parse_args()

    binaries = ["cabinet", "cabinet-session", "cabinetctl", "cabinet-security-gate"]
    for b in binaries:
        check_binary(args.home / f".local/bin/{b}", "0755", args.repo_root / f"ops/bin/{b}")

    check_template(
        args.home / ".config/systemd/user/cabinet.service",
        "0644",
        args.repo_root / "ops/systemd/cabinet.service.tmpl",
        args.home,
        args.app_root
    )

    check_template(
        args.home / ".config/systemd/user/cabinet.service.d/10-loopback-gate.conf",
        "0644",
        args.repo_root / "ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl",
        args.home,
        args.app_root
    )

    check_symlink(
        args.home / ".local/bin/cabinet-safe-export",
        args.repo_root / "scripts/cabinet-safe-export.sh"
    )

    check_env(
        args.home / ".config/cabinet/runtime.env",
        "0600",
        args.runtime_env_sha256
    )

    check_systemctl(args.systemctl_log, args.expected_systemctl_calls)

    print("INSTALLED-RUNTIME-CONTRACT: PASS")

if __name__ == "__main__":
    main()
