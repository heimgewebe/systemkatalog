#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any


def parse_scalar(value: str) -> object:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_manifest(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line[0].isspace() or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        result[key.strip()] = parse_scalar(value)
    return result


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Kein parsebares Frontmatter: {path}")
    result: dict[str, object] = {}
    for line in match.group("body").splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = parse_scalar(value)
    return result


def load_object(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        errors.append(f"{label} fehlt: {path}")
        return {}
    if not stat.S_ISREG(mode) or path.is_symlink():
        errors.append(f"{label} ist keine reguläre, symlinkfreie Datei: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label} ist ungültig: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} muss ein JSON-Objekt sein.")
        return {}
    return value


def safe_relative(value: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} muss ein nichtleerer relativer Pfad sein.")
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        errors.append(f"{label} ist unsicher: {value!r}")
        return None
    return path


def validate_agent_surface(root: Path, slug: str, mode: str, errors: list[str]) -> None:
    room = root / slug
    rules = room / "Operating Rules.md"
    if not rules.is_file():
        errors.append(f"{slug}: Operating Rules fehlen.")
    else:
        text = rules.read_text(encoding="utf-8")
        if re.search(r"(?m)^ {4}## .+-spezifisch\s*$", text):
            errors.append(f"{slug}: spezifische Überschrift eingerückt.")

    agents_dir = room / ".agents"
    if agents_dir.is_dir():
        for path in agents_dir.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(agents_dir)
            if relative.name == ".gitkeep":
                continue
            if mode == "local" and any(
                part in {".conversations", ".runtime", ".memory", ".messages"}
                for part in relative.parts
            ):
                continue
            errors.append(f"{slug}: unerwartete Agentendatei: {relative}")

    jobs_dir = room / ".jobs"
    if jobs_dir.is_dir():
        for path in jobs_dir.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                errors.append(f"{slug}: unerwarteter Job: {path.relative_to(jobs_dir)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path.home() / "repos" / "cabinet"))
    parser.add_argument("--mode", choices=["local", "repository"], default="local")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    mode = args.mode
    errors: list[str] = []

    policy = load_object(root / "policy/cabinet-layout.json", "Layout-Policy", errors)
    navigation_path = safe_relative(
        policy.get("navigationPolicy", "policy/cabinet-navigation.json"),
        "navigationPolicy",
        errors,
    )
    navigation = (
        load_object(root / navigation_path, "Navigationsvertrag", errors)
        if navigation_path is not None
        else {}
    )
    registry_path = safe_relative(
        navigation.get("legacyRegistry", policy.get("legacyRegistry")),
        "legacyRegistry",
        errors,
    )
    registry = (
        load_object(root / registry_path, "Legacy-Registry", errors)
        if registry_path is not None
        else {}
    )

    expected_default = policy.get("defaultRoom")
    if policy.get("schemaVersion") != 1:
        errors.append("Layout-Policy schemaVersion muss 1 sein.")
    if policy.get("layoutMode") != "three-active-rooms":
        errors.append("Layout-Policy layoutMode muss 'three-active-rooms' sein.")
    if navigation.get("schema") != "cabinet.navigation.v1":
        errors.append("Navigationsvertrag hat ein unbekanntes Schema.")
    if navigation.get("defaultRoom") != expected_default:
        errors.append("Layout- und Navigations-Default widersprechen sich.")

    policy_rooms = policy.get("rooms")
    active_rooms = navigation.get("activeRooms")
    legacy = navigation.get("legacyCollections")
    if not isinstance(policy_rooms, dict):
        errors.append("policy.rooms muss ein Objekt sein.")
        policy_rooms = {}
    if not isinstance(active_rooms, dict):
        errors.append("navigation.activeRooms muss ein Objekt sein.")
        active_rooms = {}
    if not isinstance(legacy, dict):
        errors.append("navigation.legacyCollections muss ein Objekt sein.")
        legacy = {}

    active_set = set(active_rooms)
    legacy_set = set(legacy)
    known_set = active_set | legacy_set
    policy_active = policy.get("activeRooms")
    if not isinstance(policy_active, list) or set(policy_active) != active_set:
        errors.append("policy.activeRooms weicht vom Navigationsvertrag ab.")
    if set(policy_rooms) != active_set:
        errors.append(
            "Room-Menge weicht ab: "
            f"policy={sorted(policy_rooms)}, aktiv={sorted(active_set)}"
        )
    if active_set & legacy_set:
        errors.append("Aktive Räume und Legacy-Sammlungen überlappen.")
    if expected_default not in active_set:
        errors.append("Der Default ist kein aktiver Raum.")

    if registry.get("schema") != "cabinet.legacy-room-cutover.v1":
        errors.append("Legacy-Registry hat ein unbekanntes Schema.")
    if registry.get("status") != "active-manifests-retired":
        errors.append("Legacy-Registry meldet nicht die stillgelegten aktiven Legacy-Manifeste.")
    if set(registry.get("activeRooms", [])) != active_set:
        errors.append("Registry und Navigation enthalten andere aktive Räume.")
    registry_legacy = registry.get("legacyCollections")
    if not isinstance(registry_legacy, dict) or set(registry_legacy) != legacy_set:
        errors.append("Registry und Navigation enthalten andere Legacy-Sammlungen.")
        registry_legacy = {}

    for child in root.iterdir():
        manifest_path = child / ".cabinet"
        if not manifest_path.exists() and not manifest_path.is_symlink():
            continue
        if child.name in known_set:
            continue
        if child.is_symlink() or not child.is_dir():
            errors.append(f"Unerwarteter Top-Level-.cabinet-Pfad: {child.name}")
            continue
        if not manifest_path.is_file() or manifest_path.is_symlink():
            errors.append(f"{child.name}: Top-Level-.cabinet ist keine reguläre Datei.")
            continue
        try:
            manifest = parse_manifest(manifest_path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{child.name}: unbekanntes .cabinet ist nicht lesbar: {exc}")
            continue
        kind = manifest.get("kind")
        if kind == "room":
            errors.append(f"Unerwarteter aktiver Top-Level-Room: {child.name}")
        else:
            errors.append(
                f"Unerwartetes Top-Level-.cabinet-Manifest: {child.name} "
                f"(kind={kind!r})"
            )

    found_active: dict[str, dict[str, object]] = {}
    for slug in sorted(known_set):
        directory = root / slug
        if not directory.is_dir() or directory.is_symlink():
            errors.append(f"Room-Menge weicht ab: Sammlung fehlt oder ist unsicher: {slug}")
            continue
        manifest_path = directory / ".cabinet"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            errors.append(f"{slug}: .cabinet fehlt oder ist unsicher.")
            continue
        try:
            manifest = parse_manifest(manifest_path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"{slug}: .cabinet ist nicht lesbar: {exc}")
            continue

        expected = policy_rooms.get(slug, {}) if slug in active_set else legacy.get(slug, {})
        if manifest.get("schemaVersion") != 1:
            errors.append(f"{slug}: schemaVersion={manifest.get('schemaVersion')!r}")
        if manifest.get("id") != expected.get("id"):
            errors.append(f"{slug}: id={manifest.get('id')!r}, erwartet={expected.get('id')!r}")
        if manifest.get("name") != expected.get("name"):
            errors.append(f"{slug}: name={manifest.get('name')!r}, erwartet={expected.get('name')!r}")

        if slug in active_set:
            if manifest.get("kind") != "room":
                errors.append(f"{slug}: aktiver Raum hat kind={manifest.get('kind')!r}")
            else:
                found_active[slug] = manifest
            nav_entry = active_rooms.get(slug, {})
            for key in ("id", "name"):
                if nav_entry.get(key) != expected.get(key):
                    errors.append(f"{slug}: activeRooms-Drift bei {key}.")
        else:
            entry = legacy.get(slug, {})
            if manifest.get("kind") == "room":
                errors.append(f"{slug}: Legacy-Sammlung ist als Room aktiv.")
            if manifest.get("kind") != entry.get("manifestKind"):
                errors.append(f"{slug}: Legacy-kind={manifest.get('kind')!r}")
            for key in ("successor", "axis", "visibility", "contentState"):
                if manifest.get(key) != entry.get(key):
                    errors.append(f"{slug}: Legacy-Drift bei {key}.")
            if manifest.get("registry") != str(registry_path):
                errors.append(f"{slug}: Registry-Verweis driftet.")
            registered = registry_legacy.get(slug, {})
            if isinstance(registered, dict):
                for key in ("successor", "axis"):
                    if registered.get(key) != entry.get(key):
                        errors.append(f"{slug}: Registry-Drift bei {key}.")

    if set(found_active) != active_set:
        errors.append(
            "Room-Menge weicht ab: "
            f"gefunden={sorted(found_active)}, erwartet={sorted(active_set)}"
        )

    home_path = root / ".home/home.json"
    home = load_object(home_path, "Home-Konfiguration", errors)
    if home.get("defaultRoom") != expected_default:
        errors.append(f"defaultRoom={home.get('defaultRoom')!r}, erwartet {expected_default!r}")
    if home.get("lastActiveRoom") != expected_default:
        errors.append(f"lastActiveRoom={home.get('lastActiveRoom')!r}, erwartet {expected_default!r}")

    if mode == "local":
        workspace = load_object(
            root / ".agents/.config/workspace.json", "Workspace-Konfiguration", errors
        )
        room = workspace.get("room", {})
        expected_room = policy_rooms.get(expected_default, {})
        if not isinstance(room, dict):
            errors.append("Workspace room muss ein Objekt sein.")
        elif not isinstance(expected_room, dict):
            errors.append("Default-Room fehlt in policy.rooms.")
        else:
            expected_identity = {
                "slug": expected_default,
                "id": expected_room.get("id"),
                "name": expected_room.get("name"),
            }
            for key, expected_value in expected_identity.items():
                if room.get(key) != expected_value:
                    errors.append(
                        f"Workspace room.{key}={room.get(key)!r}, "
                        f"erwartet {expected_value!r}"
                    )
        editor_path = root / ".global-agents/editor/persona.md"
        if not editor_path.is_file():
            errors.append("Globaler Editor fehlt.")
        else:
            try:
                editor = parse_frontmatter(editor_path)
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(str(exc))
            else:
                expected_editor = policy.get("systemAgents", {}).get("editor", {})
                for key, value in expected_editor.items():
                    if editor.get(key) != value:
                        errors.append(f"editor.{key}={editor.get(key)!r}, erwartet={value!r}")

    for forbidden in policy.get("forbiddenTopLevelRooms", []):
        if (root / forbidden / ".cabinet").exists():
            errors.append(f"Verbotener Top-Level-Room: {forbidden}")

    for slug in sorted(known_set):
        if (root / slug).is_dir():
            validate_agent_surface(root, slug, mode, errors)

    forbidden_names = policy.get("forbiddenNames", [])
    if forbidden_names:
        forbidden_pattern = re.compile(
            "|".join(re.escape(name) for name in forbidden_names),
            flags=re.IGNORECASE,
        )
        excluded_parts = {
            ".git", ".cabinet-state", ".global-agents", ".conversations", ".runtime"
        }
        for path in root.rglob("*"):
            relative = path.relative_to(root)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if forbidden_pattern.search(path.name):
                errors.append(f"Verbotener Pfadname: {relative}")

    if errors:
        print("CABINET-LAYOUT-GUARD: FAIL")
        print(f"Mode: {mode}")
        for error in errors:
            print(f"- {error}")
        return 2

    print("CABINET-LAYOUT-GUARD: PASS")
    print(f"Mode: {mode}")
    print("Rooms:", ", ".join(sorted(active_set)))
    print("Legacy collections:", ", ".join(sorted(legacy_set)))
    print("Default:", expected_default)
    print("Legacy room manifests: retired")
    if mode == "local":
        print("Editor: active=true heartbeatEnabled=false canDispatch=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
