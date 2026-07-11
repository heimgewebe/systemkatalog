# CAB-QA-001 — Cabinet-Kohaerenzradar v1

Status: registered
Datum: 2026-07-05
Organfuehrung: Cabinet -> Bureau
Bridge claim: `claim:cabinet-qa-radar-cab-qa-001-v0`

## Entscheidung

Cabinet registriert einen read-only Wartungs- und Kohaerenzradar als Bureau-Kandidat. Bureau darf den Kandidaten lesen und spaeter entscheiden, ob daraus ein Task-Kandidat wird.

## Warum jetzt

RepoBrief-/Lenskit-Dumps werden extern erzeugt. Cabinet soll deshalb nicht doppelt erzeugen, sondern pruefen, ob Registry, Claims, Evidence, Bridge-Grenzen und externe Snapshot-Flaechen hinreichend kohärent sind.

## Scope CAB-QA-001

- Policy: `docs/blueprints/cabinet-qa-radar-v1.md`
- Report-Contract: `docs/contracts/cabinet-maintenance-report-v1.md`
- Report-Schema: `docs/contracts/cabinet-maintenance-report-v1.schema.json`
- Producer: `scripts/write_cabinet_maintenance_report.py`
- Tests: `scripts/tests/test_cabinet_maintenance_report.py`
- Registry-Claim: `registry/ecosystem/claims.jsonl`
- Bridge-Zulassung: `registry/ecosystem/bureau-bridge.json`

## Bureau-Kandidat

| Feld | Wert |
|---|---|
| id | `claim:cabinet-qa-radar-cab-qa-001-v0` |
| status | `evidenced` |
| evidence | Blueprint, Contract, Schema, Producer, diese Aufgabe |
| expires_at_or_refresh_hint | `2026-08-04` oder frueher bei spezifizierter externer Dump-Automation |
| next_action | `run_cabinet_maintenance_report_before_bureau_task_creation` |
| responsible_organ | `cabinet` |

## Stop-Kriterien

- Der Report erzeugt Bureau-Tasks automatisch.
- Der Report startet Grabowski oder andere Agenten.
- Der Report erzeugt RepoBrief-/Lenskit-Dumps.
- Der Report mutiert Runtime, Repository, Queue oder Cleanup-Zustand.
- Der Report behandelt Map- oder Registry-Kanten als externe Wahrheit.

## Target-Proof

```bash
python3 scripts/write_cabinet_maintenance_report.py --check
python3 -m unittest discover -s scripts/tests -p 'test_cabinet_maintenance_report.py'
python3 scripts/validate_ecosystem_map.py
```

## Risiko / Nutzen

Nutzen: fruehere Drift-Erkennung, bessere Bureau-Zuarbeit, explizite Evidenzgrenzen, weniger Kontextverlust.

Risiko: Wartungsreports koennen als Freigabe missverstanden werden. Gegenmittel: effect flags bleiben false, doesNotEstablish bleibt Pflicht, Bureau-Kandidat bleibt proposal-only.

## Epistemische Leere

Pfad, Manifest, Frequenz, Hashes und Retention der externen RepoBrief-/Lenskit-Dump-Automation fehlen noch. Noetig fuer belastbare Freshness-Pruefung externer Dumps.
