#!/usr/bin/env python3
"""Build deterministic review and Lage views from Cabinet repository snapshots."""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

SCRIPT_DIR = Path(__file__).resolve().parent


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


inventory = _load_module(
    "scripts.repository_inventory", SCRIPT_DIR / "repository_inventory.py"
)
model = _load_module(
    "scripts.snapshot_review_model", SCRIPT_DIR / "snapshot_review_model.py"
)
constants = _load_module(
    "scripts.snapshot_review_constants", SCRIPT_DIR / "snapshot_review_constants.py"
)

InventoryError = inventory.InventoryError
RepositoryRecord = inventory.RepositoryRecord
SnapshotAssessment = model.SnapshotAssessment
assess_record = model.assess_record
build_assessments = model.build_assessments
priority_order = model.priority_order
DEFAULT_REVIEW_OUTPUT = constants.REVIEW_OUTPUT
DEFAULT_LAGE_OUTPUT = constants.LAGE_OUTPUT


def _escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _code(value: str) -> str:
    return f"`{_escape_cell(value)}`"


def _times(items: list[SnapshotAssessment]) -> str:
    values = sorted({item.imported_at for item in items})
    return ", ".join(_code(value) for value in values)


def _evidence_text(item: SnapshotAssessment) -> str:
    if item.evidence_status == "direct-head-equality":
        return "direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch"
    if item.relationship_class == "snapshot-divergence-claimed":
        return "reference-claim: Divergenz oder umgeschriebene Historie wurde behauptet"
    if item.relationship_class == "snapshot-review-contained":
        return "reference-claim: der Importstand soll den Reviewstand enthalten"
    return "reference-claim: Beziehung wurde nicht durch Cabinet live verifiziert"


def _reason_text(item: SnapshotAssessment, detailed: bool) -> str:
    if item.reason_code == "verify-divergence":
        if detailed:
            return "Divergenz- oder Rewrite-Claim später in Git verifizieren"
        return "Divergenz- oder Rewrite-Claim später in Git prüfen"
    if item.reason_code.startswith("refresh-dirty-"):
        count = item.reason_code.rsplit("-", 1)[1]
        return f"damals {count} Working-Tree-Änderungen; später neu erheben"
    if item.reason_code == "verify-nonidentical":
        if detailed:
            return "nicht-identische Commitbeziehung später live prüfen"
        return "nicht-identische Commitbeziehung später prüfen"
    return "keine besondere Priorität aus dem Snapshot ableitbar"


def render_review(items: list[SnapshotAssessment]) -> str:
    relationships = Counter(item.relationship_class for item in items)
    worktrees = Counter(item.worktree_class for item in items)
    lines = [
        "# Repository Snapshot Review v1",
        "",
        "<!-- GENERATED: scripts/build-repository-snapshot-review.py -->",
        "> **Generierte Datei. Nicht manuell bearbeiten.**",
        "> Quelle: versionierte `Repository Reference.md`-Dateien in Cabinet.",
        "> **Zeitgrenze:** Diese Prüfung bewertet ausschließlich gespeicherte Import-Snapshots. Sie prüft keine heutigen Repositoryzustände.",
        "",
        "## Laufvertrag",
        "",
        "- Live-Zugriff auf Quell-Repositories: **nein**",
        "- Netzwerkzugriff: **nein**",
        "- Snapshot-Zeitpunkt(e): " + _times(items),
        f"- Geprüfte Repository References: **{len(items)}**",
        "- Authority: Git-Index und versionierte Reference-Bytes im Cabinet-Repository",
        "",
        "## Zusammenfassung",
        "",
        "| Kennzahl | Wert |",
        "|---|---:|",
        f"| `snapshot-identical` | {relationships['snapshot-identical']} |",
        f"| `snapshot-review-contained` | {relationships['snapshot-review-contained']} |",
        f"| `snapshot-divergence-claimed` | {relationships['snapshot-divergence-claimed']} |",
        f"| `snapshot-relationship-claimed` | {relationships['snapshot-relationship-claimed']} |",
        f"| `snapshot-clean-at-import` | {worktrees['snapshot-clean-at-import']} |",
        f"| `snapshot-dirty-at-import` | {worktrees['snapshot-dirty-at-import']} |",
        "",
        "## Repositorybewertungen",
        "",
        "| Repository | Commit-Klassifikation | Worktree-Klassifikation | Evidenzstatus | Review-HEAD | Import-HEAD | Beziehung beim Import | Import-Worktree | Erfasst | Quelle |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                (
                    _code(item.repository),
                    _code(item.relationship_class),
                    _code(item.worktree_class),
                    _escape_cell(_evidence_text(item)),
                    _code(item.review_head[:12]),
                    _code(item.import_head[:12]),
                    _escape_cell(item.relationship),
                    _code(item.import_worktree),
                    _code(item.imported_at),
                    _code(item.source_path),
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "## Prüfreihenfolge für einen späteren Live-Sammler",
            "",
            "| Rang | Repository | Begründung | Snapshotgrenze |",
            "|---:|---|---|---|",
        )
    )
    for item in priority_order(items):
        lines.append(
            f"| {item.priority} | {_code(item.repository)} | "
            f"{_escape_cell(_reason_text(item, True))} | "
            f"nur Snapshot {_code(item.imported_at)} |"
        )
    lines.extend(
        (
            "",
            "## Ableitungsregeln",
            "",
            "- `snapshot-identical` ist direkt aus identischen gespeicherten HEAD-Werten ableitbar.",
            "- Andere Commitbeziehungen bleiben Claims der jeweiligen Reference und werden nicht als Git-Historienbeweis umgedeutet.",
            "- `snapshot-clean-at-import` und `snapshot-dirty-at-import` beschreiben ausschließlich den gespeicherten Importzeitpunkt.",
            "- Die Prüfreihenfolge ist deterministisch: Divergenz-Claim vor Dirty-Import, danach andere nicht-identische Claims, zuletzt identische saubere Snapshots.",
            "",
            "## Epistemische Leerstellen",
            "",
            "- Aktuelle Branches, HEADs und Working Trees der Quell-Repositories sind unbekannt.",
            "- Aussagen wie `enthält`, `divergent`, `rewritten` oder `amended` wurden in diesem Lauf nicht gegen Git-Historien verifiziert.",
            "- CI-, Runtime- und Deploymentzustände der Quell-Repositories wurden nicht erhoben.",
            "- Eine spätere Aktualisierung benötigt einen neuen, datierten Sammlerlauf; alte Snapshots werden nicht still überschrieben.",
            "",
        )
    )
    return "\n".join(lines)


def render_lage(items: list[SnapshotAssessment]) -> str:
    relationships = Counter(item.relationship_class for item in items)
    worktrees = Counter(item.worktree_class for item in items)
    lines = [
        "# Repository-Snapshots v1",
        "",
        "<!-- GENERATED: scripts/build-repository-snapshot-review.py -->",
        "> **Generierte Lageansicht. Nicht manuell bearbeiten.**",
        "> Sie verdichtet datierte Cabinet-Snapshots und ist keine Live-Anzeige der Quell-Repositories.",
        "",
        "## Kurzlage",
        "",
        f"- Geprüfte Repository-Snapshots: **{len(items)}**",
        "- Snapshot-Zeitpunkt(e): " + _times(items),
        f"- Identische gespeicherte HEADs: **{relationships['snapshot-identical']}**",
        f"- Claim „Reviewstand enthalten“: **{relationships['snapshot-review-contained']}**",
        f"- Divergenz-/Rewrite-Claims: **{relationships['snapshot-divergence-claimed']}**",
        f"- Beim Import dirty: **{worktrees['snapshot-dirty-at-import']}**",
        "- Aktueller Zustand der Quell-Repositories: **unbekannt**",
        "",
        "## Reihenfolge späterer Live-Prüfungen",
        "",
        "| Rang | Repository | Historischer Anlass |",
        "|---:|---|---|",
    ]
    for item in priority_order(items):
        lines.append(
            f"| {item.priority} | {_code(item.repository)} | "
            f"{_escape_cell(_reason_text(item, False))} |"
        )
    lines.extend(
        (
            "",
            "## Grenze",
            "",
            "Diese Ansicht priorisiert nur spätere Prüfungen. Sie verändert keine Quell-Repositories und trifft keine Aussage über deren heutigen Zustand.",
            "",
            "Ausführlicher Prüflauf: [`repository-snapshot-review-v1.md`](../../pruefung/10%20Laeufe/repository-snapshot-review-v1.md)",
            "",
        )
    )
    return "\n".join(lines)


def _output(repo_root: Path, raw: str, label: str) -> Path:
    candidate = Path(raw)
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repo_root / candidate).resolve()
    )
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise InventoryError(f"{label} output path escapes repository: {resolved}") from exc
    return resolved


def _diff(current: str, expected: str, path: Path) -> str:
    lines = difflib.unified_diff(
        current.splitlines(),
        expected.splitlines(),
        fromfile=str(path),
        tofile=f"{path} (expected)",
        lineterm="",
    )
    return "\n".join(list(lines)[:160])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--review-output", default=str(DEFAULT_REVIEW_OUTPUT))
    parser.add_argument("--lage-output", default=str(DEFAULT_LAGE_OUTPUT))
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        review_output = _output(repo_root, args.review_output, "review")
        lage_output = _output(repo_root, args.lage_output, "Lage")
        records, warnings = inventory.load_records(
            repo_root, verify_index_match=args.check
        )
        items = build_assessments(records)
        expected = {
            review_output: render_review(items),
            lage_output: render_lage(items),
        }
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        if args.check:
            stale = False
            for path, content in expected.items():
                current = path.read_text(encoding="utf-8") if path.is_file() else ""
                if current != content:
                    stale = True
                    print(
                        "ERROR: repository snapshot review is stale: "
                        f"{path.relative_to(repo_root)}",
                        file=sys.stderr,
                    )
                    print(_diff(current, content, path), file=sys.stderr)
            if stale:
                return 1
            print(
                "Repository snapshot review: PASS "
                f"({len(items)} snapshots, {len(warnings)} warnings)"
            )
            return 0
        changed = 0
        for path, content in expected.items():
            current = path.read_text(encoding="utf-8") if path.is_file() else ""
            if current != content:
                inventory._atomic_write(path, content)
                changed += 1
        print(
            "Repository snapshot review written "
            f"({len(items)} snapshots, {changed} files changed, "
            f"{len(warnings)} warnings)"
        )
        return 0
    except (InventoryError, UnicodeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
