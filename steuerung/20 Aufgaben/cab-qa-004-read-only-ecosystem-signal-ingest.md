# CAB-QA-004 — Read-only Ecosystem Signal Ingest

## Status

- Zustand: planned
- Owner: Cabinet
- Bureau-Kandidat: `claim:cabinet-read-only-ecosystem-signal-ingest-v0`
- Erstellt: 2026-07-05
- Wirkung: read-only

## Ziel

Cabinet bekommt eine erste Wahrnehmungsschicht fuer reale Oekosystemsignale. Der Slice validiert ein maschinenlesbares Signalformat mit `observedAt`, Primaerquelle, Evidence, Frischebasis und Effektabschluss.

## These

Ohne echte Signale bleibt der Claim-Ledger selbstreferenziell.

## Antithese

Wenn Signale direkt als Arbeit interpretiert werden, entsteht eine verdeckte Orchestrierung.

## Synthese

CAB-QA-004 baut nur Contract, Schema, Validator, Test und Fixture. Bureau darf daraus noch keine operative Aufgabe ableiten.

## Akzeptanz

- Contract und Schema fuer `cabinet_ecosystem_signal` sind vorhanden.
- Validator prueft JSONL-Signale.
- Test und Fixture pruefen Frischebasis, Evidence und Effektabschluss.
- Alle operativen Wirkungen bleiben ausgeschlossen.

## Nicht-Ziele

- kein Bureau-Import;
- keine Queue-Aenderung;
- keine Delegation;
- keine Runtime-Aenderung;
- keine Dump-Erzeugung;
- kein Ersatz fuer GitHub, CI oder Runtime als Primaerquellen.

## Naechste Aktion

`run_read_only_ecosystem_signal_ingest_for_one_fixture_repo`
