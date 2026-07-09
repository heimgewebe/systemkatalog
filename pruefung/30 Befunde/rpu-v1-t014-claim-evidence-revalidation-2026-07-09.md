# RPU-V1-T014 Claim Evidence Revalidation

Datum: 2026-07-09
Status: implemented-local
Task: `RPU-V1-T014`
Owner surface: Cabinet maintenance report

## Dialektik

These: Cabinet-Claims sollen auf RepoBrief-Zitate oder Source-Ranges mit Hash- und Freshness-Metadaten zeigen können, damit gebrochene oder alte Evidenz sichtbar wird.

Antithese: RepoBrief darf dadurch nicht zur Claim-Wahrheitsinstanz werden. Ein passender Hash belegt nur, dass die referenzierte Evidenzoberfläche noch gleich ist; er belegt nicht, dass die Claim-Aussage wahr ist.

Synthese: Der Maintenance Report ergänzt eine strikt begrenzte `claimEvidenceRevalidations`-Oberfläche. Sie unterscheidet `still_established`, `stale`, `missing`, `changed` und `unverifiable`, bleibt aber effect-closed und claim-truth-negierend.

## Umsetzung

- `scripts/write_cabinet_maintenance_report.py`
  - akzeptiert Legacy-String-Evidenz weiter;
  - akzeptiert strukturierte Evidenzobjekte mit `type: repobrief_citation` oder `type: repobrief_source_range`;
  - prüft lokale Pfade, Source-Range-Gültigkeit, SHA-256 und Freshness-Fenster;
  - erzeugt Findings für strukturierte Evidenz mit Status `stale`, `missing`, `changed` oder `unverifiable`;
  - erzeugt keine Findings für externe/textuelle Legacy-Strings ohne Metadaten, markiert sie aber als `unverifiable`.

- `docs/contracts/cabinet-maintenance-report-v1.schema.json`
  - ergänzt `claimEvidenceRevalidations`;
  - ergänzt `summary.claimEvidenceRevalidationCounts`.

- `docs/contracts/cabinet-maintenance-report-v1.md`
  - dokumentiert Statusvokabular, erlaubte strukturierte Felder und Nicht-Claims.

- `scripts/tests/test_cabinet_maintenance_report.py`
  - deckt `still_established`, `changed`, `stale`, `missing` und `unverifiable` ab.

## Validierung

- `python3 -m unittest scripts.tests.test_cabinet_maintenance_report`
  - Ergebnis: 13 Tests, OK.
- `python3 scripts/write_cabinet_maintenance_report.py --check --json`
  - Ergebnis: `ok=true`, `status=pass`, `findingCount=0`, `bureauCandidateCount=5`.
- `python3 scripts/validate_ecosystem_map.py`
  - Ergebnis: PASS.
- `python3 -m unittest discover scripts/tests`
  - Ergebnis: 274 Tests, OK.
  - Hinweis: Ein erwarteter Negativtest schreibt eine `ERROR: output path escapes repository`-Zeile nach stderr; der Testlauf endet trotzdem mit OK.

## Grenzen

Diese Änderung etabliert nicht:

- Claim-Wahrheit;
- Repo-Verständnis durch RepoBrief;
- RepoBrief als Claim-Truth-Oracle;
- Dump-Erzeugung durch Cabinet;
- Bureau-Task-Freigabe;
- Runtime-Korrektheit;
- Merge-Readiness.

## Offene Lücke

Fehlt: echte RepoBrief-Citation-IDs aus aktuellen RepoBrief-Bundles in produktiven Cabinet-Claims.

Nötig für: praktische Ende-zu-Ende-Nutzung der neuen strukturierten Evidenzform jenseits der getesteten Maintenance-Report-Oberfläche.
