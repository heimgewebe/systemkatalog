# CAB-QA-003 — External-Dump-Quellenvertrag v1

Status: registered
Datum: 2026-07-05
Organfuehrung: Cabinet -> RepoBrief/Lenskit -> Bureau
Bridge claim: `claim:external-dump-sources-contract-v1`

## Entscheidung

Cabinet registriert einen Quellenvertrag fuer extern erzeugte RepoBrief-/Lenskit-Dumps. Cabinet erzeugt diese Dumps nicht selbst, sondern prueft die beobachtbare Manifest-Oberflaeche.

## Warum jetzt

CAB-QA-001 hat die fehlende Dump-Spezifikation als epistemische Luecke markiert. Diese Luecke wird hier in einen pruefbaren Vertrag umgewandelt: Pfadmuster, Manifest-Kind, Kadenz, Maximalalter, Hashalgorithmus, Artefakt-Suffixe und Beobachtungsstatus.

## Scope CAB-QA-003

- Contract: `docs/contracts/cabinet-external-dump-sources-v1.md`
- Schema: `docs/contracts/cabinet-external-dump-sources-v1.schema.json`
- Registry: `registry/ecosystem/external-dump-sources.json`
- Validator: `scripts/validate_external_dump_sources.py`
- Tests: `scripts/tests/test_external_dump_sources.py`
- Report-Anbindung: `scripts/write_cabinet_maintenance_report.py`

## Stop-Kriterien

- Cabinet erzeugt RepoBrief-/Lenskit-Dumps.
- Cabinet interpretiert einen Dump als semantische Wahrheit.
- Ein fehlendes Manifest wird als Runtime-Fehler behandelt.
- Ein Freshness-Finding erzeugt automatisch Bureau-Task, Queue-Mutation oder Grabowski-Delegation.

## Target-Proof

```bash
python3 scripts/validate_external_dump_sources.py
python3 -m unittest discover -s scripts/tests -p 'test_external*.py'
python3 scripts/write_cabinet_maintenance_report.py --check
```

## Ergebnisgrenze

Nach diesem Slice ist die Spezifikationsluecke geschlossen. Die konkrete Beobachtung aktueller Manifeste bleibt offen, bis die externe Automation Manifest-Referenzen publiziert.
