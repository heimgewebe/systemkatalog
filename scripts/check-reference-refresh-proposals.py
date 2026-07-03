#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


PROPOSAL_GLOB = "*reference-refresh-proposal*.md"
PROPOSAL_ROOT = Path("steuerung/20 Aufgaben")
REQUIRED_SECTIONS = (
    "## Status",
    "## Eingaben",
    "## Vorher",
    "## Nachher-Entwurf",
    "## Nicht anwenden",
    "## Review-Kriterien",
    "## Stop-Kriterium",
    "## Target-Proof",
)
REQUIRED_TEXT = (
    "Vorschlag, nicht angewendet.",
    "Dieser Vorschlag ändert keine Repository Reference.",
    "Betroffene Reference:",
    "pruefung/30 Befunde/",
    "steuerung/20 Aufgaben/",
    "Repository Reference.md",
    "Quelle ist genannt.",
    "Live-Hinweis ist genannt.",
    "Vorher und Nachher bleiben getrennt.",
)
FORBIDDEN_TEXT = (
    "## Angewendet",
    "Reference wurde aktualisiert",
    "Bureau-Task erzeugt",
    "Dispatch erzeugt",
)


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str


def proposal_paths(repo_root: Path) -> list[Path]:
    root = repo_root / PROPOSAL_ROOT
    if not root.exists():
        return []
    return sorted(path for path in root.glob(PROPOSAL_GLOB) if path.is_file())


def check_proposal(path: Path, repo_root: Path) -> list[Finding]:
    rel = path.relative_to(repo_root)
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            findings.append(Finding(rel, f"missing section: {section}"))

    for required in REQUIRED_TEXT:
        if required not in text:
            findings.append(Finding(rel, f"missing required text: {required}"))

    for forbidden in FORBIDDEN_TEXT:
        if forbidden in text:
            findings.append(Finding(rel, f"forbidden applied-state text: {forbidden}"))

    if "## Vorher" in text and "## Nachher-Entwurf" in text:
        if text.index("## Nachher-Entwurf") < text.index("## Vorher"):
            findings.append(Finding(rel, "Nachher-Entwurf appears before Vorher"))

    return findings


def run(repo_root: Path) -> list[Finding]:
    root = repo_root.resolve()
    findings: list[Finding] = []
    for path in proposal_paths(root):
        findings.extend(check_proposal(path, root))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    findings = run(args.repo_root)
    if findings:
        for finding in findings:
            print(f"{finding.path}: {finding.message}", file=sys.stderr)
        return 2

    count = len(proposal_paths(args.repo_root.resolve()))
    print(f"Reference refresh proposal guard: PASS ({count} proposals)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
