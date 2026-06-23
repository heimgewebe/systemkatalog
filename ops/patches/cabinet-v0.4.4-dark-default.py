#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

EXPECTED_VERSION = "0.4.4"

PATCHES = {
    "src/app/layout.tsx": (
        'defaultTheme="light"',
        'defaultTheme="dark"',
    ),
    "src/components/layout/theme-initializer.tsx": (
        'const themeName = stored || "paper";',
        'const themeName = stored || "black";',
    ),
    "src/components/layout/room-theme-sync.tsx": (
        'room?.theme || getStoredThemeName() || "paper";',
        'room?.theme || getStoredThemeName() || "black";',
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply or verify Cabinet 0.4.4 dark defaults."
    )

    parser.add_argument(
        "--app-root",
        type=Path,
        default=Path.home() / ".cabinet" / "app" / "v0.4.4",
    )

    mode = parser.add_mutually_exclusive_group(
        required=True,
    )

    mode.add_argument(
        "--check",
        action="store_true",
    )

    mode.add_argument(
        "--apply",
        action="store_true",
    )

    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="strict",
    )


def verify_version(app_root: Path) -> None:
    package = app_root / "package.json"

    if not package.is_file():
        raise SystemExit(
            f"STOP: package.json fehlt: {package}"
        )

    payload = json.loads(
        read_text(package)
    )

    actual = payload.get("version")

    if actual != EXPECTED_VERSION:
        raise SystemExit(
            "STOP: Unerwartete Cabinet-Version: "
            f"{actual!r}; erwartet {EXPECTED_VERSION!r}"
        )


def verify_black_theme(app_root: Path) -> None:
    themes = app_root / "src/lib/themes.ts"

    if not themes.is_file():
        raise SystemExit(
            f"STOP: Theme-Datei fehlt: {themes}"
        )

    text = read_text(themes)

    if re.search(
        r'name:\s*"black".{0,500}?type:\s*"dark"',
        text,
        flags=re.DOTALL,
    ) is None:
        raise SystemExit(
            'STOP: Theme "black" ist nicht als dark belegt.'
        )


def patch_state(
    path: Path,
    old: str,
    new: str,
) -> str:
    text = read_text(path)

    old_count = text.count(old)
    new_count = text.count(new)

    if old_count == 1 and new_count == 0:
        return "unpatched"

    if old_count == 0 and new_count == 1:
        return "patched"

    raise SystemExit(
        f"STOP: Uneindeutiger Patchzustand in {path}: "
        f"old={old_count}, new={new_count}"
    )


def apply_patch(
    app_root: Path,
    relative: str,
    old: str,
    new: str,
    backup_root: Path,
) -> None:
    path = app_root / relative

    current_state = patch_state(
        path,
        old,
        new,
    )

    if current_state == "patched":
        print(f"PASS  bereits gepatcht: {relative}")
        return

    backup = backup_root / relative

    backup.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        path,
        backup,
    )

    text = read_text(path)
    updated = text.replace(
        old,
        new,
        1,
    )

    temporary = path.with_name(
        path.name + ".cabinet-dark.tmp"
    )

    temporary.write_text(
        updated,
        encoding="utf-8",
    )

    temporary.chmod(
        path.stat().st_mode & 0o777
    )

    temporary.replace(path)

    if patch_state(path, old, new) != "patched":
        raise SystemExit(
            f"STOP: Patchnachweis fehlgeschlagen: {relative}"
        )

    print(f"PATCH {relative}")


def main() -> int:
    args = parse_args()

    app_root = args.app_root.expanduser().resolve()

    verify_version(app_root)
    verify_black_theme(app_root)

    if args.check:
        for relative, (old, new) in PATCHES.items():
            path = app_root / relative

            if not path.is_file():
                raise SystemExit(
                    f"STOP: Patchziel fehlt: {path}"
                )

            if patch_state(path, old, new) != "patched":
                raise SystemExit(
                    f"STOP: Dark-Default fehlt: {relative}"
                )

            print(f"PASS  {relative}")

        print("DARK-DEFAULT-CHECK: PASS")
        return 0

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup_root = (
        Path.home()
        / ".local/state/cabinet/theme-backups"
        / stamp
    )

    for relative, (old, new) in PATCHES.items():
        path = app_root / relative

        if not path.is_file():
            raise SystemExit(
                f"STOP: Patchziel fehlt: {path}"
            )

        apply_patch(
            app_root,
            relative,
            old,
            new,
            backup_root,
        )

    print(f"Backup: {backup_root}")
    print("DARK-DEFAULT-APPLY: PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
