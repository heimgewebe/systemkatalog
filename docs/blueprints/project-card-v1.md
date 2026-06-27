# Project Card v1

## Zweck

Eine Project Card bündelt ein repoübergreifendes Vorhaben als belegte Navigations- und Arbeitsfläche. Sie beschreibt Ziel, Repositorybeziehungen, belegten Stand, Blocker, Risiken und nächste Aktion. Sie ersetzt weder die Quell-Repositories noch aktuelle Git-, CI- oder Runtime-Belege.

## Ablage

- Karten liegen direkt unter `bestand/20 Projekte/`.
- `index.md` verlinkt jede Karte genau einmal.
- Der Dateiname entspricht der Karten-ID: `<id>.md`.
- Andere Dateien oder Unterverzeichnisse sind in diesem Ordner nicht zulässig.

## Maschinenlesbarer Kopf

Jede Karte enthält genau einen Block dieser Form:

```text
<!-- cabinet-project-card-v1
{
  "schema": "cabinet.project-card.v1",
  "id": "beispiel",
  "title": "Beispiel",
  "evidence_status": "partial",
  "reviewed_at": "2026-06-27",
  "repositories": [
    {
      "name": "example-repo",
      "role": "Belegte Rolle im Vorhaben",
      "evidence": "pfad/zur/Quelle.md",
      "reference": "pfad/Repository Reference.md"
    }
  ],
  "sources": [
    "pfad/zur/Quelle.md",
    "pfad/Repository Reference.md"
  ]
}
-->
```

`reference` ist optional. Wenn es vorhanden ist, verweist es auf eine reguläre `Repository Reference.md` und muss zugleich in `sources` stehen.

## Evidenzstatus

Der Evidenzstatus beschreibt ausschließlich die Beleglage der Karte, nicht den Lebenszyklus des Projekts.

- `partial`: Beziehungen oder Repository References fehlen noch.
- `bounded`: Alle aufgelisteten Beziehungen sind belegt; Aktualität und Runtime bleiben ausdrücklich begrenzt.
- `current`: Für eine spätere Vertragsfassung reserviert. Project Card v1 weist diesen Wert ab, weil noch kein Feld für einen freigegebenen Sammlerlauf existiert.

Project Card v1 erzeugt selbst keinen aktuellen Zustand. Zulässig sind deshalb nur `partial` und `bounded`.

## Pflichtabschnitte

Jede Karte enthält genau einmal und mit Inhalt:

1. `## Ziel`
2. `## Repositorybeziehungen`
3. `## Belegter Stand`
4. `## Blocker und Risiken`
5. `## Nächste Aktion`
6. `## Quellen`

## Aussagegrenze

- Jede Repositorybeziehung verweist auf eine versionierte Quelle.
- Jede Quelle aus dem Maschinenkopf erscheint auch im sichtbaren Abschnitt `## Quellen`.
- Ein Name in einer Legacy-Quelle beweist keine aktuelle Existenz, Erreichbarkeit oder Aktivität des Repositories.
- Eine Repository Reference beweist nur den in ihr datierten Snapshot und die darin belegte Rolle.
- Fehlende Repository References werden als Blocker genannt, nicht still ergänzt.
- Karten dürfen keine aktuellen Branch-, CI-, Runtime- oder Deploymentaussagen aus alten Quellen ableiten.
- Entscheidungen und Aufträge bleiben Aufgabe von `steuerung`.

## Prüfung

```bash
python3 scripts/check-project-cards.py .
python3 scripts/check-project-card-provenance.py .
python3 -m unittest discover -s scripts/tests -p 'test_project_card*.py'
```

Erwartete Abschlüsse:

```text
PROJECT-CARD-GUARD: PASS
PROJECT-CARD-PROVENANCE: PASS
```
