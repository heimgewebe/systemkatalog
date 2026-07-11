# CAB-QA-008 — External Manifest Refresh v1

Status: umgesetzt
Datum: 2026-07-09
Organführung: Cabinet -> RepoBrief/Lenskit

## Ausgangslage

CAB-QA-007 erzeugt read-only Live-Signale aus External-Dump-Registry und Maintenance Report. Am 2026-07-09 meldete der Maintenance Report zwei P2-Freshness-Findings, weil die registrierten RepoBrief-/Lenskit-Manifestreferenzen älter als `maxAgeHours=48` waren.

## Scope

CAB-QA-008 aktualisiert die Cabinet-Konsumoberfläche für externe RepoBrief-/Lenskit-Artefakte:

- begrenzte externe Manifestreferenzen aus einem bestehenden Cabinet-Bundle schreiben;
- Registry-Beobachtung auf die frischen Manifestreferenzen setzen;
- CAB-QA-007-Signale neu erzeugen;
- Maintenance-Report-Prüfung gegen die tatsächliche Manifestdatei härten.

## Nicht-Scope

- keine RepoBrief-/Lenskit-Dump-Erzeugung durch Cabinet;
- keine Queue-, Bureau-, Grabowski-, Merge-, Push- oder Runtime-Wirkung;
- keine Claim-Wahrheit aus Manifestfrische ableiten;
- keine regelmäßige Automation aktivieren.

## Stop-Kriterium

Stoppen, wenn kein aktuelles bestehendes Bundle-Manifest belegbar ist, eine Manifestreferenz nicht relativ bleibt, der Registry-Contract fehlschlägt oder der Maintenance Report trotz Refresh Findings meldet.

## Target-Proof

- `python3 scripts/validate_external_dump_sources.py --json` PASS
- `python3 scripts/write_cabinet_maintenance_report.py --check --json` PASS
- `python3 -m unittest scripts.tests.test_cabinet_maintenance_report` PASS
- `python3 -m unittest scripts.tests.test_external_dump_sources scripts.tests.test_cabinet_live_signals` PASS

## Ergebnis

Der aktuelle Cabinet-Ball ist umgesetzt, wenn der PR-Diff die externen Manifestdateien, die Registry-Aktualisierung, die Signalaktualisierung, die Prüfverstärkung und diesen Befund enthält.
