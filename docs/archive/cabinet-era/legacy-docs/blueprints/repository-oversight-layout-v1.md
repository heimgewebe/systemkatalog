# Repository-Oversight-Layout v1

## Ziel

Cabinet wird zur lokalen, repoübergreifenden Arbeits- und Entscheidungsfläche. Git, Contracts, CI und überprüfbare Runtime-Ausgaben bleiben die fachlichen Sources of Truth. Cabinet hält datierte Karten, Befunde, Entscheidungen und Übergaben zusammen.

## Zielräume

### Bestand

Beantwortet: **Was existiert, wie hängt es zusammen und auf welchem belegten Stand?**

Enthält Repositorykarten, Projektkarten, Quellen, Beziehungen sowie Frische- und Provenienzangaben.

### Prüfung

Beantwortet: **Was ist belegt, widersprüchlich, veraltet oder fehlerhaft?**

Enthält Prüfläufe, Evidence Packs, Befunde, Widersprüche, Risiken und epistemische Leerstellen.

### Steuerung

Beantwortet: **Was wird entschieden und was geschieht als Nächstes?**

Enthält Lageübersicht, Entscheidungen, priorisierte Aufgaben, Blocker und Übergaben.

`steuerung` ist der versionierte und lokale Ziel-Default. Die bisherigen sechs Pfade bleiben als lesbare Legacy-Sammlungen erhalten, besitzen aber keine aktive Top-Level-Raumrolle mehr.

## Workspace-Cutover-Vertrag

- `.home/home.json` und `policy/cabinet-layout.json` erklären `steuerung` zum verbindlichen versionierten Default.
- Die lokale `.agents/.config/workspace.json` bleibt unversioniert und darf nicht durch CI oder einen Repository-Checkout überschrieben werden.
- Der ausführbare Vertrag liegt in `scripts/workspace_default_cutover.py`; `cabinetctl workspace-check`, `cabinetctl workspace-apply` und `cabinetctl workspace-rollback BACKUP-ID` sind die Bedienoberfläche.
- Backups liegen außerhalb des Repositories unter `~/.local/state/cabinet/workspace-cutovers/<BACKUP-ID>/` und enthalten die Originalbytes sowie ein Manifest mit Dateimodus, SHA-256, Quell- und Zielraum.
- Beim Abgleich wird inhaltlich ausschließlich `room.slug` auf `steuerung` gesetzt; unbekannte JSON-Felder bleiben erhalten. Die JSON-Formatierung darf dabei normalisiert werden.
- Das Schreiben erfolgt atomar. Danach muss `python3 scripts/check-cabinet-layout.py --mode local .` erfolgreich sein.
- Scheitert die Prüfung, stellt das Werkzeug die gesicherten Originalbytes und den ursprünglichen Dateimodus wieder her.
- Manipulierte Backups, Symlinks, unsichere Backup-IDs, ungültiges JSON und ein Backup-Pfad innerhalb des Repositories werden fail-closed abgewiesen.
- Der Host-Cutover wird auf dem PR-Branch vor dem Merge ausgeführt und geprüft. Erst nach erfolgreichem Target-Proof darf der Default-PR gemergt werden.
- Nach dem Merge wird `main` aktualisiert und `workspace-check` erneut ausgeführt. Ein expliziter Rollback kann absichtlich Drift zum versionierten Default erzeugen und muss deshalb sichtbar dokumentiert werden.

## Grenzen

- Maschinen dürfen Bestand und Prüfung vorbereiten.
- Befunde ohne Evidence bleiben Hinweise.
- Nur der Mensch bestätigt Entscheidungen und Aufträge.
- Cabinet-Agenten verändern keine Quell-Repositories automatisch.
- Externe Modelle erhalten nur freigegebene, redigierte Inputs.
- Private Repositoryinhalte bleiben lokal, solange keine ausdrückliche Freigabe vorliegt.

## Minimale Artefakte

1. **Repositorykarte** – Identität, Rolle, Quellen, Beziehungen, Commit und Frische.
2. **Projektkarte** – Ziel, Repositories, Stand, Blocker und nächste Aktion.
3. **Befund** – Beobachtung, Erwartung, Evidence, Schweregrad, Vertrauen und Status.
4. **Laufprotokoll** – Quellen, Commits, Modellprofil, tatsächliches Modell, Zeitpunkt und Ergebnis.
5. **Entscheidung oder Auftrag** – zunächst strukturiertes Markdown.

## Authority-Grenze des Repositorybestands

- `Repository Reference.md` ist die versionierte Detail- und Evidenzquelle.
- `bestand/10 Repositories/index.md` ist ein deterministisch erzeugter Repository-Snapshotkatalog.
- Pfadermittlung und Zulässigkeit der References kommen aus dem Git-Index: akzeptiert werden nur reguläre Blobs im Modus `100644` auf Stage `0`.
- Der lokale Schreibmodus liest aktuelle reguläre Working-Tree-Dateien, damit Reference-Änderung und erzeugter Index anschließend gemeinsam gestaged werden können.
- Working-Tree-References werden vom geöffneten Repositoryroot komponentenweise und ohne Symlink-Following geöffnet; kein Bestandteil eines Reference-Pfades darf ein Symlink sein.
- Der Checkmodus verarbeitet keinen stillen Drift zwischen Working Tree und Index-Blob; abweichende, fehlende oder unsicher aufgelöste Working-Tree-References scheitern fail-closed.
- Der verbindliche Zweispalten- und Pipe-Escape-Contract ist in [`repository-inventory-table-contract.md`](repository-inventory-table-contract.md) festgelegt.
- CI validiert auf sauberem Checkout; dort bilden Git-Index, Working Tree und Commit-Snapshot dieselben Reference-Bytes ab.
- Der Index darf explizite Werte zusammenfassen, sortieren und verlinken.
- Import-HEAD, Import-Worktree und Commitbeziehung werden ausdrücklich als zeitgebundene Importwerte samt Erfassungszeitpunkt dargestellt; sie behaupten keinen aktuellen Zustand des Quellrepositories.
- Direkt aus einer Reference beweisbare Widersprüche werden fail-closed abgewiesen: insbesondere `identisch` bei verschiedenen HEADs sowie widersprüchliche `clean`-/`dirty`-Zähler.
- Andere Commitbeziehungen werden als Claims der Reference übernommen, nicht durch den Indexgenerator gegen das Quellrepository verifiziert.
- Der Index darf keine Rollen, Zustände oder Commitbeziehungen ergänzen oder umdeuten.
- Drift zwischen Referenzen und Index ist ein CI-Fehler; CI regeneriert oder committet nicht automatisch.
- Ein maschinenlesbarer Sidecar entsteht erst bei einem belegten Consumer.

## Arbeitsfluss

```text
Quellen sammeln
→ Bestand aktualisieren
→ deterministisch prüfen
→ semantisch anreichern
→ Befunde deduplizieren
→ Mensch entscheidet
→ Auftrag mit Target-Proof übergeben
→ Ergebnis verifizieren
```

## Modellprofile

- `free-default`: Extraktion, Klassifikation, Zusammenfassung und begrenzter Claim-Code-Vergleich.
- `manual-deep-review`: nur nach menschlicher Freigabe.
- Keine automatische kostenpflichtige Eskalation.
- Jeder Lauf protokolliert Profil, Modell, Provider, Fallback, Quellen und Zeitpunkte.

## Legacy-Räume

| Bisher | Primärer Nachfolger |
|---|---|
| Vorzimmer | Steuerung |
| Heimgewebe | Bestand |
| Weltgewebe | Bestand |
| Werkstatt | Steuerung |
| Labor | Prüfung |
| Betrieb | Prüfung |

Bestehende Inhalte werden einzeln als `keep`, `move`, `split`, `archive` oder `delete` klassifiziert. Es gibt keine automatische Massenverschiebung.

## Phasen

1. Drei Zielräume als einzige aktive Räume führen; alte Pfade bleiben als Legacy-Sammlungen lesbar.
2. Repository-Snapshotkatalog aus versionierten Repository References deterministisch erzeugen und in CI prüfen.
3. Datierte Snapshots lokal prüfen und eine erste Lageansicht ableiten, ohne Aktualität zu unterstellen.
4. Versionierten Default auf `steuerung` umstellen; lokale Workspace-Konfigurationen hostbezogen sichern, auf dem PR-Branch abgleichen und vor sowie nach dem Merge prüfen.
5. Projektkarten aus bestätigten Repositorybeziehungen und Vorhaben aufbauen.
6. Deterministischen Sammler für freigegebene Repositories bauen; erst dieser erzeugt neu erhobene Zustandsdaten.
7. Evidence-Pflicht, stabile Fingerprints und Hinweis/Bestätigt-Trennung einführen.
8. Lage und Aufträge aus validierten Artefakten erzeugen.
9. Alte aktive Raumrollen stilllegen; Fachinhalte bis zur dateiweisen Klassifikation in lesbaren Legacy-Sammlungen erhalten.
10. Automatisierung erst nach wiederholbaren manuellen Läufen aktivieren.

## Neubewertung

Die Dreiraumstruktur wird neu bewertet, wenn getrennte Benutzer, Vertraulichkeitsstufen, technisch erzwungene Agenten-Sandboxes oder stark abweichende Providerregeln entstehen.
