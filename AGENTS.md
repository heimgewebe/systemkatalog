# Systemkatalog – Agenteneinstieg

## Lesereihenfolge

1. [README.md](README.md)
2. [policy/system-catalog.v1.json](policy/system-catalog.v1.json)
3. [rendered/system-catalog.md](rendered/system-catalog.md)
4. [registry/ecosystem/authority-matrix.v1.json](registry/ecosystem/authority-matrix.v1.json)
5. [registry/ecosystem/nodes.json](registry/ecosystem/nodes.json)
6. [registry/ecosystem/edges.json](registry/ecosystem/edges.json)
7. [docs/architecture/systemkatalog.md](docs/architecture/systemkatalog.md)

## Rolle

Der Systemkatalog pflegt nur stabile Ökosystem-Semantik:

- Systeme und Zwecke;
- ausdrückliche Grenzen;
- Wahrheitszuständigkeiten;
- stabile Beziehungen;
- Einstiegspunkte.

Er pflegt keine Aufgabenpriorität, keinen Taskstatus, keine Runtime-Gesundheit, keine Merge-Reife, keine Agentendisposition und keinen Schedulerzustand.

## Wahrheitsordnung

- Bureau: Aufgaben, Queue, Claims, Handoffs und Receipts.
- Grabowski: freigegebene lokale und repositorybezogene Ausführung.
- GitHub: Repositories, Branches, Pull Requests, Issues und Reviews.
- CI und Review-Gates: technische Prüfsignale.
- Runtime, systemd, Logs und Healthchecks: laufende Dienste.
- RepoBrief / Lenskit: zitierfähiger Repositorykontext.
- Leitstand: allgemeine Live-Anzeige.
- Systemkatalog: stabile Ökosystem-Semantik und Zuordnung der Wahrheitsdomänen.

## Arbeitsregeln

1. Aktuelle Zustände immer an ihrer Primärquelle prüfen.
2. Katalogdaten dürfen keine wechselnden Betriebszustände kopieren.
3. Mermaidkarten und Markdownansichten sind Projektionen, keine eigene Wahrheit.
4. `docs/archive/cabinet-era/` ist historisch und nicht aktiv zu pflegen.
5. Neue Felder müssen stabil, quellengebunden und app-unabhängig sein.
6. Keine privaten Host-, Listener-, Journal-, Secret- oder App-Daten in öffentliche Artefakte übernehmen.
7. Vor Änderungen Livezustand, Branch, Dirty-State, PRs, CI und aktive Leases prüfen.
8. Vor Merge aktuellen Diff prüfen und grüne Gates verlangen.
9. Fehlende Belege ausdrücklich als Leerstelle benennen.

## Stop-Kriterien

Mit `[HARD-FAIL]` abbrechen, wenn:

- Zielzustand oder Eigentümer einer Wahrheit unklar ist;
- ein überlappender PR, Worktree oder Lease plausibel ist;
- private Runtime- oder Secret-Daten offengelegt würden;
- eine nötige Lösch-, Rename-, Shutdown- oder Merge-Autorisierung fehlt;
- Tests oder Review-Evidence für den behaupteten Abschluss fehlen.

## Abschlussbericht

- **Geänderte Dateien:**
- **Geprüfte Quellen:**
- **Offene Leerstellen:**
- **Risiko/Nutzen:**
- **Nächste Aktion:**
