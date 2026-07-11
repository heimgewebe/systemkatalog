# Cabinet Gemini Maintenance Preflight v1

Status: blocked
Datum: 2026-07-08
Bureau-Task: CABINET-GEMINI-MAINT-V1-T001
Repository: heimgewebe/cabinet
Owner: Cabinet

## Ergebnis

Der Gemini-Maintenance-Scan ist **nicht freigegeben** und **nicht schedulable**.

Der Preflight kann derzeit keine read-only Sandbox beweisen, weil kein konkreter Gemini-Ausfuehrungsweg mit Version, Pin, Auth-Modell, Rechteumfang, Logging-Grenze und Kosten-/Quota-Klasse vorliegt.

Damit ist der sichere Zustand: blockieren, nicht planen, keine wiederkehrende Ausfuehrung einrichten.

## Gepruefte Lage

### Belegt

- `AGENTS.md` fuehrt Gemini nur als vorgeschlagene proposal-only Review-/Scout-Kapazitaet nach Capability- und Sandbox-Preflight. Es nennt ausdruecklich: nicht verifiziert, nicht schedulable, keine Push-, Merge-, Runtime- oder private-Kontext-Autoritaet.
- `README.md` wiederholt, dass Gemini vor Capability-/Sandbox-Preflight nicht schedulable ist.
- `docs/blueprints/cabinet-maintenance-radar-v0.md` definiert Cabinet als read-only Kohaerenzradar. Cabinet erzeugt Befunde und Vorschlaege, aber keine operativen Wirkungen.
- Bureau hat `CABINET-GEMINI-MAINT-V1-T001` als naechste Preflight-Aufgabe registriert.

### Plausibel

- Gemini kann als semantischer Zweitleser nuetzlich sein, wenn es nur ein kuratiertes Evidence-Paket liest und keine Repo-, Issue-, PR-, Dispatch-, Queue-, Merge- oder Runtime-Rechte erhaelt.
- Der Nutzen liegt eher bei Widerspruchs-, Ueberclaiming- und Semantikpruefung als bei deterministischen Checks. JSON, Schemas, Links, Hashes, Pfade und Freshness muessen weiterhin deterministisch geprueft werden.

### Spekulativ

- Ob Gemini in der vorhandenen Umgebung ueberhaupt verfuegbar ist.
- Ob ein verwendbarer Tool-Pin, ein sicheres Auth-Modell und eine belastbare Kosten-/Quota-Grenze existieren.
- Ob Gemini-Ausgaben ausreichend belegt, reproduzierbar und rauscharm sind.

## Akzeptanzkriterien gegen T001

| Kriterium | Befund | Status |
|---|---|---|
| exaktes Gemini-Tool, Version oder Pin, Auth-Modus, Secret Boundary dokumentiert | Fehlt. Kein konkreter Ausfuehrungsweg bekannt. | blocked |
| read-only Operation ohne Issue/PR/Contents-Write/Dispatch/Merge/Runtime/Queue-Mutation bewiesen | Nicht beweisbar ohne konkreten Tool- und Permission-Manifest. | blocked |
| bounded Markdown plus JSON Output geprueft | Nicht geprueft. Kein Dry Run ausgefuehrt. | blocked |
| Kosten-/Quota-Klasse und Log-Privacy-Risiken dokumentiert | Fehlt. | blocked |

## No-Effect Boundary

Dieser Preflight erlaubt nicht:

- Gemini-Ausfuehrung gegen ein unkuratiertes Repository
- Scheduling oder Recurrence
- GitHub Issue-/PR-/Comment-Erstellung durch Gemini
- Contents-Write durch Gemini
- Bureau-Task-Erzeugung oder Queue-Mutation durch Gemini
- Grabowski-Dispatch durch Gemini
- Push, Merge, Deploy, Cleanup oder Runtime-Aktion durch Gemini
- Nutzung privater Logs, Secrets oder `.agents`-Runtime-Inhalte

## Minimaler sicherer Zielpfad

1. Tool- und Auth-Entscheidung separat dokumentieren:
   - Anbieter/Tool
   - Version oder Action-Pin
   - Auth-Modell
   - konkrete GitHub Permissions
   - Secret-Quelle ohne Secret-Wert
   - Logging-Ort und Retention
   - Kosten-/Quota-Klasse
2. Nur kuratiertes Evidence-Paket erlauben, keinen freien Repo-Crawl.
3. Output-Contract definieren:
   - Markdown Summary
   - JSON Finding Array
   - `observed`, `plausible`, `speculative` getrennt
   - Evidence-Refs fuer alle observed Claims
   - `effects` Objekt mit allen Effektflags `false`
4. Erst danach einen manuellen Dry Run als Artefakt erzeugen.
5. Erst nach Review des Dry Runs ueber Scheduling entscheiden.

## Entscheidung

T001 ist fachlich ausgefuehrt als **Blocker-Preflight**: Ohne konkreten Gemini-Ausfuehrungsweg darf keine geplante oder automatische Gemini-Maintenance-Lane eingerichtet werden.

## Does not establish

- Gemini availability
- Gemini schedulability
- Gemini scan quality
- task approval
- claim truth
- merge readiness
- runtime correctness
- autonomous dispatch
