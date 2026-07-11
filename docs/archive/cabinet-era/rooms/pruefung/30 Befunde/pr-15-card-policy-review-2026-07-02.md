# PR 15 Card Policy Review 2026-07-02

## Ergebnis

Empfehlung: revise/rebase. Nicht mergen. Nicht schließen.

## Belegt

- PR 15 ist offen und Draft.
- Head: project-card-hardening. Base: main.
- Geänderte Flächen: Project-Cards-Workflow, Policy-Blueprint, neues Python-Prüfskript, zwei Tests.
- Bekannte Branch-CI vom 2026-06-28 war grün: Validate, Project Cards, Repository Snapshot Review.
- GitHub meldete mergeStateStatus UNKNOWN und leere reviewDecision.

## Prüfung

These: Die neue Regelrichtung ist sinnvoll: Projektkarten sollen keine Eigenbelege sein, und reviewed_at darf nicht in der Zukunft liegen.

Antithese: Draft-Status, alter CI-Stand und UNKNOWN-Merge-State verhindern eine saubere Merge-Empfehlung.

Synthese: Der PR soll aktualisiert und erneut geprüft werden.

## Findings

- R15-01 P1: Draft-Status blockiert Merge.
- R15-02 P1: Bekannte Checks sind alt und müssen nach Rebase gegen aktuellen main neu laufen.
- R15-03 P2: Tests decken den Kern ab, aber nur minimal.

## Entscheidung

revise/rebase

## Nächste Aktion

Branch auf aktuellen main bringen, CI neu laufen lassen, Draft entfernen, dann erneut prüfen.
