# Repository Observation Candidates v1

<!-- GENERATED: scripts/build-repository-observation-candidates.py -->
> **Generierte Datei. Nicht manuell bearbeiten.**
> Quelle: versionierte `Repository Reference.md`-Dateien und deterministische Snapshot-Bewertungen.
> **Grenze:** Diese Datei erzeugt Kandidaten, keine Bureau-Tasks, keine Claims, keine Dispatches und keine Merge-Rechte.

## Kurzlage

- Geprüfte Repository-Snapshots: **8**
- Kandidaten: **1**
- Routine-/Nicht-Kandidaten: **7**
- Snapshot-Zeitpunkt(e): `2026-06-23T18:38:45.731368+00:00`, `2026-07-02T12:54:24Z`, `2026-07-03T12:54:24Z`, `2026-07-03T20:24:19Z`
- Aktueller Zustand der Quell-Repositories: **unbekannt**

## Kandidaten

| Rang | Repository | Kandidatentyp | Vorgeschlagene nächste Prüfung | Snapshotgrenze | Quelle |
|---:|---|---|---|---|---|
| 2 | `lenskit` | `live-snapshot-refresh` | Repository-Beobachtung aktualisieren, nachdem geprüft wurde, ob der Dirty-Import noch relevant ist. | Nur historischer Dirty-Import; heutiger Worktree unbekannt. | `werkstatt/20 Werkzeuge/Lenskit/Repository Reference.md` |

## Routine- oder Nicht-Kandidaten

| Repository | Grund | Quelle |
|---|---|---|
| `bureau` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `steuerung/40 Organe/Bureau/Repository Reference.md` |
| `grabowski` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `steuerung/40 Organe/grabowski/Repository Reference.md` |
| `heimgewebe-katalog` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `steuerung/40 Organe/Heimgewebe-Systemkatalog/Repository Reference.md` |
| `infra` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `werkstatt/20 Werkzeuge/Infra/Repository Reference.md` |
| `steuerboard` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `werkstatt/20 Werkzeuge/Steuerboard/Repository Reference.md` |
| `vibe-lab` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `labor/30 Versuchsstände/Vibe-Lab/Repository Reference.md` |
| `weltgewebe` | Keine besondere Priorität aus dem gespeicherten Snapshot ableitbar. | `weltgewebe/Repository Reference.md` |

## Promotionsregeln

- Ein Kandidat ist nur ein Hinweis auf eine spätere Prüfung.
- Promotion zu Bureau benötigt eine separate menschliche Entscheidung und ein eigenes, versioniertes Task-Artefakt.
- Dieser Report liest keine heutigen Quell-Repositories und darf deshalb keine aktuelle Readiness behaupten.
- Dirty-, Divergenz- und nicht-identische Commit-Befunde müssen vor jeder Umsetzung live geprüft werden.

## Epistemische Leerstellen

- Aktuelle Branches, HEADs, Worktrees, CI und Runtime-Zustände der Quell-Repositories fehlen.
- Ob ein Kandidat fachlich wichtig ist, kann aus Snapshotdaten allein nicht entschieden werden.
- Ob Bureau, Grabowski, Steuerboard oder ein Mensch zuständig ist, bleibt pro Kandidat separat zu klären.
