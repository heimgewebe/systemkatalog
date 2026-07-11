# Cabinet-Bureau Bridge v0

Status: draft
Datum: 2026-07-04
Owner: Cabinet
Target organ: Bureau

## Entscheidung

Cabinet darf Bureau Kandidaten anbieten. Bureau darf diese Kandidaten nur read-only als Eingangssignal lesen.

Die Bridge erzeugt keine Bureau-Aufgabe automatisch, startet keinen Grabowski-Lauf und veraendert keine Runtime.

## Zweck

Die Bridge trennt drei Dinge, die leicht verwechselt werden:

1. Cabinet erkennt Sinn, Evidenz und Prioritaet.
2. Bureau fuehrt Kadenz, Aufgabenstatus und Receipts.
3. Grabowski fuehrt konkrete Repo- und Review-Arbeit aus.

Der kleinste sichere Uebergang ist deshalb kein Autopilot, sondern ein Kandidatenvertrag.

## Zulassung

Ein Cabinet-Kandidat ist fuer Bureau zulaessig, wenn alle Bedingungen erfuellt sind:

- Der Kandidat hat eine eindeutige ID.
- Der Kandidat hat einen Status aus `evidenced`, `approved` oder `draft_decision` mit expliziter menschlicher Freigabe.
- Der Kandidat nennt mindestens eine Evidenzquelle.
- Der Kandidat hat ein Ablaufdatum oder einen Refresh-Hinweis.
- Der Kandidat beschreibt eine naechste Aktion, nicht nur einen Wunsch.
- Der Kandidat nennt, welches Organ primär zustaendig ist.

Abgelaufene, spekulative oder widerspruechliche Kandidaten duerfen nicht direkt operativ werden. Sie koennen nur als Refresh- oder Klaerungsaufgabe erscheinen.

## Organrollen

| Organ | Rolle in der Bridge |
|---|---|
| Cabinet | Owner der Semantik, Prioritaet und Kandidatenbewertung |
| Bureau | Read-only Konsument und spaetere Aufgaben-/Receipt-Kadenz |
| Grabowski | Ausfuehrung erst nach Bureau- oder expliziter Operator-Freigabe |
| RepoBrief | Zitierfaehiger Kontext und Snapshot-Grenze |
| Steuerboard | Read-only Repo-State-Signal, kein Gate |
| Chronik | Ereigniskontinuitaet und historische Spur |
| GitHub/CI | Primaere Wahrheit fuer PR-, Branch- und Check-Zustand |
| Schauwerk | Darstellung, nicht Kanon |
| Externe Agenten | Vorschlag und Review, nicht Autoritaet |

## Prohibited path

Die Bridge verbietet:

- automatische Bureau-Task-Erzeugung aus jedem Claim;
- automatische Grabowski-Delegation;
- Merge-, Push-, Runtime- oder Cleanup-Aktionen;
- Behandlung der Map als Wahrheit fuer fremde Repos;
- Uebernahme von Spekulation als Prioritaet.

## Minimaler Ablauf

1. Cabinet markiert einen Kandidaten.
2. RepoBrief oder direkte Quellen liefern zitierfaehigen Kontext.
3. Bureau liest nur den Kandidatenkopf: ID, Status, Evidenz, Ablauf, naechste Aktion, Organ.
4. Bureau entscheidet, ob daraus ein Task-Kandidat wird.
5. Grabowski handelt erst nach Task-/Operator-Freigabe und Review-Gate.

## v0-Grenze

Diese Datei ist ein Vertrag fuer die Richtung, nicht die Implementierung eines Imports. Bureau wird in diesem Slice nicht geaendert.

## Naechster Slice

BRIDGE-001: maschinenlesbare Bridge-Policy in Cabinet, danach ein Bureau-Read-Probe nur, wenn Bureau eine passende Task- oder Frontier-Struktur besitzt.
