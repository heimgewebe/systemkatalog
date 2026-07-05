# CAB-QA-002 — Cabinet Maintenance Report CI

Status: implemented
Datum: 2026-07-05
Organfuehrung: Cabinet

## Entscheidung

Der vorhandene Cabinet Maintenance Report wird in die bestehende `Cabinet Maintenance Radar`-Automation eingebunden. Der Lauf bleibt read-only und erzeugt nur pruefbare CI-Signale sowie ein Report-Artefakt.

## These

CAB-QA-001 hat den Report-Producer, Contract und Testkern angelegt. Ohne CI-Lauf bleibt der Radar nur ein manuell nutzbares Werkzeug.

## Antithese

Der CI-Lauf darf nicht zur verdeckten Operativschicht werden. Ein Report darf keine Aufgaben, keine Agentenstarts und keine Systemaenderungen ausloesen.

## Synthese

CAB-QA-002 fuehrt den Report automatisch als Check aus, validiert seine JSON-Form, schreibt eine kurze Step-Summary und laedt den Report als Artefakt hoch. Die Semantik bleibt: Wartungssignal, keine Freigabe.

## Scope

- Workflow-Pfade fuer Maintenance-Report-Inputs erweitern.
- `test_cabinet_maintenance_report.py` im Radar-Workflow ausfuehren.
- `scripts/write_cabinet_maintenance_report.py --check --json` ausfuehren.
- Einen Report nach `.tmp/cabinet-maintenance-report.json` schreiben.
- JSON-Form mit `python3 -m json.tool` pruefen.
- Summary- und Statusartefakte hochladen.

## Non-Effects

- Keine RepoBrief-/Lenskit-Dump-Erzeugung.
- Keine Bureau-Task-Erzeugung.
- Keine Agenten-Delegation.
- Keine Merge-, Push- oder Cleanup-Wirkung.

## Target-Proof

- `python3 -m unittest discover -s scripts/tests -p 'test_cabinet_maintenance_report.py'`
- `python3 scripts/write_cabinet_maintenance_report.py --check --json`
- `python3 scripts/write_cabinet_maintenance_report.py --output .tmp/cabinet-maintenance-report.json --json`

## Epistemische Leere

Der CI-Lauf kann externe RepoBrief-/Lenskit-Frische erst vollstaendig bewerten, wenn `registry/ecosystem/external-dump-sources.json` oder ein aequivalenter Manifestvertrag spezifiziert ist.
