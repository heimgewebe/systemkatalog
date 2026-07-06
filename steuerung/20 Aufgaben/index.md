# Aufgaben

Priorisierte Arbeit mit Scope, Risiko, Stop-Kriterium und Target-Proof.

## Arbeitsregel

Cabinet hält Aufgaben als Steuerungsobjekte. Eine Aufgabe ist noch keine Ausführungserlaubnis, kein Merge-Recht und kein Bureau-Dispatch.

- Bestand liefert Repository-, Projekt- und Quellenkontext.
- Prüfung liefert Befunde, Widersprüche, Evidence und Risiko.
- Steuerung priorisiert, entscheidet und übergibt Aufgaben.
- Bureau erhält nur freigegebene, eng begrenzte Ausführungskandidaten.

## Lage vom 2026-07-05

Quelle: GitHub-PR-Liste und `origin/main` nach Merge `2ccd62b83a69ffc311efa8132741a83c1b994542`, erhoben 2026-07-05T16:45+02:00.

- Offene GitHub-PRs: 0.
- Letzte CAB-QA-Merges: #70 Cabinet Maintenance Radar, #71 Maintenance Report Contract, #73 Maintenance Report CI, #72 External-Dump-Quellenvertrag.
- Main-Checks fuer `2ccd62b83a69ffc311efa8132741a83c1b994542`: gruen.
- CAB-STE-001 und CAB-STE-002 verweisen auf alte Draft-PRs und sind nicht mehr die aktuelle naechste Aktion.
- Der aktuelle offene CAB-QA-Punkt ist nicht Code-Ausbau, sondern die Beobachtung externer RepoBrief-/Lenskit-Manifestreferenzen.

## Priorisierte Cabinet-Verbesserungstasks

| ID | Titel | Organführung | Warum jetzt | Scope | Risiko | Stop-Kriterium | Target-Proof |
|---|---|---|---|---|---|---|---|
| CAB-STE-001 | Draft-PR-Triage #15 | Prüfung -> Steuerung | Evidence-Policy kann Project Cards belastbarer machen. | PR #15 gegen main prüfen: Diff, CI, Reviews, Verhältnis zu Project-Card-v1. | Mittel: Policy kann Scheinsicherheit erzeugen. | Draft bleibt unklar, CI rot oder Autorität widersprüchlich. | Review-Befund mit Entscheidung merge, revise, supersede oder close. |
| CAB-STE-002 | Draft-PR-Triage #14 | Prüfung -> Steuerung | Cards3 ist als Titel zu unklar. | PR #14 semantisch zerlegen: Zweck, Dateien, Konflikte, Verhältnis zu #15. | Mittel: Card-Modell und Evidence-Policy können vermischt werden. | Zweck nicht rekonstruierbar oder Konflikt mit aktueller Card-Policy. | Review-Befund mit Empfehlung schließen, splitten, rebasen oder fortführen. |
| CAB-STE-003 | Project-Card-Evidence abschließen | Bestand -> Prüfung | Projektkarten existieren; Aussagegrenzen müssen prüfbar bleiben. | Bestehende Projektkarten gegen Project-Card-v1 und Provenienzprüfung prüfen. | Mittel: Current-Claims aus alten Quellen wären gefährlich. | Fehlende Quellen oder nicht reproduzierbare Checks. | PROJECT-CARD-GUARD: PASS und Provenienzcheck-PASS oder dokumentierte Blocker. |
| CAB-STE-004 | Ecosystem-Graph auswertbar machen | Prüfung -> Steuerung | Graph-Datei existiert; Nutzen entsteht erst durch Lage- und Taskableitung. | ecosystem-graph.json gegen Blueprint prüfen; minimale Lageableitung definieren. | Niedrig bis mittel: Graph kann als Wahrheit missverstanden werden. | Graph enthält unbelegte Current- oder Runtime-Claims. | Befund mit belegt/plausibel/spekulativ und nächster Aktion. |
| CAB-STE-005 | Repository-Observer manuell replizieren | Bestand -> Prüfung | Live-Sammler erst nach manueller Reproduzierbarkeit automatisieren. | Observer lokal read-only auf freigegebene Repos anwenden, ohne Dispatch oder Mutation. | Mittel: Freshness-Claims können überschätzt werden. | Netzwerk-, Auth- oder Redaktionsgrenze unklar. | Datierter Lauf in pruefung/10 Laeufe plus Quellenhinweis in bestand/30 Quellen. |
| CAB-STE-006 | Bureau-Export-Kandidat schneiden | Steuerung -> Bureau | Cabinet soll geprüfte Kandidaten übergeben, nicht selbst ausführen. | Einen validierbaren read-only Cabinet-Task für Bureau formulieren. | Niedrig: falsche Delegation wäre Prozessdrift. | Task erzeugt Queue-, Dispatch- oder Registry-Effekt. | bureau cabinet-validate-task --json PASS oder dokumentierte Leerstelle. |
| CAB-STE-007 | Alte Raumrollen klassifizieren | Bestand -> Steuerung | Legacy-Räume bleiben lesbar, sollen aber keine aktive Top-Level-Raumrolle tragen. | Inhalte dateiweise als keep, move, split, archive oder delete klassifizieren. | Mittel: Massenverschiebung zerstört Kontext. | Keine Einzelklassifikation oder fehlender Zielraum. | Klassifikationsregister unter docs/migrations mit Prüfung. |
| CAB-QA-001 | Cabinet-Kohaerenzradar v1 | Cabinet -> Bureau | Cabinet soll externe Dumps konsumieren und pruefen, nicht erzeugen. | Maintenance-Report-Contract, deterministischen read-only Scan und Bureau-Kandidat registrieren. | Mittel: Report kann als Freigabe missverstanden werden. | Report erzeugt Task-, Dispatch-, Runtime-, Cleanup- oder Dump-Wirkung. | `python3 scripts/write_cabinet_maintenance_report.py --check` und Unit-Test PASS. |
| CAB-QA-002 | Cabinet Maintenance Report CI | Cabinet | CAB-QA-001 erzeugt einen Report, aber ohne CI-Artefakt bleibt er manuell. | Radar-Workflow fuehrt Report-Tests, Check, JSON-Build, Summary und Artefakt-Upload aus. | Mittel: Report-Artefakt kann als Freigabe missverstanden werden. | Report-CI erzeugt Task-, Dispatch-, Runtime-, Cleanup- oder Dump-Wirkung. | Cabinet-Maintenance-Radar-Workflow PASS und Report-Artefakt ist JSON-validiert. |
| CAB-QA-003 | External-Dump-Quellenvertrag v1 | Cabinet -> RepoBrief/Lenskit -> Bureau | CAB-QA-001 meldete fehlende externe Dump-Spezifikation. | Registry, Contract, Validator und Report-Anbindung fuer externe RepoBrief-/Lenskit-Manifeste. | Mittel: ein fehlendes Manifest darf nicht als Runtime-Fehler gelten. | Cabinet erzeugt Dumps oder leitet Autoritaet aus Dump-Freshness ab. | External-Dump-Validator PASS und Maintenance-Report zeigt keine Spezifikationsluecke mehr. |
| CAB-QA-004 | Externe Manifestreferenzen beobachten | Cabinet -> RepoBrief/Lenskit | Der Maintenance Report meldet keine Spezifikationsluecke mehr, aber zwei unobserved Manifestquellen. | Externe Manifestorte pruefen und Registry nur mit belegten relativen Manifestpfaden aktualisieren; sonst Leerstelle dokumentieren. | Mittel: Freshness kann mit Wahrheit verwechselt werden. | Kein aktuelles Manifest belegbar oder Pfad passt nicht zum Contract. | External-Dump-Validator PASS und Maintenance-Report reduziert manifest-unobserved-Findings oder dokumentiert die Leerstelle. |
| CAB-QA-005 | Read-only Ecosystem Signal Ingest | Cabinet | Cabinet braucht eine belegte Wahrnehmungsschicht, ohne daraus operative Wirkung abzuleiten. | Contract, Schema, Validator, Fixture, Tests und Claim-Kandidat fuer read-only Ecosystem-Signale. | Mittel: Signale koennen als Task-, Merge- oder Dispatch-Recht missverstanden werden. | Signal erzeugt Bureau-Import, Queue-Mutation, Dispatch, Runtime-Wirkung, Merge-/Push-Recht oder Dump-Erzeugung. | Ecosystem-Signal-Tests PASS, Fixture-Validator PASS und Maintenance-Report-Check PASS. |
| CAB-QA-006 | Live Signal Probe v0 | Cabinet | CAB-QA-005 ist gemergt; der Contract braucht ein erstes echtes Probe-Artefakt. | Ein datiertes read-only Signal-JSONL zu Cabinet PR #75 und Main-CI validieren. | Mittel: ein Signal kann mit Freigabe oder Wahrheit verwechselt werden. | Signal erzeugt Bureau-Import, Queue-Mutation, Dispatch, Runtime-Wirkung, Schreibrecht oder Dump-Erzeugung. | Live-Signal-Validator PASS; Run-Evidence verweist auf konkrete GitHub-Actions-Runs. |

## Nicht tun

- Keine automatische Massenmigration alter Räume.
- Kein Bureau-Dispatch aus Cabinet ohne freigegebenen Task-Kandidaten.
- Keine Current-Claims aus datierten Repository References ableiten.
- Keine Merge-Entscheidung für Draft-PRs ohne Review-Befund und grüne Checks.
- Keine Automatisierung, bevor der manuelle Lauf reproduzierbar ist.

## Nächste Aktion

CAB-QA-004 ist beobachtet: externe RepoBrief-/Lenskit-Manifestreferenzen fuer `cabinet/main` sind registriert. Naechste Aktion: CAB-QA-007 nur als read-only Producer auf Basis dieser Manifestbeobachtung planen.
- [Reference Refresh Contract 2026-07-03](reference-refresh-contract-2026-07-03.md)
- [Bureau Reference Refresh Plan 2026-07-03](bureau-reference-refresh-plan-2026-07-03.md)
- [Bureau Reference Refresh Proposal 2026-07-03](bureau-reference-refresh-proposal-2026-07-03.md)
- [CAB-QA-001 — Cabinet-Kohaerenzradar v1](cab-qa-001-cabinet-coherence-radar.md)
- [CAB-QA-002 — Cabinet Maintenance Report CI](cab-qa-002-maintenance-report-ci.md)
- [CAB-QA-003 — External-Dump-Quellenvertrag v1](cab-qa-003-external-dump-sources-contract.md)
- [CAB-QA-004 — Externe Manifestreferenzen beobachten](cab-qa-004-external-manifest-observation.md)
- [CAB-QA-005 — Read-only Ecosystem Signal Ingest](cab-qa-005-read-only-ecosystem-signal-ingest.md)
- [CAB-QA-006 — Live Signal Probe v0](cab-qa-006-live-signal-probe.md)
