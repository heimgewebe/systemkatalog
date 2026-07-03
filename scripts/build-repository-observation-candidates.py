#!/usr/bin/env python3
"""Build deterministic candidate views from Cabinet repository snapshots.

This generator turns historical Repository Reference snapshot assessments into
reviewable work candidates. A candidate is not a Bureau task, not a dispatch
request, and not a permission to mutate any source repository.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATED_MARKER = "<!-- GENERATED: scripts/build-repository-observation-candidates.py -->"
DEFAULT_OUTPUT = Path("steuerung/20 Aufgaben/repository-observation-candidates-v1.md")


def _load_module(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


inventory = _load_module("scripts.repository_inventory", SCRIPT_DIR / "repository_inventory.py")
model = _load_module("scripts.snapshot_review_model", SCRIPT_DIR / "snapshot_review_model.py")

InventoryError = inventory.InventoryError
SnapshotAssessment = model.SnapshotAssessment


def _escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _code(value: str) -> str:
    return f"`{_escape_cell(value)}`"


def _candidate_kind(item: SnapshotAssessment) -> str | None:
    if item.reason_code == "verify-divergence":
        return "live-history-verification"
    if item.reason_code == "refresh-dirty":
        return "live-snapshot-refresh"
    if item.reason_code == "verify-nonidentical":
        return "live-relationship-verification"
    if item.reason_code == "routine":
        return None
    raise AssertionError(f"unknown reason code: {item.reason_code!r}")


def _candidate_action(item: SnapshotAssessment) -> str:
    if item.reason_code == "verify-divergence":
        return "Divergenz- oder Rewrite-Claim gegen Git-Historie prüfen, bevor Reparaturarbeit geplant wird."
    if item.reason_code == "refresh-dirty":
        return "Repository-Beobachtung aktualisieren, nachdem geprüft wurde, ob der Dirty-Import noch relevant ist."
    if item.reason_code == "verify-nonidentical":
        return "Nicht-identische Commitbeziehung gegen Live-Git prüfen, bevor Folgearbeit vorgeschlagen wird."
    raise AssertionError(f"routine items have no candidate action: {item.repository}")


def _candidate_boundary(item: SnapshotAssessment) -> str:
    if item.reason_code == "refresh-dirty":
        return "Nur historischer Dirty-Import; heutiger Worktree unbekannt."
    if item.reason_code == "verify-divergence":
        return "Nur Reference-Claim; kein Live-Historienbeweis in diesem Lauf."
    if item.reason_code == "verify-nonidentical":
        return "Nur gespeicherter Beziehungs-Claim; heutiger Repozustand unbekannt."
    raise AssertionError(f"routine items have no candidate boundary: {item.repository}")


def _times(items: list[SnapshotAssessment]) -> str:
    values = sorted({item.imported_at for item in items})
    return ", ".join(_code(value) for value in values)


def _candidate_items(items: list[SnapshotAssessment]) -> list[SnapshotAssessment]:
    return [item for item in model.priority_order(items) if _candidate_kind(item) is not None]


def _routine_items(items: list[SnapshotAssessment]) -> list[SnapshotAssessment]:
    return [item for item in model.priority_order(items) if _candidate_kind(item) is None]


def render_candidates(items: list[SnapshotAssessment]) -> str:
    candidates = _candidate_items(items)
    routines = _routine_items(items)
    lines = [
        "# Repository Observation Candidates v1",
        "",
        GENERATED_MARKER,
        "> **Generierte Datei. Nicht manuell bearbeiten.**",
        "> Quelle: versionierte `Repository Reference.md`-Dateien und deterministische Snapshot-Bewertungen.",
        "> **Grenze:** Diese Datei erzeugt Kandidaten, keine Bureau-Tasks, keine Claims, keine Dispatches und keine Merge-Rechte.",
        "",
        "## Kurzlage",
        "",
        f"- Geprüfte Repository-Snapshots: **{len(items)}**",
        f"- Kandidaten: **{len(candidates)}**",
        f"- Routine-/Nicht-Kandidaten: **{len(routines)}**",
        "- Snapshot-Zeitpunkt(e): " + _times(items),
        "- Aktueller Zustand der Quell-Repositories: **unbekannt**",
        "",
        "## Kandidaten",
        "",
        "| Rang | Repository | Kandidatentyp | Vorgeschlagene nächste Prüfung | Snapshotgrenze | Quelle |",
        "|---:|---|---|---|---|---|",
    ]
    if not candidates:
        lines.append("| — | — | — | Keine Kandidaten aus den gespeicherten Snapshots ableitbar. | — | — |")
    for item in candidates:
        lines.append(
            f"| {item.priority} | {_code(item.repository)} | "
            f"{_code(_candidate_kind(item) or 'none')} | "
            f"{_escape_cell(_candidate_action(item))} | "
            f"{_escape_cell(_candidate_boundary(item))} | "
            f"{_code(item.source_path)} |"
        )

    lines.extend(
        (
            "",
            "## Routine- oder Nicht-Kandidaten",
            "",
            "| Repository | Grund | Quelle |",
            "|---|---|---|",
        )
    )
    if not routines:
        lines.append("| — | — | — |")
    for item in routines:
        lines.append(
            f"| {_code(item.repository)} | "
            "Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | "
            f"{_code(item.source_path)} |"
        )

    lines.extend(
        (
            "",
            "## Promotionsregeln",
            "",
            "- Ein Kandidat ist nur ein Hinweis auf eine spätere Prüfung.",
            "- Promotion zu Bureau benötigt eine separate menschliche Entscheidung und ein eigenes, versioniertes Task-Artefakt.",
            "- Dieser Report liest keine heutigen Quell-Repositories und darf deshalb keine aktuelle Readiness behaupten.",
            "- Dirty-, Divergenz- und nicht-identische Commit-Befunde müssen vor jeder Umsetzung live geprüft werden.",
            "",
            "## Epistemische Leerstellen",
            "",
            "- Aktuelle Branches, HEADs, Worktrees, CI und Runtime-Zustände der Quell-Repositories fehlen.",
            "- Ob ein Kandidat fachlich wichtig ist, kann aus Snapshotdaten allein nicht entschieden werden.",
            "- Ob Bureau, Grabowski, Steuerboard oder ein Mensch zuständig ist, bleibt pro Kandidat separat zu klären.",
            "",
        )
    )
    return "\n".join(lines)


def _resolve_output(repo_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    lexical = Path(os.path.abspath(candidate if candidate.is_absolute() else repo_root / candidate))
    try:
        relative = lexical.relative_to(repo_root)
    except ValueError as exc:
        raise InventoryError(f"candidate output path escapes repository: {lexical}") from exc
    if not relative.parts:
        raise InventoryError("candidate output path must name a Markdown file")
    if ".git" in relative.parts:
        raise InventoryError("candidate output path may not target Git metadata")
    if lexical.suffix.casefold() != ".md":
        raise InventoryError(f"candidate output path must end in .md: {relative}")
    cursor = repo_root
    for component in relative.parts:
        cursor /= component
        if cursor.is_symlink():
            raise InventoryError(f"candidate output path may not contain symlinks: {relative}")
    return lexical


def _is_tracked(repo_root: Path, path: Path) -> bool:
    relative = path.relative_to(repo_root).as_posix()
    return bool(inventory._run_git(repo_root, "ls-files", "-z", "--", relative))


def _canonical_outputs(repo_root: Path) -> set[Path]:
    return {(repo_root / DEFAULT_OUTPUT).resolve()}


def _preflight_output(repo_root: Path, output: Path, source_paths: set[Path], *, check_mode: bool) -> None:
    relative = output.relative_to(repo_root)
    canonical = _canonical_outputs(repo_root)
    if output in source_paths:
        raise InventoryError(f"candidate output collides with a source reference: {relative}")
    tracked = _is_tracked(repo_root, output)
    if tracked and output not in canonical:
        raise InventoryError(f"candidate output is not an approved generated target: {relative}")
    if output.exists() and not output.is_file():
        raise InventoryError(f"candidate output is not a regular file: {relative}")
    if not check_mode and output.exists() and not tracked and output not in canonical:
        current = output.read_text(encoding="utf-8")
        if GENERATED_MARKER not in current:
            raise InventoryError(f"candidate output is not a generated file: {relative}")


def _read_current(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


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
    limit = 160
    if len(diff) > limit:
        diff = diff[:limit] + [f"... diff truncated after {limit} lines ..."]
    return "\n".join(diff)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        output = _resolve_output(repo_root, args.output)
        records, warnings = inventory.load_records(repo_root, verify_index_match=True)
        source_paths = {(repo_root / record.source_path).resolve() for record in records}
        _preflight_output(repo_root, output, source_paths, check_mode=args.check)
        items = model.build_assessments(records)
        expected = render_candidates(items)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        current = _read_current(output) or ""
        if args.check:
            if current != expected:
                print(
                    f"ERROR: repository observation candidates are stale: {output.relative_to(repo_root)}",
                    file=sys.stderr,
                )
                print(_limited_diff(current, expected, output), file=sys.stderr)
                return 1
            print(
                "Repository observation candidates: PASS "
                f"({len(_candidate_items(items))} candidates, {len(warnings)} warnings)"
            )
            return 0
        if current != expected:
            inventory._atomic_write(output, expected)
            print(
                "Repository observation candidates written "
                f"({len(_candidate_items(items))} candidates, 1 file changed, {len(warnings)} warnings)"
            )
        else:
            print(
                "Repository observation candidates unchanged "
                f"({len(_candidate_items(items))} candidates, {len(warnings)} warnings)"
            )
        return 0
    except (InventoryError, UnicodeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
