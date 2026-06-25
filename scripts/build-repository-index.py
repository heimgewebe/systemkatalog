#!/usr/bin/env python3
"""Build the deterministic Cabinet repository snapshot catalogue."""

from __future__ import annotations

import argparse
import difflib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT = Path("bestand/10 Repositories/index.md")
REFERENCE_PATHSPEC = ":(glob)**/Repository Reference.md"
REQUIRED_HEADINGS = (
    "Provenienz",
    "Geprüfter Review-Snapshot",
    "Live-Snapshot beim Import",
    "Identität",
)
OPTIONAL_ROLE_HEADING = "Kanonische Systemrolle"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
WORKTREE_RE = re.compile(r"^(clean|dirty):([0-9]+)$")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
VISIBLE_HASH_LENGTH = 12
VISIBLE_ROLE_WORDS = 5


class InventoryError(RuntimeError):
    """Raised when a repository reference violates the extraction contract."""


@dataclass(frozen=True)
class RepositoryRecord:
    repository: str
    role: str | None
    origin: str
    default_branch: str | None
    review_head: str
    import_head: str
    relationship: str
    import_worktree: str
    imported_at: str
    source_path: str


def _run_git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise InventoryError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise InventoryError(f"git {' '.join(args)} failed: {detail}") from exc
    return completed.stdout


def tracked_reference_paths(repo_root: Path) -> list[str]:
    raw = _run_git(repo_root, "ls-files", "-z", "--", REFERENCE_PATHSPEC)
    paths = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    return sorted(paths, key=lambda value: (value.casefold(), value))


def _strip_wrapper(value: str) -> str:
    value = value.strip()
    changed = True
    while changed and value:
        changed = False
        for prefix, suffix in (("`", "`"), ("**", "**"), ("__", "__")):
            if value.startswith(prefix) and value.endswith(suffix):
                value = value[len(prefix) : -len(suffix)].strip()
                changed = True
    return value


def _split_sections(text: str, source_path: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            if current in sections:
                raise InventoryError(
                    f"{source_path}: duplicate section heading: {current}"
                )
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    missing = [heading for heading in REQUIRED_HEADINGS if heading not in sections]
    if missing:
        raise InventoryError(
            f"{source_path}: missing required section(s): {', '.join(missing)}"
        )
    return sections


def _parse_field_table(
    lines: list[str], source_path: str, section: str
) -> dict[str, str]:
    rows: dict[str, str] = {}
    header_seen = False
    separator_seen = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            if header_seen and separator_seen and rows:
                break
            continue

        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) != 2:
            raise InventoryError(
                f"{source_path}: malformed table row in {section}: {raw_line}"
            )
        left, right = cells
        if not header_seen:
            if left != "Feld" or right != "Wert":
                continue
            header_seen = True
            continue
        if not separator_seen:
            if TABLE_SEPARATOR_RE.fullmatch(left) and TABLE_SEPARATOR_RE.fullmatch(right):
                separator_seen = True
                continue
            raise InventoryError(
                f"{source_path}: malformed table separator in {section}"
            )

        key = _strip_wrapper(left)
        value = _strip_wrapper(right)
        if not key:
            raise InventoryError(f"{source_path}: empty field name in {section}")
        if key in rows:
            raise InventoryError(
                f"{source_path}: duplicate field {key!r} in {section}"
            )
        rows[key] = value

    if not header_seen or not separator_seen:
        raise InventoryError(f"{source_path}: field table missing in {section}")
    return rows


def _parse_role(lines: list[str]) -> str | None:
    quote_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith(">"):
            value = _strip_wrapper(line[1:].strip())
            if value.startswith("- "):
                value = value[2:].strip()
            if value:
                quote_lines.append(value)
        elif quote_lines:
            break
    return " ".join(quote_lines) or None


def _require(table: dict[str, str], key: str, source_path: str, section: str) -> str:
    value = table.get(key, "").strip()
    if not value or value == "<fehlt>":
        raise InventoryError(f"{source_path}: required field {section}/{key} missing")
    return value


def _validate_commit(value: str, source_path: str, label: str) -> None:
    if not COMMIT_RE.fullmatch(value):
        raise InventoryError(f"{source_path}: invalid {label}: {value!r}")


def _validate_timestamp(value: str, source_path: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InventoryError(
            f"{source_path}: invalid import timestamp: {value!r}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InventoryError(
            f"{source_path}: import timestamp must include a timezone: {value!r}"
        )


def _validate_worktree(value: str, source_path: str) -> None:
    match = WORKTREE_RE.fullmatch(value)
    if match is None:
        raise InventoryError(
            f"{source_path}: invalid import Working Tree value: {value!r}"
        )
    state, raw_count = match.groups()
    count = int(raw_count)
    if state == "clean" and count != 0:
        raise InventoryError(
            f"{source_path}: contradictory import Working Tree value: {value!r}"
        )
    if state == "dirty" and count == 0:
        raise InventoryError(
            f"{source_path}: contradictory import Working Tree value: {value!r}"
        )


def _validate_relationship(
    relationship: str, review_head: str, import_head: str, source_path: str
) -> None:
    normalized = relationship.casefold()
    if normalized == "identisch" and review_head != import_head:
        raise InventoryError(
            f"{source_path}: relationship 'identisch' contradicts differing HEADs"
        )
    if review_head == import_head and (
        "divergent" in normalized or "rewritten" in normalized or "amended" in normalized
    ):
        raise InventoryError(
            f"{source_path}: divergent relationship contradicts identical HEADs"
        )


def parse_reference(repo_root: Path, source_path: str) -> RepositoryRecord:
    path = repo_root / source_path
    if not path.is_file():
        raise InventoryError(f"tracked reference is not a file: {source_path}")
    text = path.read_text(encoding="utf-8", errors="strict")
    if not text.endswith("\n"):
        raise InventoryError(f"{source_path}: final newline missing")

    sections = _split_sections(text, source_path)
    provenance = _parse_field_table(sections["Provenienz"], source_path, "Provenienz")
    review = _parse_field_table(
        sections["Geprüfter Review-Snapshot"],
        source_path,
        "Geprüfter Review-Snapshot",
    )
    imported = _parse_field_table(
        sections["Live-Snapshot beim Import"],
        source_path,
        "Live-Snapshot beim Import",
    )
    identity = _parse_field_table(sections["Identität"], source_path, "Identität")
    role = _parse_role(sections.get(OPTIONAL_ROLE_HEADING, []))

    repository = _require(review, "Repository", source_path, "Geprüfter Review-Snapshot")
    review_origin = _require(review, "Origin", source_path, "Geprüfter Review-Snapshot")
    review_path = _require(review, "Pfad", source_path, "Geprüfter Review-Snapshot")
    review_head = _require(review, "HEAD", source_path, "Geprüfter Review-Snapshot")
    import_origin = _require(imported, "Origin", source_path, "Live-Snapshot beim Import")
    import_path = _require(imported, "Pfad", source_path, "Live-Snapshot beim Import")
    import_head = _require(imported, "HEAD", source_path, "Live-Snapshot beim Import")
    import_worktree = _require(
        imported, "Working Tree", source_path, "Live-Snapshot beim Import"
    )
    relationship = _require(
        imported, "Beziehung zum Review", source_path, "Live-Snapshot beim Import"
    )
    imported_at = _require(
        provenance, "Import-Snapshot erfasst", source_path, "Provenienz"
    )
    live_captured_at = _require(
        imported, "Erfasst", source_path, "Live-Snapshot beim Import"
    )
    canonical_path = _require(identity, "Kanonischer Pfad", source_path, "Identität")
    canonical_remote = _require(identity, "Remote", source_path, "Identität")
    default_branch = identity.get("Default-Branch") or None

    if len({review_origin, import_origin, canonical_remote}) != 1:
        raise InventoryError(f"{source_path}: contradictory repository origin values")
    if len({review_path, import_path, canonical_path}) != 1:
        raise InventoryError(f"{source_path}: contradictory repository path values")
    if imported_at != live_captured_at:
        raise InventoryError(f"{source_path}: contradictory import timestamps")

    _validate_commit(review_head, source_path, "review HEAD")
    _validate_commit(import_head, source_path, "import HEAD")
    _validate_timestamp(imported_at, source_path)
    _validate_worktree(import_worktree, source_path)
    _validate_relationship(relationship, review_head, import_head, source_path)

    return RepositoryRecord(
        repository=repository,
        role=role,
        origin=review_origin,
        default_branch=default_branch,
        review_head=review_head,
        import_head=import_head,
        relationship=relationship,
        import_worktree=import_worktree,
        imported_at=imported_at,
        source_path=source_path,
    )


def load_records(repo_root: Path) -> tuple[list[RepositoryRecord], list[str]]:
    paths = tracked_reference_paths(repo_root)
    if not paths:
        raise InventoryError("no tracked Repository Reference.md files found")

    records = [parse_reference(repo_root, path) for path in paths]
    warnings = [
        f"{record.source_path}: optional role missing"
        for record in records
        if record.role is None
    ]
    seen: dict[str, str] = {}
    for record in records:
        key = record.repository.casefold()
        previous = seen.get(key)
        if previous is not None:
            raise InventoryError(
                "duplicate repository identity "
                f"{record.repository!r}: {previous} and {record.source_path}"
            )
        seen[key] = record.source_path

    records.sort(
        key=lambda record: (
            record.repository.casefold(),
            record.repository,
            record.source_path,
        )
    )
    return records, warnings


def _escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _code(value: str | None) -> str:
    if not value:
        return "—"
    return f"`{_escape_cell(value)}`"


def _short_hash(value: str) -> str:
    return value[:VISIBLE_HASH_LENGTH]


def _role_excerpt(value: str | None) -> str:
    if not value:
        return "—"
    plain = value.replace("`", "").replace("**", "").replace("__", "")
    words = plain.split()
    excerpt = " ".join(words[:VISIBLE_ROLE_WORDS])
    if len(words) > VISIBLE_ROLE_WORDS:
        excerpt += " ..."
    return _escape_cell(excerpt)


def render_index(records: list[RepositoryRecord], output_path: Path) -> str:
    lines = [
        "# Repositories",
        "",
        "<!-- GENERATED: scripts/build-repository-index.py -->",
        "> **Generierte Datei. Nicht manuell bearbeiten.**",
        "> Quelle: versionierte `Repository Reference.md`-Dateien.",
        "> **Zeitgrenze:** Die Werte sind datierte Import-Snapshots und keine Aussage über den aktuellen Zustand der Quell-Repositories.",
        "> `Repository Reference.md` bleibt die versionierte Detail- und Evidenzquelle; dieser Index ist nur eine Übersicht.",
        "",
        "| Repository | Rollen-Auszug | Review-HEAD | Import-HEAD | Beziehung beim Import | Import-Worktree | Erfasst | Referenzpfad |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                (
                    _code(record.repository),
                    _role_excerpt(record.role),
                    _code(_short_hash(record.review_head)),
                    _code(_short_hash(record.import_head)),
                    _escape_cell(record.relationship),
                    _code(record.import_worktree),
                    _code(record.imported_at),
                    _code(record.source_path),
                )
            )
            + " |"
        )
    lines.extend(("", f"Tracked references: **{len(records)}**", ""))
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _limited_diff(current: str, expected: str, path: Path) -> str:
    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile=str(path),
            tofile=f"{path} (expected)",
            lineterm="",
        )
    )
    limit = 200
    if len(diff) > limit:
        diff = diff[:limit] + [f"... diff truncated after {limit} lines ..."]
    return "\n".join(diff)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument(
        "--repo-root", default=".", help="Git repository root (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"output path relative to the repository (default: {DEFAULT_OUTPUT})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    raw_output = Path(args.output)
    output_path = (
        raw_output.resolve()
        if raw_output.is_absolute()
        else (repo_root / raw_output).resolve()
    )

    try:
        try:
            relative_output = output_path.relative_to(repo_root)
        except ValueError as exc:
            raise InventoryError(
                f"output path escapes repository: {output_path}"
            ) from exc
        records, warnings = load_records(repo_root)
        expected = render_index(records, relative_output)
        current = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""

        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        if args.check:
            if current != expected:
                print(
                    f"ERROR: repository inventory is stale: {relative_output}",
                    file=sys.stderr,
                )
                print(_limited_diff(current, expected, output_path), file=sys.stderr)
                return 1
            print(
                "Repository inventory: PASS "
                f"({len(records)} tracked references, {len(warnings)} warnings)"
            )
            return 0

        if current == expected:
            print(
                "Repository inventory unchanged "
                f"({len(records)} tracked references, {len(warnings)} warnings)"
            )
            return 0

        _atomic_write(output_path, expected)
        print(
            "Repository inventory written "
            f"({len(records)} tracked references, {len(warnings)} warnings)"
        )
        return 0
    except (InventoryError, UnicodeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
