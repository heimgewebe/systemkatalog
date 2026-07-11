# Cabinet — Heimgewebe-Systemkatalog

Cabinet beschreibt die Systeme des Heimgewebe-Ökosystems, ihre Zwecke, Wahrheitszuständigkeiten, stabilen Beziehungen und Einstiegspunkte.

Das Repository befindet sich in einer kontrollierten Migration weg von der externen Cabinet AI Workspace App. Die App ist nur noch ein vorübergehender optionaler Viewer; Katalogdaten, Validierung und Rendering funktionieren unabhängig von ihr.

## Schnellstart

1. **Lesbaren Systemkatalog öffnen:** [rendered/system-catalog.md](rendered/system-catalog.md)
2. **Agentenregeln lesen:** [AGENTS.md](AGENTS.md)
3. **Maschinenlesbare Rollenpolicy lesen:** [policy/system-catalog.v1.json](policy/system-catalog.v1.json)
4. **Wahrheitszuständigkeiten prüfen:** [registry/ecosystem/authority-matrix.v1.json](registry/ecosystem/authority-matrix.v1.json)
5. **Stabile Katalogregistry prüfen:** [Knoten](registry/ecosystem/nodes.json) und [Beziehungen](registry/ecosystem/edges.json)
6. **Migrationsmatrix lesen:** [docs/migration/cabinet-surface-matrix-v1.md](docs/migration/cabinet-surface-matrix-v1.md)
7. **Katalogschema ansehen:** [Schema](catalog/system-catalog.schema.v1.json) und [nichtkanonisches Beispiel](catalog/system-catalog.example.v1.json)

## Cabinet beantwortet

- Welche Systeme existieren?
- Was ist ihr Zweck?
- Wofür sind sie ausdrücklich nicht zuständig?
- Wem gehört welche Wahrheit?
- Welche stabilen Beziehungen bestehen?
- Wo liegen die Einstiegspunkte?

## Cabinet beantwortet nicht

- Welche Aufgabe ist als Nächstes dran?
- Welcher Task ist aktiv oder blockiert?
- Ist ein Dienst gesund?
- Ist ein Pull Request mergebereit?
- Welcher Agent soll handeln?
- Welche Priorität oder Taktung gilt gerade?

## Wahrheitsordnung

| Aussage | Primärquelle |
|---|---|
| Aufgaben, Queue, Claims und Receipts | Bureau |
| lokale und repositorybezogene Ausführung | Grabowski |
| Repositories, Branches, Pull Requests und Reviews | GitHub |
| technische Prüfergebnisse | CI und Review-Gates |
| laufender Dienstzustand | Runtime, Healthchecks, systemd und Logs |
| allgemeine Live-Anzeige | Leitstand |
| Repo-Snapshots und zitierfähiger Kontext | RepoBrief / Lenskit |
| stabile Ökosystem-Semantik und Truth Ownership | dieser Systemkatalog |

Cabinet verweist auf die jeweilige Primärquelle. Es kopiert deren wechselnde Zustände nicht in ein zweites Statusmodell.

## Technischer Kern

Der notwendige Unterbau besteht nur aus:

- versionierten Katalog- und Registry-Dateien;
- deterministischen Validatoren;
- deterministischen Renderern;
- CI-Prüfungen gegen Inkonsistenzen und private Runtime-Leaks.

Kein Server, Daemon, Scheduler, KI-Agent oder Datenbankdienst ist für den Katalog erforderlich.

## Migration

Die Katalogkonsolidierung ist bewusst nichtdestruktiv. Bestehende Räume, Radar-, Gemini- und Runtime-Flächen bleiben zunächst lesbar, sind aber Migrations- oder Kompatibilitätsflächen und keine Zielarchitektur. Legacy-Radar und Gemini-Dry-Run sind ausschließlich manuell startbar; sie besitzen keine Katalogautorität. Abschaltung der App, Löschung lokaler Daten und Umbenennung des Repositories benötigen eigene Bureau-Tasks und separate Review-Gates.

Für die vorgelagerte private Datensicherung existiert ein [begrenztes Archiv-, verschlüsseltes Restic-Handoff- und Restore-Verfahren](docs/migration/private-cabinet-archive-v1.md). Seine Dokumentation erteilt keine Ausführungserlaubnis; Werkzeugentwicklung und echter Export benötigen getrennte, zielgebundene Bureau-Autorisierungen.

Die geplante Zielidentität nach abgeschlossener Entkopplung lautet `heimgewebe/heimgewebe-katalog`.

## Nicht verwechseln

- Der lesbare Katalog ist eine Projektion, keine Live- oder Merge-Wahrheit.
- Mermaidkarten sind Orientierung, kein Wahrheitsbeweis.
- Das öffentliche Consumer-Usage-Artefakt enthält nur redaktierte Aggregataussagen; Runtime-Details bleiben privat.
- Die externe Cabinet-App ist weder Canon noch notwendiger Runtime-Unterbau.
- Ein wiederkehrender Gemini-Maintenance-Scout wird nicht eingerichtet.
