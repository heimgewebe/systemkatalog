# Aufgaben

Priorisierte Arbeit mit Scope, Risiko, Stop-Kriterium und Target-Proof.

## Arbeitsregel

Cabinet hält Aufgaben als Steuerungsobjekte. Eine Aufgabe ist noch keine Ausführungserlaubnis, kein Merge-Recht und kein Bureau-Dispatch.

- Bestand liefert Repository-, Projekt- und Quellenkontext.
- Prüfung liefert Befunde, Widersprüche, Evidence und Risiko.
- Steuerung priorisiert, entscheidet und übergibt Aufgaben.
- Bureau erhält nur freigegebene, eng begrenzte Ausführungskandidaten.

## Lage vom 2026-07-02

Quelle: lokaler main-Checkout und GitHub-PR-Liste, erhoben 2026-07-02T06:36:05+02:00.

- Offene GitHub-Issues: 0.
- Offene Draft-PRs: #14 Cards3, #15 fix: harden card evidence policy.
- Diese Aufgabentafel war vor diesem Slice nur ein Platzhalter.

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

## Nicht tun

- Keine automatische Massenmigration alter Räume.
- Kein Bureau-Dispatch aus Cabinet ohne freigegebenen Task-Kandidaten.
- Keine Current-Claims aus datierten Repository References ableiten.
- Keine Merge-Entscheidung für Draft-PRs ohne Review-Befund und grüne Checks.
- Keine Automatisierung, bevor der manuelle Lauf reproduzierbar ist.

## Nächste Aktion

CAB-STE-001 zuerst: PR #15 prüfen, weil Evidence-Policy die Grundlage für belastbare Project Cards und spätere Taskableitung ist.
- [Reference Refresh Contract 2026-07-03](reference-refresh-contract-2026-07-03.md)
- [Bureau Reference Refresh Plan 2026-07-03](bureau-reference-refresh-plan-2026-07-03.md)
- [Bureau Reference Refresh Proposal 2026-07-03](bureau-reference-refresh-proposal-2026-07-03.md)
- [CAB-QA-001 — Cabinet-Kohaerenzradar v1](cab-qa-001-cabinet-coherence-radar.md)
