#!/usr/bin/env python3
"""Validate Cabinet Project Card v1 documents."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_DIR = Path("bestand/20 Projekte")
INDEX_RELATIVE = PROJECT_DIR / "index.md"
SCHEMA = "cabinet.project-card.v1"
CARD_PATTERN = re.compile(
    r"<!--\s*cabinet-project-card-v1\s*\n(?P<payload>\{.*?\})\s*\n-->",
    re.DOTALL,
)
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
LOCAL_CARD_LINK_PATTERN = re.compile(r"\]\(([^/()]+\.md)\)")
REQUIRED_HEADINGS = (
    "## Ziel",
    "## Repositorybeziehungen",
    "## Belegter Stand",
    "## Blocker und Risiken",
    "## Nächste Aktion",
    "## Quellen",
)
ALLOWED_EVIDENCE_STATUS = {"partial", "bounded"}
REQUIRED_METADATA_KEYS = {
    "schema",
    "id",
    "title",
    "evidence_status",
    "reviewed_at",
    "repositories",
    "sources",
}
REQUIRED_REPOSITORY_KEYS = {"name", "role", "evidence"}
ALLOWED_REPOSITORY_KEYS = REQUIRED_REPOSITORY_KEYS | {"reference"}


class ProjectCardError(RuntimeError):
    """Raised when a Project Card v1 contract is violated."""


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
            raise ProjectCardError(f"{label} may not contain symlinks: {current}")


def _require_directory(path: Path, label: str) -> Path:
    path = _absolute(path)
    _reject_symlink_components(path, label)
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise ProjectCardError(f"{label} is missing: {path}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise ProjectCardError(f"{label} is not a directory: {path}")
    return path


def _safe_relative_path(relative: Path, label: str) -> None:
    if relative.is_absolute() or not relative.parts:
        raise ProjectCardError(f"{label} uses an unsafe relative path: {relative}")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise ProjectCardError(f"{label} uses an unsafe relative path: {relative}")
    if relative.parts[0] == ".git":
        raise ProjectCardError(f"{label} may not read Git internals: {relative}")


def _require_regular_file(root: Path, relative: Path, label: str) -> Path:
    _safe_relative_path(relative, label)
    root = _require_directory(root, f"{label} root")
    path = root / relative
    _reject_symlink_components(path, label)
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise ProjectCardError(f"{label} is missing: {relative.as_posix()}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ProjectCardError(f"{label} is not a regular file: {relative.as_posix()}")
    return path


def _load_metadata(text: str, label: str) -> dict[str, Any]:
    matches = list(CARD_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ProjectCardError(
            f"{label} must contain exactly one cabinet-project-card-v1 block"
        )
    try:
        value = json.loads(matches[0].group("payload"))
    except json.JSONDecodeError as exc:
        raise ProjectCardError(f"{label} contains invalid metadata JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectCardError(f"{label} metadata must be a JSON object")
    return value


def _section_body(text: str, heading: str) -> str:
    markers = list(re.finditer(rf"(?m)^{re.escape(heading)}\s*$", text))
    if len(markers) != 1:
        raise ProjectCardError(
            f"required heading must occur exactly once: {heading}"
        )
    marker = markers[0]
    next_heading = re.search(r"(?m)^##\s+.+$", text[marker.end() :])
    end = marker.end() + next_heading.start() if next_heading else len(text)
    body = text[marker.end() : end].strip()
    if not body:
        raise ProjectCardError(f"required section is empty: {heading}")
    return body


def _validate_metadata_keys(metadata: dict[str, Any], label: str) -> None:
    keys = set(metadata)
    if keys == REQUIRED_METADATA_KEYS:
        return
    missing = sorted(REQUIRED_METADATA_KEYS - keys)
    extra = sorted(keys - REQUIRED_METADATA_KEYS)
    raise ProjectCardError(
        f"{label} metadata keys mismatch; missing={missing}, extra={extra}"
    )


def _validate_sources(
    repo_root: Path,
    label: str,
    sources: object,
    visible_sources: str,
) -> set[str]:
    if not isinstance(sources, list) or not sources:
        raise ProjectCardError(f"{label} sources must be a non-empty array")
    if any(not isinstance(item, str) or not item for item in sources):
        raise ProjectCardError(f"{label} sources must contain non-empty paths")

    typed_sources = list(sources)
    if len(set(typed_sources)) != len(typed_sources):
        raise ProjectCardError(f"{label} sources contain duplicates")

    for raw_source in typed_sources:
        _require_regular_file(repo_root, Path(raw_source), f"{label} source")
        marker = f"`{raw_source}`"
        if marker not in visible_sources:
            raise ProjectCardError(
                f"{label} source is absent from visible Quellen section: {raw_source}"
            )
    return set(typed_sources)


def _validate_repositories(
    label: str,
    repositories: object,
    source_set: set[str],
) -> None:
    if not isinstance(repositories, list) or not repositories:
        raise ProjectCardError(f"{label} repositories must be a non-empty array")

    names: list[str] = []
    for index, relationship in enumerate(repositories):
        if not isinstance(relationship, dict):
            raise ProjectCardError(
                f"{label} repositories[{index}] must be a JSON object"
            )
        relationship_keys = set(relationship)
        if not REQUIRED_REPOSITORY_KEYS <= relationship_keys:
            raise ProjectCardError(
                f"{label} repositories[{index}] misses required keys"
            )
        if not relationship_keys <= ALLOWED_REPOSITORY_KEYS:
            raise ProjectCardError(
                f"{label} repositories[{index}] has unsupported keys"
            )

        name = relationship["name"]
        role = relationship["role"]
        evidence = relationship["evidence"]
        if not isinstance(name, str) or not REPOSITORY_PATTERN.fullmatch(name):
            raise ProjectCardError(
                f"{label} repositories[{index}] has invalid name"
            )
        if not isinstance(role, str) or not role.strip():
            raise ProjectCardError(
                f"{label} repositories[{index}] has invalid role"
            )
        if not isinstance(evidence, str) or evidence not in source_set:
            raise ProjectCardError(
                f"{label} repositories[{index}] evidence is not listed in sources"
            )
        names.append(name)

        reference = relationship.get("reference")
        if reference is None:
            continue
        if not isinstance(reference, str) or not reference:
            raise ProjectCardError(
                f"{label} repositories[{index}] has invalid reference"
            )
        if reference not in source_set:
            raise ProjectCardError(
                f"{label} repositories[{index}] reference is not listed in sources"
            )
        if not reference.endswith("Repository Reference.md"):
            raise ProjectCardError(
                f"{label} repositories[{index}] reference has unexpected path"
            )

    if len(set(names)) != len(names):
        raise ProjectCardError(f"{label} repositories contain duplicate names")


def _validate_metadata(
    repo_root: Path,
    card_path: Path,
    text: str,
    metadata: dict[str, Any],
) -> None:
    label = card_path.relative_to(repo_root).as_posix()
    _validate_metadata_keys(metadata, label)
    if metadata["schema"] != SCHEMA:
        raise ProjectCardError(f"{label} has unsupported schema")

    card_id = metadata["id"]
    if not isinstance(card_id, str) or not ID_PATTERN.fullmatch(card_id):
        raise ProjectCardError(f"{label} has invalid id")
    if card_path.stem != card_id:
        raise ProjectCardError(
            f"{label} filename does not match metadata id {card_id!r}"
        )

    title = metadata["title"]
    if not isinstance(title, str) or not title.strip():
        raise ProjectCardError(f"{label} has invalid title")
    h1 = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if h1 is None or h1.group(1) != title:
        raise ProjectCardError(f"{label} H1 must equal metadata title")

    if metadata["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
        raise ProjectCardError(f"{label} has invalid evidence_status")

    reviewed_at = metadata["reviewed_at"]
    if not isinstance(reviewed_at, str):
        raise ProjectCardError(f"{label} reviewed_at must be an ISO date string")
    try:
        date.fromisoformat(reviewed_at)
    except ValueError as exc:
        raise ProjectCardError(f"{label} has invalid reviewed_at date") from exc

    section_bodies = {
        heading: _section_body(text, heading) for heading in REQUIRED_HEADINGS
    }
    source_set = _validate_sources(
        repo_root,
        label,
        metadata["sources"],
        section_bodies["## Quellen"],
    )
    _validate_repositories(label, metadata["repositories"], source_set)


def validate_project_cards(repo_root: Path) -> list[dict[str, Any]]:
    repo_root = _require_directory(repo_root, "repository root")
    project_dir = _require_directory(repo_root / PROJECT_DIR, "project card directory")
    index_path = _require_regular_file(repo_root, INDEX_RELATIVE, "project card index")
    index_text = index_path.read_text(encoding="utf-8", errors="strict")

    card_paths: list[Path] = []
    for entry in sorted(project_dir.iterdir(), key=lambda path: path.name.casefold()):
        if entry.name == "index.md":
            continue
        if entry.suffix != ".md":
            raise ProjectCardError(
                f"unexpected non-card entry in project directory: {entry.name}"
            )
        _reject_symlink_components(entry, "project card")
        if not stat.S_ISREG(os.lstat(entry).st_mode):
            raise ProjectCardError(f"project card is not a regular file: {entry.name}")
        card_paths.append(entry)
    if not card_paths:
        raise ProjectCardError("project card directory contains no cards")

    cards: list[dict[str, Any]] = []
    ids: set[str] = set()
    for card_path in card_paths:
        text = card_path.read_text(encoding="utf-8", errors="strict")
        metadata = _load_metadata(text, card_path.name)
        _validate_metadata(repo_root, card_path, text, metadata)
        card_id = metadata["id"]
        if card_id in ids:
            raise ProjectCardError(f"duplicate project card id: {card_id}")
        ids.add(card_id)
        link = f"]({card_path.name})"
        if index_text.count(link) != 1:
            raise ProjectCardError(
                f"project card index must link {card_path.name} exactly once"
            )
        cards.append(metadata)

    linked_cards = set(LOCAL_CARD_LINK_PATTERN.findall(index_text))
    expected_cards = {path.name for path in card_paths}
    unexpected = sorted(linked_cards - expected_cards)
    if unexpected:
        raise ProjectCardError(
            f"project card index links unknown card files: {unexpected}"
        )
    return cards


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cards = validate_project_cards(args.repo_root)
    except (ProjectCardError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("PROJECT-CARD-GUARD: PASS")
    print(f"Cards: {len(cards)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
