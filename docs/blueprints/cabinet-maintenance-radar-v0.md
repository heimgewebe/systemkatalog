# Cabinet Maintenance Radar v0

Status: draft
Datum: 2026-07-05
Owner: Cabinet

## Entscheidung

RepoBrief- und Lenskit-Dumps werden nicht mehr als Cabinet-Aufgabe behandelt. Sie werden ausserhalb von Cabinet erzeugt und von Cabinet nur als Eingangsartefakte mit Provenienz, Frische und Beleggrenze konsumiert.

Cabinet wird fuer den Oekosystembetrieb als read-only Kohaerenzradar ausgebaut: Es scannt Inkonsistenzen, strukturelle Fehler, Frische, Quellenordnung, Handoff-Reife, verbotene Effekte und Lernsignale. Es erzeugt Befunde und Vorschlaege, aber keine operativen Wirkungen.

Gemini bleibt bis zu einem bestandenen Capability-/Sandbox-Preflight eine blockierte, proposal-only Kapazitaet. Der aktuelle Preflight-Befund liegt unter [`pruefung/30 Befunde/cabinet-gemini-maintenance-preflight-v1.md`](../../pruefung/30%20Befunde/cabinet-gemini-maintenance-preflight-v1.md). Er blockiert Scheduling, weil kein konkreter Gemini-Ausfuehrungsweg mit Version/Pin, Auth-Modell, Permission-Manifest, Kosten-/Quota-Klasse und Log-Privacy-Grenze vorliegt.

## These

Der Betrieb braucht einen Ort, der quer ueber Repos, Karten, Claims, CI, Runtime-Belege und Agentenuebergaben nach Widerspruechen sucht.

## Antithese

Wenn Cabinet selbst Tasks erzeugt, Dispatch ausloest, Grabowski startet, Merges vorbereitet oder Runtime veraendert, wird aus dem Radar ein Schatten-Orchestrator. Das wuerde die bestehende Organtrennung beschaedigen.

## Synthese

Cabinet darf automatisch sehen, pruefen, priorisieren und Belege verdichten. Bureau besitzt Taktung und Receipts. Grabowski handelt erst nach Task- oder Operatorfreigabe. Heimlern bewertet rueckblickend Outcomes und schlaegt Anpassungen vor, wendet sie aber nicht direkt an.

## Scope

Erlaubte Scan-Klassen:

| Klasse | Zweck | Primaere Grenze |
|---|---|---|
| `consistency` | Widersprueche zwischen Registry, Claims, Docs, PR-/CI-/Runtime-Aussagen finden | keine Wahrheit aus Karten ableiten |
| `structural_error` | JSON, JSONL, Pfade, IDs, Links, Schemas und Pflichtfelder pruefen | keine semantische Readiness behaupten |
| `freshness` | ablaufende Claims, alte Evidence, fehlende externe Dumps und stale Snapshots melden | Frische ist kein Wahrheitsbeweis |
| `authority_order` | pruefen, ob Aussagen ihre primaere Quelle respektieren | Cabinet ersetzt GitHub, CI und Runtime nicht |
| `handoff_readiness` | Bureau-Kandidaten auf Evidence, Next Action und verantwortliches Organ pruefen | keine Task-Erzeugung |
| `effect_closure` | sicherstellen, dass Import, Dispatch, Queue, Merge, Push und Runtimewirkung deaktiviert bleiben | Vorschlag bleibt Vorschlag |
| `external_artifact_surface` | externe RepoBrief-/Lenskit-Artefakte auf Manifest, Hash, Zeitpunkt und Bezug pruefen | keine Dump-Erzeugung |
| `learning_feedback` | abgeschlossene Befunde und Receipts fuer Heimlern auswertbar machen | keine automatische Policy-Aenderung |

## Nicht-Ziele

Cabinet erzeugt in diesem Modell keine RepoBriefs und keine Lenskit-Dumps. Cabinet darf fehlende, alte oder widerspruechliche Dump-Artefakte melden, aber nicht deren Erzeugung uebernehmen.

Cabinet fuehrt keine Bereinigung aus, veraendert keine Runtime, erstellt keine Bureau-Tasks, delegiert nicht automatisch an Grabowski und leitet keine Autoritaet aus Mermaidkarten ab.

## Artefakte

### `cabinet.scan_finding.v1`

Ein einzelner maschinenlesbarer Befund eines Cabinet-Scans.

Pflichtfelder:

```text
id
scan_id
rule_id
subject
finding_type
severity
evidence
confidence
status
responsible_organ
next_action
created_at
```

### `cabinet.maintenance_report.v1`

Eine datierte Lageverdichtung aus mehreren Findings. Der Report ist ein Wartungssignal, keine Freigabe.

### `cabinet.maintenance_outcome.v1`

Rueckmeldung, was aus einem Finding wurde. Dieses Artefakt ist die wichtigste Bruecke zu Heimlern.

Pflichtfelder:

```text
finding_id
outcome
evidence
closed_at
reviewer
learning_allowed
```

### `cabinet.handoff_candidate.v1`

Optionaler Vorschlag fuer Bureau. Der Kandidat bleibt `proposal_only`, solange kein separates Review-Gate ihn hebt.

### `heimlern.policy_adjustment.proposed.v1`

Heimlern darf aus Outcomes Vorschlaege ableiten. Diese Vorschlaege bleiben proposed, bis Cabinet/Bureau sie reviewt.

## Heimlern-Einbindung

Heimlern wird nicht in den Scanpfad eingebaut. Es bekommt nur abgeschlossene Outcome-Records und historische Entscheidungssnapshots.

Erlaubt:

- False-Positive-Muster erkennen.
- Wiederkehrende Fehlerklassen melden.
- Scan-Regelgewichte vorschlagen.
- Review- und Handoff-Routing als Vorschlag bewerten.
- Confidence und Mindestfallzahl ausweisen.

Verboten:

- Scan-Regeln direkt aendern.
- Bureau-Tasks erzeugen.
- Grabowski automatisch delegieren.
- Merges, Pushes oder Runtime-Aktionen ausloesen.
- einzelne Outcomes als allgemeine Wahrheit behandeln.

Startbedingung: Heimlern darf erst produktiv angebunden werden, wenn die relevanten Contracts repariert und CI-gruen sind. Bis dahin ist die Einbindung Design- und Fixture-Arbeit.

## Organrollen

| Organ | Rolle |
|---|---|
| Cabinet | Kohaerenzradar, Bedeutung, Evidence, Priorisierung, Wartungsbefunde |
| Bureau | Taktung, Aufgaben, Kandidaten, Receipts, Handoff-Status |
| Grabowski | lokale und repo-bezogene Ausfuehrung nach Freigabe |
| RepoBrief / Lenskit | extern erzeugte Kontext- und Dump-Artefakte |
| Heimlern | retrospektive Outcome-Auswertung und proposal-only Policy-Vorschlaege |
| Chronik | Ereigniskontinuitaet und historische Entscheidungsspuren |
| GitHub / CI / Runtime | primaere Realitaetsquellen |
| Externe Agenten | Review, Vorschlag, Gegenposition, keine Mutationshoheit |

## Reifekriterien

1. Policy-Datei `policy/cabinet-maintenance-radar.json` ist maschinenpruefbar.
2. CI prueft Policy und Non-Effects.
3. Erste Findings bleiben report-only.
4. Handoff an Bureau bleibt proposal-only und reviewpflichtig.
5. Heimlern-Output bleibt proposal-only und braucht Review.
6. Externe Dump-Artefakte werden nur konsumiert, nicht in Cabinet erzeugt.

## Epistemische Leerstellen

- Pfade, Frequenz und Manifestform der externen RepoBrief-/Lenskit-Erzeugung fehlen noch.
- Das aktuelle Heimlern-Contract-Repair ist noch nicht als abgeschlossen vorauszusetzen.
- Eine semantische Wahrheitspruefung bleibt ohne Primaerquellenzugriff unvollstaendig.
- Fuer Gemini fehlt weiterhin ein konkreter Ausfuehrungsweg mit Version/Pin, Auth-Modell, Permission-Manifest, Kosten-/Quota-Klasse und Log-Privacy-Grenze.
