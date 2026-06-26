#!/usr/bin/env python3
"""Build a deterministic review and Lage view from repository import snapshots.

This generator evaluates only versioned ``Repository Reference.md`` evidence.
It does not access source repositories, networks, current branches, or current
working trees outside Cabinet.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

INVENTORY_MODULE_NAME = "scripts.repository_inventory"
INVENTORY_PATH = Path(__file__).resolve().with_name("repository_inventory.py")
DEFAULT_REVIEW_OUTPUT = Path(
    "pruefung/10 Laeufe/repository-snapshot-review-v1.md"
)
DEFAULT_LAGE_OUTPUT = Path("steuerung/10 Lage/repository-snapshots-v1.md")


@dataclass(frozen=True)
class SnapshotAssessment:
    repository: str
    relationship_class: str
    worktree_class: str
    evidence_status: str
    priority: int
    priority_reason: str
    review_head: str
    import_head: str
    relationship: str
    import_worktree: str
    imported_at: str
    source_path: str


def _load_inventory_module() -> ModuleType:
    existing = sys.modules.get(INVENTORY_MODULE_NAME)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(
        INVENTORY_MODULE_NAME, INVENTORY_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository inventory implementation")

    module = importlib.util.module_from_spec(spec)
    sys.modules[INVENTORY_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(INVENTORY_MODULE_NAME, None)
        raise
    return module


inventory = _load_inventory_module()
InventoryError = inventory.InventoryError
RepositoryRecord = inventory.RepositoryRecord


def _relationship_class(record: RepositoryRecord) -> tuple[str, str]:
    normalized = record.relationship.casefold()
    if record.review_head == record.import_head:
        return (
            "snapshot-identical",
            "direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch",
        )
    if any(token in normalized for token in ("divergent", "rewritten", "amended")):
        return (
            "snapshot-divergence-claimed",
            "reference-claim: Divergenz oder umgeschriebene Historie wurde behauptet",
        )
    if "enthält" in normalized or "contains" in normalized:
        return (
            "snapshot-review-contained",
            "reference-claim: der Importstand soll den Reviewstand enthalten",
        )
    return (
        "snapshot-relationship-claimed",
        "reference-claim: Beziehung wurde nicht durch Cabinet live verifiziert",
    )


def assess_record(record: RepositoryRecord) -> SnapshotAssessment:
    relationship_class, evidence_status = _relationship_class(record)
    worktree_state, raw_count = record.import_worktree.split(":", 1)
    worktree_class = f"snapshot-{worktree_state}-at-import"
    change_count = int(raw_count)

    if relationship_class == "snapshot-divergence-claimed":
        priority = 1
        priority_reason = "Divergenz- oder Rewrite-Claim später in Git verifizieren"
    elif worktree_state == "dirty":
        priority = 2
        priority_reason = (
            f"damals {change_count} Working-Tree-Änderungen; später neu erheben"
        )
    elif relationship_class in {
        "snapshot-review-contained",
        "snapshot-relationship-claimed",
    }:
        priority = 3
        priority_reason = "nicht-identische Commitbeziehung später live prüfen"
    else:
        priority = 4
        priority_reason = "keine besondere Priorität aus dem Snapshot ableitbar"

    return SnapshotAssessment(
        repository=record.repository,
        relationship_class=relationship_class,
        worktree_class=worktree_class,
        evidence_status=evidence_status,
        priority=priority,
        priority_reason=priority_reason,
        review_head=record.review_head,
        import_head=record.import_head,
        relationship=record.relationship,
        import_worktree=record.import_worktree,
        imported_at=record.imported_at,
        source_path=record.source_path,
    )


def build_assessments(records: list[RepositoryRecord]) -> list[SnapshotAssessment]:
    return [assess_record(record) for record in records]


def _escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _code(value: str) -> str:
    return f"`{_escape_cell(value)}`"


def _short_head(value: str) -> str:
    return value[:12]


def _snapshot_times(assessments: list[SnapshotAssessment]) -> str:
    values = sorted({assessment.imported_at for assessment in assessments})
    return ", ".join(_code(value) for value in values)


def _priority_order(
    assessments: list[SnapshotAssessment],
) -> list[SnapshotAssessment]:
    return sorted(
        assessments,
        key=lambda item: (item.priority, item.repository.casefold(), item.repository),
    )


def render_review(assessments: list[SnapshotAssessment]) -> str:
    relationship_counts = Counter(
        assessment.relationship_class for assessment in assessments
    )
    worktree_counts = Counter(assessment.worktree_class for assessment in assessments)

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
        "- Snapshot-Zeitpunkt(e): " + _snapshot_times(assessments),
        f"- Geprüfte Repository References: **{len(assessments)}**",
        "- Authority: Git-Index und versionierte Reference-Bytes im Cabinet-Repository",
        "",
        "## Zusammenfassung",
        "",
        "| Kennzahl | Wert |",
        "|---|---:|",
        f"| `snapshot-identical` | {relationship_counts['snapshot-identical']} |",
        f"| `snapshot-review-contained` | {relationship_counts['snapshot-review-contained']} |",
        f"| `snapshot-divergence-claimed` | {relationship_counts['snapshot-divergence-claimed']} |",
        f"| `snapshot-relationship-claimed` | {relationship_counts['snapshot-relationship-claimed']} |",
        f"| `snapshot-clean-at-import` | {worktree_counts['snapshot-clean-at-import']} |",
        f"| `snapshot-dirty-at-import` | {worktree_counts['snapshot-dirty-at-import']} |",
        "",
        "## Repositorybewertungen",
        "",
        "| Repository | Commit-Klassifikation | Worktree-Klassifikation | Evidenzstatus | Review-HEAD | Import-HEAD | Beziehung beim Import | Import-Worktree | Erfasst | Quelle |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in assessments:
        lines.append(
            "| "
            + " | ".join(
                (
                    _code(item.repository),
                    _code(item.relationship_class),
                    _code(item.worktree_class),
                    _escape_cell(item.evidence_status),
                    _code(_short_head(item.review_head)),
                    _code(_short_head(item.import_head)),
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
    for item in _priority_order(assessments):
        lines.append(
            f"| {item.priority} | {_code(item.repository)} | "
            f"{_escape_cell(item.priority_reason)} | "
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


def render_lage(assessments: list[SnapshotAssessment]) -> str:
    relationship_counts = Counter(
        assessment.relationship_class for assessment in assessments
    )
    worktree_counts = Counter(assessment.worktree_class for assessment in assessments)

    lines = [
        "# Repository-Snapshots v1",
        "",
        "<!-- GENERATED: scripts/build-repository-snapshot-review.py -->",
        "> **Generierte Lageansicht. Nicht manuell bearbeiten.**",
        "> Sie verdichtet datierte Cabinet-Snapshots und ist keine Live-Anzeige der Quell-Repositories.",
        "",
        "## Kurzlage",
        "",
        f"- Geprüfte Repository-Snapshots: **{len(assessments)}**",
        "- Snapshot-Zeitpunkt(e): " + _snapshot_times(assessments),
        f"- Identische gespeicherte HEADs: **{relationship_counts['snapshot-identical']}**",
        f"- Claim „Reviewstand enthalten“: **{relationship_counts['snapshot-review-contained']}**",
        f"- Divergenz-/Rewrite-Claims: **{relationship_counts['snapshot-divergence-claimed']}**",
        f"- Beim Import dirty: **{worktree_counts['snapshot-dirty-at-import']}**",
        "- Aktueller Zustand der Quell-Repositories: **unbekannt**",
        "",
        "## Nächste spätere Live-Prüfungen",
        "",
        "| Rang | Repository | Historischer Anlass | Nicht behauptet |",
        "|---:|---|---|---|",
    ]
    for item in _priority_order(assessments):
        lines.append(
            f"| {item.priority} | {_code(item.repository)} | "
            f"{_escape_cell(item.priority_reason)} | aktueller Zustand |"
        )

    lines.extend(
        (
            "",
            "## Steuerungsgrenze",
            "",
            "Diese Lageansicht priorisiert nur spätere Prüfungen. Sie erteilt keinen Coding-Auftrag, keine Mergefreigabe und keine Runtimefreigabe.",
            "",
            "Ausführlicher Prüflauf: [`repository-snapshot-review-v1.md`](../../pruefung/10%20Laeufe/repository-snapshot-review-v1.md)",
            "",
        )
    )
    return "\n".join(lines)


def _resolve_output(repo_root: Path, raw_path: str, label: str) -> Path:
    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise InventoryError(f"{label} output path escapes repository: {resolved}") from exc
    return resolved


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--review-output", default=str(DEFAULT_REVIEW_OUTPUT))
    parser.add_argument("--lage-output", default=str(DEFAULT_LAGE_OUTPUT))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        review_output = _resolve_output(
            repo_root, args.review_output, "review"
        )
        lage_output = _resolve_output(repo_root, args.lage_output, "Lage")
        records, warnings = inventory.load_records(
            repo_root, verify_index_match=args.check
        )
        assessments = build_assessments(records)
        expected = {
            review_output: render_review(assessments),
            lage_output: render_lage(assessments),
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
                        f"ERROR: repository snapshot review is stale: {path.relative_to(repo_root)}",
                        file=sys.stderr,
                    )
                    print(_limited_diff(current, content, path), file=sys.stderr)
            if stale:
                return 1
            print(
                "Repository snapshot review: PASS "
                f"({len(assessments)} snapshots, {len(warnings)} warnings)"
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
            f"({len(assessments)} snapshots, {changed} files changed, "
            f"{len(warnings)} warnings)"
        )
        return 0
    except (InventoryError, UnicodeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
