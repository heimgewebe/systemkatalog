#!/usr/bin/env python3
"""Build the deterministic Cabinet repository snapshot catalogue.

The Git index discovers and authorizes tracked references. Local write mode
reads current regular working-tree files; check mode rejects reference drift
between the working tree and the indexed blob before rendering. Working-tree
reference paths are opened component by component from the repository root
without following symlinks.
"""

from __future__ import annotations

import argparse
import difflib
import errno
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT = Path("bestand/10 Repositories/index.md")
REFERENCE_PATHSPEC = ":(glob)**/Repository Reference.md"
GENERATED_FILE_MODE = 0o644
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
class TrackedReference:
    source_path: str
    object_id: str


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
    relationship_verification: str | None = None


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


def tracked_references(repo_root: Path) -> list[TrackedReference]:
    raw = _run_git(repo_root, "ls-files", "-s", "-z", "--", REFERENCE_PATHSPEC)
    references: list[TrackedReference] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, encoded_path = entry.split(b"\t", 1)
            mode, object_id, stage = metadata.split(b" ", 2)
            source_path = encoded_path.decode("utf-8")
            object_id_text = object_id.decode("ascii")
            mode_text = mode.decode("ascii")
            stage_text = stage.decode("ascii")
        except (UnicodeDecodeError, ValueError) as exc:
            raise InventoryError(
                "malformed git index entry for repository reference"
            ) from exc
        if mode_text != "100644" or stage_text != "0":
            raise InventoryError(
                f"{source_path}: tracked reference must use git mode 100644 "
                f"at stage 0; found mode {mode_text}, stage {stage_text}"
            )
        references.append(
            TrackedReference(source_path=source_path, object_id=object_id_text)
        )
    return sorted(
        references,
        key=lambda reference: (reference.source_path.casefold(), reference.source_path),
    )


def read_index_blob(repo_root: Path, object_id: str) -> bytes:
    return _run_git(repo_root, "cat-file", "blob", object_id)


def _required_os_flag(name: str) -> int:
    value = getattr(os, name, None)
    if value is None:
        raise InventoryError(
            f"platform lacks required {name} support for safe reference path traversal"
        )
    return value


def _reference_path_components(source_path: str) -> list[str]:
    if not source_path or os.path.isabs(source_path):
        raise InventoryError(f"{source_path}: invalid tracked reference path")

    components = source_path.split("/")
    for component in components:
        if component in ("", ".", ".."):
            raise InventoryError(
                f"{source_path}: invalid tracked reference path component: "
                f"{component!r}"
            )
    return components


def _open_root_directory(repo_root: Path) -> int:
    flags = (
        os.O_RDONLY
        | _required_os_flag("O_DIRECTORY")
        | _required_os_flag("O_CLOEXEC")
    )
    try:
        return os.open(repo_root, flags)
    except FileNotFoundError as exc:
        raise InventoryError(f"repository root missing: {repo_root}") from exc
    except NotADirectoryError as exc:
        raise InventoryError(f"repository root is not a directory: {repo_root}") from exc


def _open_parent_directory(source_path: str, component: str, directory_fd: int) -> int:
    flags = (
        os.O_RDONLY
        | _required_os_flag("O_DIRECTORY")
        | _required_os_flag("O_NOFOLLOW")
        | _required_os_flag("O_CLOEXEC")
    )
    try:
        descriptor = os.open(component, flags, dir_fd=directory_fd)
    except FileNotFoundError as exc:
        raise InventoryError(
            f"{source_path}: parent path component {component!r} missing from "
            "working tree"
        ) from exc
    except NotADirectoryError as exc:
        raise InventoryError(
            f"{source_path}: unsafe or non-directory parent path component "
            f"{component!r}"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise InventoryError(
                f"{source_path}: parent path component {component!r} must be a "
                "real directory, not a symlink"
            ) from exc
        if exc.errno == errno.ENOENT:
            raise InventoryError(
                f"{source_path}: parent path component {component!r} missing "
                "from working tree"
            ) from exc
        if exc.errno == errno.ENOTDIR:
            raise InventoryError(
                f"{source_path}: unsafe or non-directory parent path component "
                f"{component!r}"
            ) from exc
        raise

    try:
        metadata = os.fstat(descriptor)
    except Exception:
        os.close(descriptor)
        raise
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(descriptor)
        raise InventoryError(
            f"{source_path}: unsafe or non-directory parent path component "
            f"{component!r}"
        )
    return descriptor


def _open_reference_file(source_path: str, filename: str, directory_fd: int) -> int:
    flags = (
        os.O_RDONLY
        | _required_os_flag("O_NOFOLLOW")
        | _required_os_flag("O_CLOEXEC")
        | _required_os_flag("O_NONBLOCK")
    )
    try:
        descriptor = os.open(filename, flags, dir_fd=directory_fd)
    except FileNotFoundError as exc:
        raise InventoryError(
            f"{source_path}: tracked reference missing from working tree"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise InventoryError(
                f"{source_path}: tracked reference working tree path must be a "
                "regular file, not a symlink"
            ) from exc
        if exc.errno == errno.ENOENT:
            raise InventoryError(
                f"{source_path}: tracked reference missing from working tree"
            ) from exc
        if exc.errno == errno.ENOTDIR:
            raise InventoryError(
                f"{source_path}: unsafe or non-directory parent path component"
            ) from exc
        raise
    return descriptor


def read_worktree_reference(repo_root: Path, source_path: str) -> bytes:
    if os.open not in os.supports_dir_fd:
        raise InventoryError(
            "platform lacks dir_fd support for safe reference path traversal"
        )

    components = _reference_path_components(source_path)
    current_directory_fd = _open_root_directory(repo_root)

    try:
        for component in components[:-1]:
            next_directory_fd = _open_parent_directory(
                source_path, component, current_directory_fd
            )
            old_directory_fd = current_directory_fd
            current_directory_fd = -1
            try:
                os.close(old_directory_fd)
            except Exception:
                os.close(next_directory_fd)
                raise
            current_directory_fd = next_directory_fd

        descriptor = _open_reference_file(
            source_path, components[-1], current_directory_fd
        )
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise InventoryError(
                    f"{source_path}: tracked reference working tree path must "
                    "be a regular file"
                )

            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                return handle.read()
        finally:
            if descriptor != -1:
                os.close(descriptor)
    finally:
        if current_directory_fd != -1:
            os.close(current_directory_fd)


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


def _split_table_cells(
    line: str, source_path: str, section: str, raw_line: str
) -> list[str]:
    """Split a two-column Markdown row without treating escaped pipes as separators."""
    cells: list[str] = []
    current: list[str] = []
    consecutive_backslashes = 0

    for character in line[1:-1]:
        if character == "\\":
            current.append(character)
            consecutive_backslashes += 1
            continue

        if character == "|":
            if consecutive_backslashes % 2:
                current.pop()
                current.append("|")
            else:
                cells.append("".join(current).strip())
                current = []
            consecutive_backslashes = 0
            continue

        consecutive_backslashes = 0
        current.append(character)

    cells.append("".join(current).strip())
    if len(cells) != 2:
        raise InventoryError(
            f"{source_path}: malformed table row in {section}: {raw_line}"
        )
    return cells


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

        cells = _split_table_cells(line, source_path, section, raw_line)
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


def parse_reference(source_path: str, content: bytes) -> RepositoryRecord:
    text = content.decode("utf-8", errors="strict")
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
    verification_table = (
        _parse_field_table(sections["Live-Verifikation"], source_path, "Live-Verifikation")
        if "Live-Verifikation" in sections
        else {}
    )
    relationship_verification = verification_table.get("Beziehung zum Review") or None

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
        relationship_verification=relationship_verification,
    )


def load_records(
    repo_root: Path, *, verify_index_match: bool = False
) -> tuple[list[RepositoryRecord], list[str]]:
    references = tracked_references(repo_root)
    if not references:
        raise InventoryError("no tracked Repository Reference.md files found")

    records: list[RepositoryRecord] = []
    for reference in references:
        content = read_worktree_reference(repo_root, reference.source_path)
        if verify_index_match:
            indexed_content = read_index_blob(repo_root, reference.object_id)
            if content != indexed_content:
                raise InventoryError(
                    f"{reference.source_path}: tracked reference differs from "
                    "git index"
                )
        records.append(parse_reference(reference.source_path, content))
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


def render_index(records: list[RepositoryRecord]) -> str:
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
            os.fchmod(handle.fileno(), GENERATED_FILE_MODE)
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
        records, warnings = load_records(repo_root, verify_index_match=args.check)
        expected = render_index(records)
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
