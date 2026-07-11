# CAB-QA-006 — Live Signal Probe v0

## Status

- Zustand: reviewable
- Owner: Cabinet
- Wirkung: read-only
- Erstellt: 2026-07-06

## Ziel

CAB-QA-006 legt ein erstes echtes, datiertes Ecosystem-Signal ab. Es nutzt GitHub- und CI-Zustand zu Cabinet PR #75 als Primaerquelle und prueft, dass die Signale dem Contract aus CAB-QA-005 entsprechen.

## These

Der Signalcontract wird erst belastbar, wenn mindestens ein echtes beobachtetes Signal ausserhalb der Test-Fixture validiert wird.

## Antithese

Ein Live-Signal darf nicht als Task-Freigabe, Bureau-Import, Schreibrecht oder Runtime-Wahrheit gelesen werden.

## Synthese

Dieser Slice erzeugt nur ein read-only JSONL-Probe-Artefakt und validiert es mit dem bestehenden Signalvalidator. Er erzeugt keine operative Wirkung und baut noch keinen Signal-Producer.

## Beleg

- `pruefung/10 Laeufe/cab-qa-006-live-signal-probe.jsonl`
- `python3 scripts/validate_ecosystem_signals.py --input 'pruefung/10 Laeufe/cab-qa-006-live-signal-probe.jsonl' --json`

## Nicht-Ziele

- kein Bureau-Import;
- keine Queue-Aenderung;
- keine Delegation;
- keine Runtime-Aenderung;
- kein Git-Schreibrecht aus dem Signal;
- keine Dump-Erzeugung;
- kein Ersatz fuer GitHub oder CI als Primaerquelle;
- noch keine CI-Workflow-Erweiterung;
- noch kein Signal-Producer.

## Naechste Aktion

`review_live_signal_probe_before_any_signal_producer`
