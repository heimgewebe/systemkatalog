# Repository Snapshot Review v1

<!-- GENERATED: scripts/build-repository-snapshot-review.py -->
> **Generierte Datei. Nicht manuell bearbeiten.**
> Quelle: versionierte `Repository Reference.md`-Dateien in Cabinet.
> **Zeitgrenze:** Diese Prüfung bewertet ausschließlich gespeicherte Import-Snapshots. Sie prüft keine heutigen Repositoryzustände.

## Laufvertrag

- Live-Zugriff auf Quell-Repositories: **nein**
- Netzwerkzugriff: **nein**
- Snapshot-Zeitpunkt(e): `2026-06-23T18:38:45.731368+00:00`, `2026-07-02T12:54:24Z`, `2026-07-03T12:54:24Z`
- Geprüfte Repository References: **8**
- Authority: Git-Index und versionierte, indexidentische Reference-Bytes im Cabinet-Repository

## Zusammenfassung

| Kennzahl | Wert |
|---|---:|
| `snapshot-identical` | 6 |
| `snapshot-review-contained` | 1 |
| `snapshot-divergence-claimed` | 1 |
| `snapshot-relationship-claimed` | 0 |
| `snapshot-clean-at-import` | 7 |
| `snapshot-dirty-at-import` | 1 |

## Repositorybewertungen

| Repository | Commit-Klassifikation | Worktree-Klassifikation | Evidenzstatus | Review-HEAD | Import-HEAD | Beziehung beim Import | Import-Worktree | Erfasst | Quelle |
|---|---|---|---|---|---|---|---|---|---|
| `bureau` | `snapshot-identical` | `snapshot-clean-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `cf0fef56e194dcbe0c5e9c9674a814beed157a7a` | `cf0fef56e194dcbe0c5e9c9674a814beed157a7a` | identisch | `clean:0` | `2026-07-03T12:54:24Z` | `steuerung/40 Organe/Bureau/Repository Reference.md` |
| `cabinet` | `snapshot-identical` | `snapshot-clean-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `3ce791b34b1c095afd3ea1c76f7c1461759e26b0` | `3ce791b34b1c095afd3ea1c76f7c1461759e26b0` | identisch | `clean:0` | `2026-07-02T12:54:24Z` | `steuerung/40 Organe/Cabinet/Repository Reference.md` |
| `grabowski` | `snapshot-identical` | `snapshot-clean-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `abc3ad470615ffb5fd6c18ae27d0e992be6ac73e` | `abc3ad470615ffb5fd6c18ae27d0e992be6ac73e` | identisch | `clean:0` | `2026-07-02T12:54:24Z` | `steuerung/40 Organe/grabowski/Repository Reference.md` |
| `infra` | `snapshot-review-contained` | `snapshot-clean-at-import` | reference-claim: der Importstand soll den Reviewstand enthalten | `5d9b7f840fcd59742b75ce19ba2f90fa396ddee8` | `30ab479a3ce79aa5907ab0a21e919dd07c2a5443` | Live-Stand enthält Review-Stand | `clean:0` | `2026-06-23T18:38:45.731368+00:00` | `werkstatt/20 Werkzeuge/Infra/Repository Reference.md` |
| `lenskit` | `snapshot-identical` | `snapshot-dirty-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `c692cfc7c51cdb898e95e7df9ebc762190c0767e` | `c692cfc7c51cdb898e95e7df9ebc762190c0767e` | identisch | `dirty:6` | `2026-06-23T18:38:45.731368+00:00` | `werkstatt/20 Werkzeuge/Lenskit/Repository Reference.md` |
| `steuerboard` | `snapshot-divergence-claimed` | `snapshot-clean-at-import` | reference-claim: Divergenz oder umgeschriebene Historie wurde behauptet | `62669eb95800d71aeb0d5d1f488e21524321659d` | `5a2a9a4e8a333162196d5cf16cce7d0440de34f7` | divergent oder rewritten/amended | `clean:0` | `2026-06-23T18:38:45.731368+00:00` | `werkstatt/20 Werkzeuge/Steuerboard/Repository Reference.md` |
| `vibe-lab` | `snapshot-identical` | `snapshot-clean-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `869abfb05b466e3be6529250a34a1fea257d1455` | `869abfb05b466e3be6529250a34a1fea257d1455` | identisch | `clean:0` | `2026-06-23T18:38:45.731368+00:00` | `labor/30 Versuchsstände/Vibe-Lab/Repository Reference.md` |
| `weltgewebe` | `snapshot-identical` | `snapshot-clean-at-import` | direkt-belegt: gespeicherte Review- und Import-HEADs sind identisch | `bac3c4f7879f9e86b098b081b72bf6c133b44462` | `bac3c4f7879f9e86b098b081b72bf6c133b44462` | identisch | `clean:0` | `2026-06-23T18:38:45.731368+00:00` | `weltgewebe/Repository Reference.md` |

## Prüfreihenfolge für einen späteren Live-Sammler

| Rang | Repository | Begründung | Snapshotgrenze |
|---:|---|---|---|
| 1 | `steuerboard` | Divergenz- oder Rewrite-Claim später in Git verifizieren | nur Snapshot `2026-06-23T18:38:45.731368+00:00` |
| 2 | `lenskit` | damals 6 Working-Tree-Änderungen; später neu erheben | nur Snapshot `2026-06-23T18:38:45.731368+00:00` |
| 3 | `infra` | nicht-identische Commitbeziehung später live prüfen | nur Snapshot `2026-06-23T18:38:45.731368+00:00` |
| 4 | `bureau` | keine besondere Priorität aus dem Snapshot ableitbar | nur Snapshot `2026-07-03T12:54:24Z` |
| 4 | `cabinet` | keine besondere Priorität aus dem Snapshot ableitbar | nur Snapshot `2026-07-02T12:54:24Z` |
| 4 | `grabowski` | keine besondere Priorität aus dem Snapshot ableitbar | nur Snapshot `2026-07-02T12:54:24Z` |
| 4 | `vibe-lab` | keine besondere Priorität aus dem Snapshot ableitbar | nur Snapshot `2026-06-23T18:38:45.731368+00:00` |
| 4 | `weltgewebe` | keine besondere Priorität aus dem Snapshot ableitbar | nur Snapshot `2026-06-23T18:38:45.731368+00:00` |

## Ableitungsregeln

- `snapshot-identical` ist direkt aus identischen gespeicherten HEAD-Werten ableitbar.
- Andere Commitbeziehungen bleiben Claims der jeweiligen Reference und werden nicht als Git-Historienbeweis umgedeutet.
- `snapshot-clean-at-import` und `snapshot-dirty-at-import` beschreiben ausschließlich den gespeicherten Importzeitpunkt.
- Die Prüfreihenfolge ist deterministisch: Divergenz-Claim vor Dirty-Import, danach andere nicht-identische Claims, zuletzt identische saubere Snapshots.

## Epistemische Leerstellen

- Aktuelle Branches, HEADs und Working Trees der Quell-Repositories sind unbekannt.
- Aussagen wie `enthält`, `divergent`, `rewritten` oder `amended` wurden in diesem Lauf nicht gegen Git-Historien verifiziert.
- CI-, Runtime- und Deploymentzustände der Quell-Repositories wurden nicht erhoben.
- Eine spätere Aktualisierung benötigt einen neuen, datierten Sammlerlauf; alte Snapshots werden nicht still überschrieben.
