# Agent Routing Brief v0

Status: draft
Datum: 2026-07-04

## Zweck

Dieser Brief ist eine Entscheidungsgrundlage fuer die kuenftige Agenten-Nutzung im Cabinet-, Bureau- und Grabowski-Oekosystem.

## These

Die bisherige Regel war zu grob. Externe Modelle sollen nicht pauschal ausgeschlossen werden. Besser ist eine Routing-Regel nach Aufgabe, Datenklasse, Kosten und Nachweis.

## Entscheidungsvorschlag

Cabinet bleibt Sinn- und Entscheidungsschicht. Bureau wird enger angebunden und fuehrt Aufgaben, Kandidaten, Receipts und Laufbelege. Grabowski bleibt die lokale Hand fuer belegte Schritte.

## Agentenrollen

| Agent | Primaere Rolle | Geeignet fuer |
|---|---|---|
| Grabowski | lokale Ausfuehrung | Git, lokale Dateien, Runtime, Receipts |
| ChatGPT Pro / Codex | Umsetzung und Review | Code-Slices, PR-Reviews, Refactoring, Tests |
| Gemini / Google AI Pro | breite Analyse | grosse Kontextvergleiche, Strukturvorschlaege, zweite Meinung |
| Claude | Architektur- und Sicherheitsreview | riskante Diffs, Designkritik, Gegenposition |
| Bureau | Koordination | Aufgaben, Kandidaten, Receipts, Laufstatus |
| Cabinet | Sinnschicht | Bestand, Pruefung, Steuerung, Entscheidungen |

## Neue Leitlinie

Externe Agenten duerfen genutzt werden, wenn der Input zur Aufgabe passt und der Lauf belegbar bleibt. Die alte Pauschalgrenze wird durch eine Routing-Policy ersetzt.

## Routing-Matrix

| Aufgabe | Default | Zweitreview | Nachweis |
|---|---|---|---|
| kleiner Docs-Slice | Grabowski + ChatGPT | optional Gemini | PR + Checks |
| Code-Slice | Codex oder Grabowski | Claude bei Risiko | Diff, Tests, PR |
| Architekturentscheidung | ChatGPT + Cabinet-Brief | Claude und Gemini | Entscheidungsbrief |
| Repo-Status / Drift | Grabowski + Steuerboard | Cabinet | Befund |
| Worktree-Lifecycle | Grabowski typed tools | ChatGPT Review | Preview, Recovery, Apply-Beleg |
| grosse Systemfrage | Cabinet Brief | Gemini + Claude | Synthese und offene Luecken |

## Cabinet und Bureau

Cabinet und Bureau sollten enger verzahnt werden, aber nicht verschmelzen.

- Cabinet beantwortet: Was bedeutet das, was ist belegt, was soll entschieden werden?
- Bureau beantwortet: Welche Aufgabe laeuft, wer oder was hat sie erzeugt, welcher Receipt beweist den Lauf?
- Uebergabe: Cabinet-Befund erzeugt Bureau-Kandidat; Bureau-Receipt wird zur Cabinet-Evidence.

## Kosten- und Kontingentregel

Die vorhandenen Abos sollen genutzt werden. Trotzdem wird kein Anbieter als unlimited behandelt. Coding-Agenten verbrauchen dynamische Kontingente. Jeder Lauf soll knapp nennen, warum genau dieses Modell verwendet wurde.

## Konfiguration v0

1. Externe Agenten sind erlaubt fuer freigegebene Diffs, Repo-Briefe, Review-Prompts und Architekturfragen.
2. Bei komplexen PRs: ChatGPT/Codex Self-Review plus Claude- oder Gemini-Gegenreview.
3. Bei grossen Systemfragen: Cabinet-Brief zuerst, dann externe Reviews.
4. Bei mutierenden Schritten: Grabowski oder Operator-Relay, nie externer Agent direkt.
5. Jede Abweichung von der Default-Route wird im Befund oder PR-Body begruendet.

## Naechster Slice

AGENT-ROUTE-001: Eine formale Routing-Policy als maschinenlesbare Tabelle ergaenzen. Dazu gehoeren Datenklasse, erlaubte Agenten, Freigabe, Nachweis und Stop-Kriterium.
