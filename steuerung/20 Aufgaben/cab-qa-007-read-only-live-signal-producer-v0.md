# CAB-QA-007 — Read-only Live Signal Producer v0

Status: done
Datum: 2026-07-06
Organfuehrung: Cabinet

## Entscheidung

CAB-QA-007 baut keinen GitHub-Scraper und keinen Bureau-Dispatch. Der erste Producer liest nur bereits beobachtete Cabinet-Oberflaechen: External-Dump-Registry und Maintenance Report.

## These

Nach CAB-QA-004 sind externe Manifestreferenzen beobachtet. Cabinet kann daraus ein valides, datiertes Signal erzeugen, ohne neue Dump- oder Runtime-Wirkung zu bauen.

## Antithese

Ein Signal-Producer kann schnell als Automationsfreigabe missverstanden werden. Wenn er Queue, Dispatch, Claims oder Bureau-Import ausloest, kippt Wahrnehmung in Handlung.

## Synthese

`scripts/write_cabinet_live_signals.py` produziert nur `cabinet_ecosystem_signal`-JSONL. Alle Effektflags bleiben false. Der Lauf ist eine Wahrnehmung, keine Entscheidung.

## Scope

- External-Dump-Observationen aus `registry/ecosystem/external-dump-sources.json` signalisieren.
- Maintenance-Report-Status signalisieren.
- Output nach `pruefung/10 Laeufe/cab-qa-007-live-signal-producer-v0.jsonl` schreiben.
- Bestehenden Signal-Validator nutzen.
- Keine Bureau-Queue, kein Dispatch, keine Claim-Promotion, keine Dump-Erzeugung.

## Target-Proof

- `python3 -m unittest scripts.tests.test_cabinet_live_signals -v`
- `python3 scripts/write_cabinet_live_signals.py --output 'pruefung/10 Laeufe/cab-qa-007-live-signal-producer-v0.jsonl' --json`
- `python3 scripts/validate_ecosystem_signals.py --input 'pruefung/10 Laeufe/cab-qa-007-live-signal-producer-v0.jsonl' --json`
- `python3 scripts/write_cabinet_maintenance_report.py --check --json`

## Epistemische Leere

Der Producer beweist nicht, dass externe Manifestpublikation dauerhaft automatisiert ist. Noetig dafuer bleibt ein separater Publikations-/Freshness-Run ausserhalb von Cabinet.
