# Cabinet Agent Entry

Dieses Dokument ist der kanonische Einstieg fuer LLMs und Agenten im Cabinet-Repo.

## Lesereihenfolge

1. [README.md](README.md) — Entree und Schnellstart.
2. [docs/blueprints/ecosystem-map-v0.md](docs/blueprints/ecosystem-map-v0.md) — Zweck, Dateien, Wahrheitsgrenzen und Reifekriterien der Karte.
3. [rendered/ecosystem-map.mmd](rendered/ecosystem-map.mmd) — visuelle Mermaidkarte.
4. [docs/blueprints/o.json](docs/blueprints/o.json) — kompakter maschinenlesbarer Seed.
5. [registry/ecosystem/nodes.json](registry/ecosystem/nodes.json), [registry/ecosystem/edges.json](registry/ecosystem/edges.json), [registry/ecosystem/claims.jsonl](registry/ecosystem/claims.jsonl) — Graph, Kanten und Claims.
6. [docs/blueprints/heim-pc-operatorium-index-v0.md](docs/blueprints/heim-pc-operatorium-index-v0.md) — Heim-PC als Operatorium.
7. [docs/blueprints/agent-routing-brief-v0.md](docs/blueprints/agent-routing-brief-v0.md) — Aufgaben- und Agentenroute.

## Wahrheitsordnung

- GitHub ist primaer fuer Branches, Pull Requests, Issues und Reviews.
- CI und Review-Gates sind primaer fuer technische Pruefsignale.
- Runtime, systemd, Logs und Healthchecks sind primaer fuer laufende Dienste.
- Contracts, Schemas und Tests sind primaer fuer maschinenpruefbare Invarianten.
- Menschliche Entscheidungen sind primaer fuer Prioritaet, Freigabe und Abbruch.
- Cabinet verbindet Aussagen und Bedeutung; es ersetzt die primaeren Quellen nicht.

## Arbeitsregel

1. Erst lesen, dann handeln.
2. Bei Cabinet-Fragen vorhandene Merge-Dumps nur als Snapshot behandeln; aktuelle Repo-/PR-Zustaende gegen GitHub oder lokalen Working Tree pruefen.
3. Sidecars, Health-Berichte und Reading Packs sind Navigation oder Diagnose, keine Inhaltswahrheit.
4. Keine Claims aus der Mermaidkarte als Beweis verwenden. Graphkanten brauchen Quelle, Status und Kontext.
5. Widersprueche sichtbar lassen und einordnen.
6. Mutationen eng schneiden: Wegweiser, Belege oder klar begrenzte Docs/Code-Slices.
7. Kein Merge und kein direkter Main-Eingriff ohne aktuelle Head-Pruefung, Diff-Review und beruecksichtigte Findings.

## Organrollen

- Cabinet: Sinn, Evidenz, Priorisierung, Lernen, Kartensemantik.
- Bureau: Aufgaben, Taktung, Kandidaten, Receipts, Rueckmeldung.
- Grabowski: lokale/repo-bezogene Ausfuehrung und Review-Gates.
- RepoBrief / Lenskit: zitierfaehige Kontextansicht.
- Steuerboard: read-only Repo-State-Signal, keine Freigabe.
- Vibe-Lab: Methoden- und Evidence-Lab.
- Chronik: Event-Trace und historische Kontinuitaet.
- Schauwerk: Renderer und visuelle Flaeche, nicht Karten-Canon.
- GitHub / CI / Runtime: harte Realitaetspruefung.
- Externe Agenten: Vorschlag, Review, Patch; keine direkte Mutationshoheit.

## Stop-Kriterien

Stoppe und berichte statt zu handeln, wenn:

- der lokale oder remote Zielzustand nicht eindeutig ist;
- ein ueberlappender offener PR oder Worktree plausibel ist;
- ein Schritt Secrets, private Runtime-Daten oder `.agents`-Runtime-Inhalte offenlegen wuerde;
- die Aufgabe eine Freigabe, Priorisierung oder Loesch-/Merge-Entscheidung voraussetzt;
- Tests, Gates oder Review-Evidence fehlen, aber fuer den Anspruch noetig sind.

## Minimaler Bericht nach Arbeit

Nenne: geaenderte Dateien, gepruefte Quellen, offene Leerstellen, Risiko/Nutzen, naechste Aktion.
