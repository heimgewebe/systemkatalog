# Cabinet Role Boundary v1

Status: draft
Datum: 2026-07-09
Owner: Cabinet

## Entscheidung

Cabinet bleibt die semantische Evidenz- und Priorisierungsschicht fuer das Heimgewebe-Oekosystem.

Cabinet wird nicht durch ein einzelnes anderes Programm ersetzt. Stattdessen wird Cabinet enger geschnitten und von spezialisierten Organen flankiert:

- Bureau fuer Aufgaben, Taktung, Kandidaten, Receipts und Handoff-Status.
- Grabowski fuer lokale und repo-bezogene Ausfuehrung nach Task- oder Operatorfreigabe.
- RepoBrief / Lenskit fuer extern erzeugte, zitierfaehige Kontext- und Dump-Artefakte.
- Leitstand oder Schauwerk fuer Live-Anzeige, Visualisierung und Operator-Oberflaeche.
- GitHub, CI und Runtime fuer harte Primaerrealitaet.

## These

Cabinet ist geeignet, wenn Ziel, Relevanz und Risiko so gewichtet werden:

- Ziel: Widersprueche, Belege, Quellenordnung und Prioritaeten sichtbar halten.
- Relevanz: repo- und organuebergreifende Bedeutung wichtiger nehmen als UI-Komfort.
- Risiko: falsche Autoritaet, Schatten-Orchestrierung und unbewiesene Claims verhindern.

## Antithese

Andere Programme sind praktischer, wenn die Aufgabe anders gewichtet wird:

| Gewichtung | Praktischeres Werkzeug | Grund |
|---|---|---|
| Aufgabensteuerung | Bureau, GitHub Projects oder Linear | bessere Queue-, Status- und Board-Flaeche |
| Live-Betrieb | Leitstand, Grafana oder Backstage | bessere Anzeige fuer Dienste, Health und Ownership |
| Notizen und Denknetz | Obsidian | schnellere lokale Markdown- und Graph-Arbeit |
| Team-Wiki | Notion oder Confluence | weniger Reibung fuer manuelle Pflege |
| Servicekatalog | Backstage | fertige Softwarekatalog- und Ownership-Flaeche |

Diese Werkzeuge ersetzen Cabinet nicht automatisch, weil sie die Cabinet-Rolle nicht als Beleg-, Wahrheitsgrenzen- und Organtrennungsmodell abdecken.

## Synthese

Cabinet bleibt Canon fuer:

- Sinn und Begriffsordnung.
- Evidenz- und Claim-Oberflaeche.
- Priorisierung und Entscheidungsgrundlagen.
- Karten-Semantik.
- read-only Kohärenzradar.
- Maintenance-Befunde und proposal-only Handoff-Kandidaten.
- Lernrueckkopplung als reviewed proposal.

Cabinet ist nicht:

- Aufgabenqueue.
- Scheduler.
- Operator.
- Merge-, Push- oder Runtime-Werkzeug.
- Live-Dashboard.
- Primaerquelle fuer GitHub-, CI-, Runtime- oder Service-Wahrheit.
- RepoBrief- oder Lenskit-Dump-Produzent.
- alleiniger Servicekatalog.

## Default-Routing

| Anspruch | Primaeres Organ | Cabinet-Aufgabe |
|---|---|---|
| Was ist als Naechstes dran? | Bureau | Kandidaten und Belege liefern |
| Soll ein PR gemergt werden? | GitHub, CI, Review-Gates, Mensch | Readiness-Claims pruefen, nicht freigeben |
| Soll etwas im Repo geaendert werden? | Grabowski | Kontext, Risiko und Quellenordnung liefern |
| Ist ein Dienst live gesund? | Runtime, systemd, Logs, Healthchecks, Leitstand | Runtime-Claims gegen Primaerquellen markieren |
| Welche Repos/Dienste gibt es? | GitHub, Registry, spaeter Servicekatalog | Semantische Karte und Driftbefunde pflegen |
| Welche Dumps sind nutzbar? | RepoBrief / Lenskit | Provenienz, Frische und Beleggrenzen pruefen |
| Was wurde gelernt? | Heimlern nach Review | Outcome-Artefakte und Vorschlaege einordnen |

## Werkzeugentscheidung

Ein externes Werkzeug wird ergaenzend genutzt, wenn mindestens eine Bedingung zutrifft:

1. Es verbessert Anzeige oder Bedienung ohne neue Autoritaet.
2. Es konsumiert Cabinet-Artefakte read-only.
3. Es hat eine klar getrennte Primaerquelle.
4. Es erzeugt Belege, die Cabinet pruefen kann.
5. Es reduziert manuelle Reibung ohne Queue-, Merge-, Push- oder Runtimewirkung aus Cabinet heraus.

Ein externes Werkzeug ersetzt Cabinet erst, wenn alle Bedingungen zutreffen:

1. Es kann Claims, Evidenz, Verfallsdaten, Primaerquellen und Organrollen versioniert abbilden.
2. Es respektiert die Trennung zwischen Radar, Queue, Operator, Runtime und Freigabe.
3. Es ist fuer lokale/private Quellen kontrollierbar.
4. Es kann Drift und Nicht-Claims maschinenpruefbar ausdruecken.
5. Es verbessert das System ohne neue Schattenautoritaet.

Aktueller Entscheid: keine Ersetzung.

## Grenzen

Cabinet darf Findings und Handoff-Kandidaten erzeugen. Diese bleiben proposal-only, bis Bureau oder ein separates Review-Gate sie hebt.

Cabinet darf keine Aufgaben selbst erstellen, keine Queue mutieren, keine Grabowski-Delegation ausloesen, keine PRs mergen, keine Runtime veraendern und keine Policy-Gewichte direkt anwenden.

## Reifesignale fuer spaetere Spezialwerkzeuge

### Leitstand / Schauwerk

Sinnvoll, wenn Live-Status, Kartenansicht und Operator-Oberflaeche mehr Nutzen bringen als Markdown-Ansichten.

Bedingung: Anzeige bleibt Consumer. Cabinet bleibt Canon fuer Karten-Semantik.

### Backstage

Sinnvoll, wenn mehrere Dienste stabile Ownership-, Lifecycle-, API- und Runbook-Metadaten brauchen.

Bedingung: Backstage wird Servicekatalog und UI, nicht Wahrheitsersatz fuer Cabinet-Claims.

### GitHub Projects / Linear

Sinnvoll, wenn Bureau-Status menschlich komfortabler angezeigt oder mit PRs verknuepft werden soll.

Bedingung: Bureau bleibt Task- und Receipt-Canon.

### Obsidian

Sinnvoll fuer Lern- und Denknotizen.

Bedingung: Obsidian bleibt Arbeitsflaeche, nicht Repo-Canon.

## Nicht-Claims

Diese Entscheidung beweist nicht:

- Cabinet ist vollstaendig implementiert.
- Cabinet ist live eingelesen.
- Bureau-Handoff ist produktiv aktiviert.
- Leitstand ist live.
- Backstage, Notion, Obsidian, Linear oder GitHub Projects sind evaluiert und freigegeben.
- Aktuelle PRs sind mergebar.
- Runtime-Zustand ist gesund.

## Umsetzungsumfang dieser Scheibe

- Policy um die Rollenentscheidung erweitert.
- Entrée, Agent Entry und Cabinet Home auf diese Entscheidung verlinkt.
- Keine Runtime-, Queue- oder Dispatch-Wirkung eingebaut.
