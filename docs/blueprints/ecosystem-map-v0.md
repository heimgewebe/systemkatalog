# Ecosystem Map v0

Status: draft
Datum: 2026-07-04
Owner: Cabinet
Lokaler Pflegeort: `/home/alex/repos/cabinet`

## Entscheidung

Die Heimgewebe-Oekosystemkarte wird in v0 im Cabinet-Repo gepflegt, nicht in einem eigenen Repository.

Das eigene Repo bleibt eine spaetere Option, wenn die Karte selbst produktive Schnittstellen, eigene CI, mehrere aktive Consumer oder eine klare Produktgrenze bekommt.

## Zweck

Die Karte ist kein Poster. Sie ist ein kleiner, maschinenlesbarer Betriebsgraph fuer Orientierung, Scope-Klaerung und Widerspruchspflege.

Sie beantwortet:

- Welche Organe gibt es?
- Welche Rolle hat jedes Organ?
- Welche Beziehungen sind belegt, geplant oder nur plausibel?
- Welche Aussagen sind Entscheidung, Beobachtung, Evidenz oder Spekulation?
- Welche Realitaetsquelle bleibt fuer welche Wahrheit primaer?

## Wahrheitsgrenzen

Cabinet besitzt in v0 die Semantik der Karte, aber nicht die Wahrheit aller Quellen.

Primaere Quellen bleiben:

- GitHub fuer Branches, Pull Requests, Issues und Reviews.
- CI und Review-Gates fuer technische Pruefsignale.
- Runtime, systemd, Logs und Healthchecks fuer laufende Dienste.
- Contracts, Schemas und Tests fuer maschinenpruefbare Invarianten.
- Menschliche Entscheidungen fuer Prioritaet, Freigabe und Abbruch.

Die Karte darf diese Quellen verknuepfen. Sie darf sie nicht ersetzen.

## Dateien

```text
registry/ecosystem/nodes.json       # Organe, Repos, Services, Agenten, Artefakte
registry/ecosystem/edges.json       # Beziehungen zwischen Knoten
registry/ecosystem/claims.jsonl     # Aussagen mit Status, Konfidenz und Ablaufdatum
rendered/ecosystem-map.mmd                # lesbare Uebersichtskarte; Einstieg, kein Canon
rendered/ecosystem-registry-map.mmd       # generierte Registry-Projektion aus Knoten und Kanten
scripts/validate_ecosystem_map.py         # minimaler Konsistenzcheck
scripts/render_ecosystem_registry_map.py  # Generator und Drift-Check der Registry-Projektion
```

## Ansichten

`rendered/ecosystem-map.mmd` ist die menschlich kuratierte Uebersicht. Sie darf Knoten buendeln und Beziehungen vereinfachen, aber daraus folgt keine Beweiskraft.

`rendered/ecosystem-registry-map.mmd` ist die deterministische Projektion aus `nodes.json` und `edges.json`. Sie ist fuer Driftpruefung nuetzlicher, aber nicht automatisch besser lesbar.

Wahrheit liegt weder in der Uebersicht noch in der Projektion. Die Registry ist der versionierte Karteninput; primaere Quellen bleiben GitHub, CI, Runtime, Contracts und menschliche Entscheidungen.

## Pflegeprinzipien

1. Kein Edge ohne existierenden Knoten.
2. Kein Claim ohne Status und Ablaufdatum.
3. Scores und Konfidenzen sind Hinweise, keine Wahrheit.
4. Widersprueche duerfen sichtbar bleiben.
5. Bureau darf nur freigegebene oder validierte Kandidaten operativ nutzen.
6. Schauwerk darf rendern, aber nicht die Karte kanonisieren.
7. Die Uebersichtskarte darf vereinfachen, muss aber als Uebersicht erkennbar bleiben.
8. Die Registry-Projektion muss per `scripts/render_ecosystem_registry_map.py --check` aktuell bleiben.
9. Ein eigenes Repo wird erst nach expliziter Reifeentscheidung eroeffnet.

## Reifekriterien fuer ein eigenes Repo

Ein eigenes Repository wie `heimgewebe/ecosystem-map` oder `heimgewebe/heimatlas` wird erst sinnvoll, wenn mindestens drei Bedingungen erfuellt sind:

- mehrere Repos konsumieren die Karte automatisiert;
- die Karte hat eigene CI-Schemas, Exporte oder Generatoren;
- Cabinet, Bureau, Grabowski und Schauwerk nutzen denselben Graphen produktiv;
- die Karte enthaelt repo-uebergreifende Vertraege statt nur Orientierung;
- Cabinet wird durch Map-Daten semantisch ueberladen;
- es gibt einen klaren Render-, API- oder Produktbedarf.

## Naechster Slice

v0 bleibt klein:

- Knoten erfassen.
- Kanten erfassen.
- Claims mit Verfallsdatum erfassen.
- Konsistenz pruefen.
- Registry-Projektion pruefbar halten.
- Keine Autonomie daraus ableiten.
