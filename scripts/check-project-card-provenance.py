#!/usr/bin/env python3
"""Verify that Project Card inputs are tracked, regular, and index-identical."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_DIR = Path("bestand/20 Projekte")
VALIDATOR_PATH = Path(__file__).resolve().with_name("check-project-cards.py")


class ProvenanceError(RuntimeError):
    """Raised when a card or source lacks trustworthy Git provenance."""


@dataclass(frozen=True)
class IndexEntry:
    path: str
    object_id: str
    mode: str
    stage: str


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("project_card_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise ProvenanceError("cannot load project card validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ProvenanceError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ProvenanceError(f"git {' '.join(args)} failed: {detail}") from exc
    return completed.stdout


def _index_entry(repo_root: Path, relative: Path) -> IndexEntry:
    raw_path = relative.as_posix()
    if any(character in raw_path for character in ("\x00", "\n", "\r")):
        raise ProvenanceError(f"unsafe path character: {raw_path!r}")
    raw = _run_git(
        repo_root,
        "ls-files",
        "-s",
        "-z",
        "--error-unmatch",
        "--",
        f":(literal){raw_path}",
    )
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        raise ProvenanceError(
            f"expected one Git index entry for {raw_path}; found {len(entries)}"
        )
    try:
        metadata, encoded_path = entries[0].split(b"\t", 1)
        mode, object_id, stage = metadata.split(b" ", 2)
        entry = IndexEntry(
            path=encoded_path.decode("utf-8"),
            object_id=object_id.decode("ascii"),
            mode=mode.decode("ascii"),
            stage=stage.decode("ascii"),
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProvenanceError(f"malformed Git index entry for {raw_path}") from exc
    if entry.path != raw_path:
        raise ProvenanceError(
            f"Git index path mismatch: {entry.path!r} != {raw_path!r}"
        )
    if entry.mode not in {"100644", "100755"} or entry.stage != "0":
        raise ProvenanceError(
            f"{raw_path} must be a regular Git blob at stage 0; "
            f"found mode {entry.mode}, stage {entry.stage}"
        )
    return entry


def _verify_index_identical(repo_root: Path, relative: Path) -> None:
    entry = _index_entry(repo_root, relative)
    path = repo_root / relative
    try:
        working_bytes = path.read_bytes()
    except OSError as exc:
        raise ProvenanceError(f"cannot read working file {relative.as_posix()}") from exc
    indexed_bytes = _run_git(repo_root, "cat-file", "blob", entry.object_id)
    if working_bytes != indexed_bytes:
        raise ProvenanceError(
            f"working file differs from indexed blob: {relative.as_posix()}"
        )


def verify_provenance(repo_root: Path) -> list[Path]:
    repo_root = Path(os.path.abspath(repo_root.expanduser()))
    validator = _load_validator()
    cards = validator.validate_project_cards(repo_root)

    required_paths: set[Path] = {PROJECT_DIR / "index.md"}
    for metadata in cards:
        required_paths.add(PROJECT_DIR / f"{metadata['id']}.md")
        required_paths.update(Path(source) for source in metadata["sources"])

    ordered = sorted(required_paths, key=lambda path: (path.as_posix().casefold(), path.as_posix()))
    for relative in ordered:
        _verify_index_identical(repo_root, relative)
    return ordered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        paths = verify_provenance(args.repo_root)
    except (ProvenanceError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("PROJECT-CARD-PROVENANCE: PASS")
    print(f"Tracked inputs: {len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
