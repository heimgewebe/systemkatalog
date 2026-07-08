# Cabinet Gemini Maintenance Evidence Packet Contract v1

## Status

- Typ: Contract
- Version: 1
- Owner: Cabinet
- Modus: deterministic curated input packet
- Gemini-Wirkung: keine Ausfuehrung
- Bureau-Wirkung: keine direkte Task-Erzeugung
- Generator: `scripts/write_gemini_maintenance_evidence_packet.py`
- Schema: `docs/contracts/cabinet-gemini-maintenance-evidence-packet-v1.schema.json`
- Consumer Output Contract: `docs/contracts/cabinet-gemini-maintenance-scan-v1.md`

## Zweck

`cabinet_gemini_maintenance_evidence_packet` ist die einzige zulaessige Eingabemappe fuer einen spaeteren Gemini-Maintenance-Dry-Run.

Das Paket ist kein Modelllauf. Es startet Gemini nicht, aktiviert keinen Scheduler, erzeugt keine Issues, Pull Requests oder Kommentare, schreibt keine Bureau-Tasks, mutiert keine Queue, dispatcht Grabowski nicht, pusht oder merged nicht, veraendert keine Runtime und fordert keine Secrets an.

## Input-Policy

Der Generator arbeitet mit einer festen Allowlist. Der erste Dry Run darf nur diese Repo-Dateien und einen deterministisch erzeugten Maintenance Report enthalten:

- `AGENTS.md`
- `README.md`
- `docs/blueprints/cabinet-maintenance-radar-v0.md`
- `docs/blueprints/agent-routing-brief-v0.md`
- `docs/contracts/cabinet-frontier-v1.md`
- `docs/contracts/cabinet-gemini-maintenance-scan-v1.md`
- `registry/ecosystem/nodes.json`
- `registry/ecosystem/edges.json`
- `registry/ecosystem/claims.jsonl`
- `registry/ecosystem/external-dump-sources.json`
- generated `cabinet_maintenance_report`

Der Generator darf keinen freien Repository-Crawl ausfuehren. Pfade ausserhalb der Allowlist sind kein Teil des Pakets.

## Harte Ausschluesse

Das Paket darf nicht enthalten:

- `.git/`
- `.agents/`
- `.global-agents/`
- `.jobs/`
- `.cabinet-state/`
- `.conversations/`, `.memory/`, `.messages/`
- `.env`, `.env.*`, `.cabinet.env`, `runtime.env`
- `.cabinet.db`, SQLite-/Datenbankdateien
- `daemon-token`
- Key- und Zertifikatsdateien wie `.key`, `.pem`, `.p12`, `.pfx`
- Logs wie `.log`
- private key marker wie `-----BEGIN PRIVATE KEY-----`

## Manifest-Pflichten

Jeder Eintrag enthaelt:

- `ref` als Evidence-Referenz
- `path`
- `role`
- `mediaType`
- `sha256`
- `bytes`
- `lines`
- `content`

Die Zusammenfassung enthaelt:

- Anzahl der Eintraege
- Anzahl kuratierter Repo-Dateien
- Anzahl generierter Eintraege
- Gesamtbytes
- `manifestSha256` ueber Eintragsmetadaten und Maintenance-Report-Summary
- Status und Finding-Zahl des generierten Maintenance Reports

## Effektabschluss

Alle `effectFlags` muessen existieren und `false` sein:

- `issueCreationAllowed`
- `prCreationAllowed`
- `commentCreationAllowed`
- `taskCreationAllowed`
- `queueMutationAllowed`
- `grabowskiDispatchAllowed`
- `pushOrMergeAllowed`
- `runtimeMutationAllowed`
- `secretRequestAllowed`
- `dumpGenerationAllowed`
- `cleanupActionAllowed`
- `externalModelExecutionAllowed`
- `scheduleAllowed`

## Nicht behauptet

Ein valides Evidence Packet beweist nicht:

- Gemini-Verfuegbarkeit
- Gemini-Schedulability
- Dry-Run-Erfolg
- Scan-Qualitaet
- Claim-Wahrheit
- Task-Freigabe
- Bureau-Import
- Merge-Reife
- Runtime-Korrektheit
- Secret-Abwesenheit ausserhalb der kuratierten Inputs
- vollstaendigen Repository-Kontext
- autonomen Dispatch

## Nächster erlaubter Schritt

Nach diesem Paket ist nur ein manuell gepruefter Dry-Run-Workflow als eigener PR zulaessig. Scheduling bleibt blockiert, bis mehrere manuelle Dry Runs mit stabilen Outputs belegt sind.
