# Checkout-Lifecycle-Map v0

Status: draft
Datum: 2026-07-03
Scope: erste lokale Worktree-Klassifikation auf heim-pc

## Zweck

Diese Map ist ein Befund- und Planartefakt. Sie entfernt, archiviert und bereinigt nichts. Sie ordnet lokale Git-Worktrees in grobe Lifecycle-Klassen ein, damit spätere Schritte nicht blind in parallele Arbeit eingreifen.

## Regel

Erst klassifizieren, dann handeln.

- Dirty Worktrees bleiben aktiv, bis ihr Inhalt geprüft wurde.
- Clean Worktrees ohne Zweck sind unklar, nicht automatisch entbehrlich.
- Technisch verwaiste Worktree-Einträge sind nur Prüfpunkt für einen späteren Dry-Run.
- Bereits archivierte und saubere Kandidaten sind die einzigen sinnvollen frühen Kandidaten für eine spätere Einzelprüfung.

## Gelesene lokale Inventare

Erfolgreich gelesen:

- Cabinet: 3 Worktrees
- Grabowski: 14 Worktrees
- Infra: 22 Worktrees
- Weltgewebe: 42 Worktrees

Nicht vollständig gelesen:

- Bureau
- Lenskit
- Steuerboard
- weitere Repositories

Diese Karte ist daher OP-001A, nicht der vollständige heim-pc-Endzustand.

## Klassifikationsschema

| Klasse | Bedeutung | Nächste Aktion |
|---|---|---|
| active | laufende Arbeit, dirty Checkout, Primärcheckout auf Feature-Branch oder aktueller Arbeits-Worktree | nicht anfassen |
| preserve | sauberer Checkout mit erkennbarem Zweck oder Retention | behalten bis Review oder Frist |
| unknown | sauber, aber Zweck oder Owner unklar | Zweck klären |
| cleanup-candidate | sauber und archiviert oder technisch verwaist | nur Dry-Run, dann explizite Bestätigung |

## Befundübersicht

| Bereich | Worktrees | Hauptbefund | Bewertung |
|---|---:|---|---|
| Cabinet | 3 | separater OP-001-Worktree vorhanden; Primärcheckout auf parallelem Branch | kontrolliert |
| Grabowski | 14 | mehrere Retentions; ein archivierter sauberer Kandidat; mehrere aktive Arbeitsstände | sensibel |
| Infra | 22 | mehrere aktive Arbeitsstände und mehrere technisch verwaiste temporäre Einträge | riskant |
| Weltgewebe | 42 | viele historische oder thematische Arbeitsstände; wenige technisch verwaiste Einträge | mengenbedingt riskant |

## Top-Risiken

1. Dirty Primärcheckouts in operativen Repos dürfen nicht durch Pull, Switch oder Reset überschrieben werden.
2. Grabowski hat einen Runtime-/Checkout-Split: runtime-matching Worktree und kanonischer Checkout sind nicht dieselbe Lage.
3. Technisch verwaiste Worktree-Einträge sind wahrscheinlich Hygiene-Thema, aber keine inhaltliche Löschfreigabe.
4. Viele clean Worktrees ohne sichtbare Retention erzeugen kognitive Last, sind aber keine automatischen Löschkandidaten.
5. Cabinet-Arbeit sollte weiter in separaten Worktrees laufen, solange der Primärcheckout auf paralleler Arbeit steht.

## Erste Kandidatenklassen

### Nicht anfassen

- alle dirty Worktrees
- runtime-matching Grabowski-Worktree
- aktuelle Cabinet-Arbeitsworktrees
- Primärcheckouts auf aktiven Feature-Branches

### Späterer Dry-Run möglich

- bereits archivierter sauberer Grabowski-Checkout aus der Steuerboard-Context-Arbeit
- technisch verwaiste temporäre Infra-Worktree-Einträge
- technisch verwaiste temporäre Weltgewebe-Worktree-Einträge

### Zu klären

- clean Worktrees ohne Retention
- alte Repair-, Review- und Lifecycle-Branches ohne sichtbare PR- oder Task-Beziehung
- Cabinet-Altworktree zur Repository-Oversight-Blueprint-Arbeit

## Entscheidung

OP-001 bestätigt: Der nächste operative Schritt ist ein Lifecycle-Gate, kein Cleanup-Lauf.

1. Unknown clean Worktrees bekommen Owner und Purpose oder werden als archive-candidate markiert.
2. Bereits archivierte Kandidaten dürfen einzeln per Dry-Run geprüft werden.
3. Dirty Worktrees bleiben aktiv, bis ihr Inhalt bewertet wurde.

## Nächste Aktion

OP-001B soll einen maschinenlesbaren Sidecar `checkout-lifecycle-candidates.json` erstellen. Bis dahin keine Änderung an fremden Worktrees.
