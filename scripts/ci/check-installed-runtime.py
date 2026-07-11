#!/usr/bin/env python3
"""Verify the shadow-installed Systemkatalog runtime exactly."""

from __future__ import annotations

import argparse
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def rendered_unit(repo: Path, home: Path) -> bytes:
    source = repo / "ops/systemd/systemkatalog.service.tmpl"
    return (
        source.read_text(encoding="utf-8")
        .replace("@HOME@", str(home))
        .replace("@SYSTEMKATALOG_ROOT@", str(repo))
        .encode()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--systemctl-log", type=Path, required=True)
    parser.add_argument("--expected-systemctl-calls", type=int, required=True)
    args = parser.parse_args()
    home, repo = args.home, args.repo_root

    expected = {
        home / ".config/systemd/user/systemkatalog.service": rendered_unit(repo, home),
        home / ".local/bin/systemkatalog": (repo / "ops/bin/systemkatalog").read_bytes(),
        home / ".local/bin/systemkatalogctl": (repo / "ops/bin/systemkatalogctl").read_bytes(),
    }
    for path, content in expected.items():
        if not path.is_file() or path.is_symlink():
            fail(f"missing regular file: {path}")
        if path.read_bytes() != content:
            fail(f"content mismatch: {path}")
        actual_mode = path.stat().st_mode & 0o777
        expected_mode = 0o644 if path.name.endswith(".service") else 0o755
        if actual_mode != expected_mode:
            fail(f"mode mismatch: {path}: {actual_mode:o} != {expected_mode:o}")

    retired = [
        home / ".config/systemd/user/heimgewebe-systemkatalog.service",
        home / ".config/systemd/user/cabinet.service",
        home / ".config/systemd/user/cabinet.service.d",
        home / ".local/bin/heimgewebe-systemkatalog",
        *(home / ".local/bin" / name for name in ("cabinet", "cabinet-session", "cabinetctl", "cabinet-security-gate")),
    ]
    for path in retired:
        if path.exists() or path.is_symlink():
            fail(f"retired path exists: {path}")

    calls = [line for line in args.systemctl_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(calls) != args.expected_systemctl_calls:
        fail(f"systemctl call count: gefunden={len(calls)}, erwartet={args.expected_systemctl_calls}")
    if any(line != "--user daemon-reload" for line in calls):
        fail(f"unexpected systemctl call: {calls}")
    print("INSTALLED-SYSTEMKATALOG-RUNTIME: PASS")


if __name__ == "__main__":
    main()
