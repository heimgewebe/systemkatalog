# Cabinet Agent Entry

Dieses Dokument ist der kanonische Einstieg für LLMs und Agenten im Cabinet-Repo während der Migration zum Heimgewebe-Systemkatalog.

## Lesereihenfolge

1. [README.md](README.md) — Zielrolle und Schnellstart.
2. [policy/system-catalog.v1.json](policy/system-catalog.v1.json) — maschinenlesbare Rollen- und Wirkungsgrenze.
3. [rendered/system-catalog.md](rendered/system-catalog.md) — deterministisch erzeugte Leseansicht.
4. [registry/ecosystem/authority-matrix.v1.json](registry/ecosystem/authority-matrix.v1.json) — Wahrheitszuständigkeiten.
5. [registry/ecosystem/nodes.json](registry/ecosystem/nodes.json) und [registry/ecosystem/edges.json](registry/ecosystem/edges.json) — kanonische stabile Katalogregistry.
6. [docs/migration/cabinet-surface-matrix-v1.md](docs/migration/cabinet-surface-matrix-v1.md) — Keep/Simplify/Move/Archive/Remove-Zuordnung.
7. [catalog/system-catalog.schema.v1.json](catalog/system-catalog.schema.v1.json) und [catalog/system-catalog.example.v1.json](catalog/system-catalog.example.v1.json) — Zielformat und ausdrücklich nichtkanonisches Beispiel.
8. Frühere Role-Boundary-, Radar-, Gemini- und Raumdokumente nur als Migrations- oder historische Quellen lesen, nicht als Zielarchitektur.

## Zielrolle

Cabinet ist ein app-unabhängiger Systemkatalog. Es beschreibt:

- vorhandene Systeme;
- Zweck und ausdrückliche Nicht-Zuständigkeit;
- Wahrheitszuständigkeiten;
- stabile Beziehungen;
- Einstiegspunkte.

Cabinet pflegt keine Aufgabenpriorität, keinen Taskstatus, keine Runtime-Gesundheit, keine Merge-Reife, keine aktive Agentendisposition und keinen Schedulerzustand.

Die externe Cabinet AI Workspace App ist nur ein vorübergehender optionaler Viewer. Sie ist weder Canon noch Voraussetzung für Validierung, Rendering oder Agentenorientierung.

## Wahrheitsordnung

- Bureau ist primär für Aufgaben, Queue, Claims, Handoffs und Receipts.
- Grabowski ist primär für freigegebene lokale und repositorybezogene Ausführung.
- GitHub ist primär für Repositories, Branches, Pull Requests, Issues und Reviews.
- CI und Review-Gates sind primär für technische Prüfsignale.
- Runtime, systemd, Logs und Healthchecks sind primär für laufende Dienste.
- RepoBrief / Lenskit ist primär für extern erzeugte Snapshots und zitierfähigen Repositorykontext.
- Leitstand ist die allgemeine Live-Anzeige.
- Cabinet besitzt nur die stabile Ökosystem-Semantik und die Zuordnung von Wahrheitsdomänen zu ihren Primärquellen.

## Arbeitsregel

1. Erst lesen, dann handeln.
2. Bei Cabinet-Fragen vorhandene Merge-Dumps nur als Snapshot behandeln; aktuelle Repo-/PR-Zustände gegen GitHub oder lokalen Working Tree prüfen.
3. Sidecars, Health-Berichte und Reading Packs sind Navigation oder Diagnose, keine Inhaltswahrheit.
4. Keine Claims aus Mermaidkarten als Beweis verwenden. Karten sind Projektionen.
5. Keine wechselnden Zustände aus GitHub, Bureau, CI oder Runtime in Cabinet kopieren.
6. Neue Katalogfelder müssen stabil, quellengebunden und app-unabhängig sein.
7. Das nichtkanonische Beispiel unter `catalog/` darf nie als vollständige Registry behandelt werden.
8. Mutationen eng schneiden und an den aktiven Bureau-Task binden.
9. Kein Merge und kein direkter Main-Eingriff ohne aktuelle Head-Prüfung, Diff-Review, grüne Gates und berücksichtigte Findings.
10. Erfinde keine Dateiinhalte. Wenn Kontext fehlt, nutze einen extern erzeugten RepoBrief-/Lenskit-Dump oder benenne die Leerstelle ausdrücklich.
11. Öffentliche Artefakte dürfen keine privaten Host-, Unit-, Listener-, Port-, Journal-, Reachability-, Secret- oder App-Daten enthalten.
12. Runtime-Abschaltung, Datenlöschung und Repository-Rename benötigen jeweils eine separate Bureau-Autorisierung.

## Organrollen

- Heimgewebe-Systemkatalog: stabile Systeme, Zwecke, Grenzen, Truth Ownership, Beziehungen und Einstiegspunkte.
- Bureau: Aufgaben, Taktung, Kandidaten, Claims, Receipts und Abschluss.
- Grabowski: lokale/repositorybezogene Ausführung und Review-Gates.
- RepoBrief / Lenskit: extern erzeugte zitierfähige Kontext- und Dump-Artefakte.
- Leitstand: allgemeine Live-Anzeige und Operator-Oberfläche.
- Schauwerk: spezialisierte Visualisierung.
- Heimlern: retrospektive Outcome-Auswertung und proposal-only Lernvorschläge.
- Chronik: append-only Ereigniskontinuität, sofern tatsächlich konsumiert.
- GitHub / CI / Runtime: harte Primärrealität für ihre jeweiligen Domänen.
- Externe Agenten: Vorschlag, Review oder Patch; keine unmittelbare Mutationshoheit aus Cabinet heraus.

## Stop-Kriterien

Wenn ein Stop-Kriterium greift, brich die Ausführung sofort ab und antworte zwingend mit dem Präfix `[HARD-FAIL]`, gefolgt von einer kurzen Begründung. Starte keine weiteren Lösungsversuche.

Stop-Kriterien:

- der lokale oder remote Zielzustand ist nicht eindeutig;
- ein überlappender offener PR oder Worktree ist plausibel;
- ein Schritt würde Secrets, private Runtime-Daten oder `.agents`-Runtime-Inhalte offenlegen;
- die Aufgabe setzt eine nicht vorliegende Freigabe, Lösch-, Shutdown-, Rename- oder Merge-Entscheidung voraus;
- Tests, Gates oder Review-Evidence fehlen, sind aber für den Anspruch nötig.

## Minimaler Bericht nach Arbeit

Generiere nach Abschluss exakt diese Liste:

- **Geänderte Dateien:**
- **Geprüfte Quellen:**
- **Offene Leerstellen:**
- **Risiko/Nutzen:**
- **Nächste Aktion:**
