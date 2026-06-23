#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import json
import re
import sys


def parse_scalar(value: str):
    value = value.strip()

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        return value[1:-1]

    if value == "true":
        return True

    if value == "false":
        return False

    if re.fullmatch(r"-?\d+", value):
        return int(value)

    return value


def parse_manifest(path: Path) -> dict:
    result: dict[str, object] = {}

    for raw_line in path.read_text(
        encoding="utf-8",
    ).splitlines():
        if not raw_line:
            continue

        if raw_line[0].isspace():
            continue

        if ":" not in raw_line:
            continue

        key, value = raw_line.split(":", 1)
        result[key.strip()] = parse_scalar(value)

    return result


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    match = re.match(
        r"\A---\n(?P<body>.*?)\n---\n",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"Kein parsebares Frontmatter: {path}"
        )

    result: dict[str, object] = {}

    for line in match.group("body").splitlines():
        if not line or line[0].isspace():
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        result[key.strip()] = parse_scalar(value)

    return result


def main() -> int:
    root = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) > 1
        else (Path.home() / "repos" / "cabinet").resolve()
    )

    policy_path = root / "policy/cabinet-layout.json"

    if not policy_path.is_file():
        print(
            f"FAIL: Policy fehlt: {policy_path}",
            file=sys.stderr,
        )
        return 2

    policy = json.loads(
        policy_path.read_text(encoding="utf-8")
    )

    errors: list[str] = []

    home_path = root / ".home/home.json"
    workspace_path = root / ".agents/.config/workspace.json"

    if not home_path.is_file():
        errors.append("Home-Konfiguration fehlt.")
    else:
        home = json.loads(
            home_path.read_text(encoding="utf-8")
        )

        expected_default = policy["defaultRoom"]

        if home.get("defaultRoom") != expected_default:
            errors.append(
                "defaultRoom="
                f"{home.get('defaultRoom')!r}, "
                f"erwartet {expected_default!r}"
            )

        if home.get("lastActiveRoom") != expected_default:
            errors.append(
                "lastActiveRoom="
                f"{home.get('lastActiveRoom')!r}, "
                f"erwartet {expected_default!r}"
            )

    if not workspace_path.is_file():
        errors.append("Workspace-Konfiguration fehlt.")
    else:
        workspace = json.loads(
            workspace_path.read_text(encoding="utf-8")
        )

        room = workspace.get("room", {})

        if room.get("slug") != policy["defaultRoom"]:
            errors.append(
                "Workspace zeigt nicht auf den Default-Room."
            )

    expected_rooms = policy["rooms"]
    found_rooms: dict[str, dict] = {}

    for child in root.iterdir():
        if not child.is_dir():
            continue

        manifest_path = child / ".cabinet"

        if not manifest_path.is_file():
            continue

        manifest = parse_manifest(manifest_path)

        if manifest.get("kind") == "room":
            found_rooms[child.name] = manifest

    if set(found_rooms) != set(expected_rooms):
        errors.append(
            "Room-Menge weicht ab: "
            f"gefunden={sorted(found_rooms)}, "
            f"erwartet={sorted(expected_rooms)}"
        )

    for slug, expected in expected_rooms.items():
        actual = found_rooms.get(slug)

        if actual is None:
            continue

        if actual.get("id") != expected["id"]:
            errors.append(
                f"{slug}: id={actual.get('id')!r}, "
                f"erwartet={expected['id']!r}"
            )

        if actual.get("name") != expected["name"]:
            errors.append(
                f"{slug}: name={actual.get('name')!r}, "
                f"erwartet={expected['name']!r}"
            )

        if actual.get("schemaVersion") != 1:
            errors.append(
                f"{slug}: schemaVersion="
                f"{actual.get('schemaVersion')!r}"
            )

    for forbidden in policy["forbiddenTopLevelRooms"]:
        forbidden_path = root / forbidden

        if (forbidden_path / ".cabinet").exists():
            errors.append(
                f"Verbotener Top-Level-Room: {forbidden}"
            )

    editor_path = root / ".global-agents/editor/persona.md"

    if not editor_path.is_file():
        errors.append("Globaler Editor fehlt.")
    else:
        editor = parse_frontmatter(editor_path)
        expected_editor = policy["systemAgents"]["editor"]

        for key, expected_value in expected_editor.items():
            if editor.get(key) != expected_value:
                errors.append(
                    f"editor.{key}={editor.get(key)!r}, "
                    f"erwartet={expected_value!r}"
                )

    for slug in expected_rooms:
        room = root / slug

        rules = room / "Operating Rules.md"

        if not rules.is_file():
            errors.append(
                f"{slug}: Operating Rules fehlen."
            )
        else:
            text = rules.read_text(encoding="utf-8")

            if re.search(
                r"(?m)^ {4}## .+-spezifisch\s*$",
                text,
            ):
                errors.append(
                    f"{slug}: spezifische Überschrift eingerückt."
                )

        agents_dir = room / ".agents"

        if agents_dir.is_dir():
            for path in agents_dir.rglob("*"):
                if not path.is_file():
                    continue

                relative = path.relative_to(agents_dir)

                if relative.name == ".gitkeep":
                    continue

                if any(
                    part in {
                        ".conversations",
                        ".runtime",
                        ".memory",
                        ".messages",
                    }
                    for part in relative.parts
                ):
                    continue

                errors.append(
                    f"{slug}: unerwartete Agentendatei: "
                    f"{relative}"
                )

        jobs_dir = room / ".jobs"

        if jobs_dir.is_dir():
            for path in jobs_dir.rglob("*"):
                if path.is_file() and path.name != ".gitkeep":
                    errors.append(
                        f"{slug}: unerwarteter Job: "
                        f"{path.relative_to(jobs_dir)}"
                    )

    forbidden_pattern = re.compile(
        "|".join(
            re.escape(name)
            for name in policy["forbiddenNames"]
        ),
        flags=re.IGNORECASE,
    )

    excluded_parts = {
        ".git",
        ".cabinet-state",
        ".global-agents",
        ".conversations",
        ".runtime",
    }

    for path in root.rglob("*"):
        relative = path.relative_to(root)

        if any(part in excluded_parts for part in relative.parts):
            continue

        if forbidden_pattern.search(path.name):
            errors.append(
                f"Verbotener Pfadname: {relative}"
            )

    if errors:
        print("CABINET-LAYOUT-GUARD: FAIL")

        for error in errors:
            print(f"- {error}")

        return 2

    print("CABINET-LAYOUT-GUARD: PASS")
    print(
        "Rooms:",
        ", ".join(sorted(expected_rooms)),
    )
    print(
        "Default:",
        policy["defaultRoom"],
    )
    print(
        "Editor:",
        "active=true",
        "heartbeatEnabled=false",
        "canDispatch=false",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
