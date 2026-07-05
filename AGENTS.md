# Cabinet Agent Entry

Dieses Dokument ist der kanonische Einstieg für LLMs und Agenten im Cabinet-Repo.

## Lesereihenfolge

1. [README.md](README.md) — Entrée und Schnellstart.
2. [docs/blueprints/ecosystem-map-v0.md](docs/blueprints/ecosystem-map-v0.md) — Zweck, Dateien, Wahrheitsgrenzen und Reifekriterien der Karte.
3. [rendered/ecosystem-map.mmd](rendered/ecosystem-map.mmd) — lesbare Mermaid-Uebersicht.
4. [rendered/ecosystem-registry-map.mmd](rendered/ecosystem-registry-map.mmd) — generierte Registry-Projektion aus Knoten und Kanten.
5. [docs/blueprints/o.json](docs/blueprints/o.json) — kompakter maschinenlesbarer Seed.
6. [registry/ecosystem/nodes.json](registry/ecosystem/nodes.json), [registry/ecosystem/edges.json](registry/ecosystem/edges.json), [registry/ecosystem/claims.jsonl](registry/ecosystem/claims.jsonl) — Graph, Kanten und Claims.
7. [docs/blueprints/heim-pc-operatorium-index-v0.md](docs/blueprints/heim-pc-operatorium-index-v0.md) — Heim-PC als Operatorium.
8. [docs/blueprints/agent-routing-brief-v0.md](docs/blueprints/agent-routing-brief-v0.md) — Aufgaben- und Agentenroute.

## Wahrheitsordnung

- GitHub ist primär für Branches, Pull Requests, Issues und Reviews.
- CI und Review-Gates sind primär für technische Prüfsignale.
- Runtime, systemd, Logs und Healthchecks sind primär für laufende Dienste.
- Contracts, Schemas und Tests sind primär für maschinenprüfbare Invarianten.
- Menschliche Entscheidungen sind primär für Priorität, Freigabe und Abbruch.
- Cabinet verbindet Aussagen und Bedeutung; es ersetzt die primären Quellen nicht.

## Arbeitsregel

1. Erst lesen, dann handeln.
2. Bei Cabinet-Fragen vorhandene Merge-Dumps nur als Snapshot behandeln; aktuelle Repo-/PR-Zustände gegen GitHub oder lokalen Working Tree prüfen.
3. Sidecars, Health-Berichte und Reading Packs sind Navigation oder Diagnose, keine Inhaltswahrheit.
4. Keine Claims aus Mermaidkarten als Beweis verwenden. Die Uebersicht darf buendeln; die Registry-Projektion ist ein Driftcheck, kein Wahrheitsersatz. Graphkanten brauchen Quelle, Status und Kontext.
5. Widersprüche sichtbar lassen und einordnen.
6. Mutationen eng schneiden: Wegweiser, Belege oder klar begrenzte Docs/Code-Slices.
7. Kein Merge und kein direkter Main-Eingriff ohne aktuelle Head-Prüfung, Diff-Review und berücksichtigte Findings.
8. Erfinde keine Dateiinhalte. Wenn Kontext fehlt, fordere einen Read-Dump über Lenskit/RepoBrief an oder benenne die Leerstelle ausdrücklich.

## Organrollen

- Cabinet: Sinn, Evidenz, Priorisierung, Lernen, Kartensemantik.
- Bureau: Aufgaben, Taktung, Kandidaten, Receipts, Rückmeldung.
- Grabowski: lokale/repo-bezogene Ausführung und Review-Gates.
- RepoBrief / Lenskit: zitierfähige Kontextansicht.
- Steuerboard: read-only Repo-State-Signal, keine Freigabe.
- Vibe-Lab: Methoden- und Evidence-Lab.
- Chronik: Event-Trace und historische Kontinuität.
- Schauwerk: Renderer und visuelle Fläche, nicht Karten-Canon.
- GitHub / CI / Runtime: harte Realitätsprüfung.
- Externe Agenten: Vorschlag, Review, Patch; keine direkte Mutationshoheit.

## Stop-Kriterien

Wenn ein Stop-Kriterium greift, brich die Ausführung sofort ab und antworte zwingend mit dem Präfix `[HARD-FAIL]`, gefolgt von einer kurzen Begründung. Starte keine weiteren Lösungsversuche.

Stop-Kriterien:

- der lokale oder remote Zielzustand ist nicht eindeutig;
- ein überlappender offener PR oder Worktree ist plausibel;
- ein Schritt würde Secrets, private Runtime-Daten oder `.agents`-Runtime-Inhalte offenlegen;
- die Aufgabe setzt eine Freigabe, Priorisierung oder Lösch-/Merge-Entscheidung voraus;
- Tests, Gates oder Review-Evidence fehlen, sind aber für den Anspruch nötig.

## Minimaler Bericht nach Arbeit

Generiere nach Abschluss exakt diese Liste:

- **Geänderte Dateien:**
- **Geprüfte Quellen:**
- **Offene Leerstellen:**
- **Risiko/Nutzen:**
- **Nächste Aktion:**
