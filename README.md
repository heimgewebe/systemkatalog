# Cabinet — Heimgewebe-Systemkatalog

Cabinet beschreibt die Systeme des Heimgewebe-Ökosystems, ihre Zwecke, Wahrheitszuständigkeiten, stabilen Beziehungen und Einstiegspunkte.

Die externe Cabinet AI Workspace App ist außer Betrieb. Der aktive lokale Viewer ist ein kleiner, read-only Heimgewebe-Systemkatalog ohne Node, Next, KI-Agent, Daemon, Datenbank oder Secret-Konfiguration.

## Schnellstart

1. **Lokalen Systemkatalog öffnen:** `http://127.0.0.1:4001/`
2. **Lesbare Repositoryprojektion öffnen:** [rendered/system-catalog.md](rendered/system-catalog.md)
3. **Agentenregeln lesen:** [AGENTS.md](AGENTS.md)
4. **Maschinenlesbare Rollenpolicy lesen:** [policy/system-catalog.v1.json](policy/system-catalog.v1.json)
5. **Wahrheitszuständigkeiten prüfen:** [registry/ecosystem/authority-matrix.v1.json](registry/ecosystem/authority-matrix.v1.json)
6. **Stabile Katalogregistry prüfen:** [Knoten](registry/ecosystem/nodes.json) und [Beziehungen](registry/ecosystem/edges.json)
7. **Migrationsmatrix lesen:** [docs/migration/cabinet-surface-matrix-v1.md](docs/migration/cabinet-surface-matrix-v1.md)
8. **Abgeschlossenen Runtime-Cutover nachvollziehen:** [T013-Preflight](docs/migration/cabinet-runtime-retirement-preflight-v1.json) und [Cutover-/Rollbackbeleg](docs/migration/cabinet-runtime-retirement-authorization-v1.md)
9. **Katalogschema ansehen:** [Schema](catalog/system-catalog.schema.v1.json) und [nichtkanonisches Beispiel](catalog/system-catalog.example.v1.json)

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

Der Katalogkanon benötigt keinen Server. Für die lokale Leseoberfläche läuft `heimgewebe-systemkatalog.service`: ein zustandsloser Python-HTTP-Dienst auf Loopback. `cabinet.service` ist nur noch dessen Kompatibilitätsalias.

## Runtime und Migration

Der aktive Dienst liefert den Katalog ausschließlich lesend aus. Seine Inhalte werden bei jedem Request aus den versionierten kanonischen Eingaben zusammengesetzt. Der frühere Node-/Next-App- und Daemon-Unterbau wurde aus dem aktiven Repository- und Dienstvertrag entfernt. Private Altbestände bleiben außerhalb des Katalogkanons als Rückfall- und Archivmaterial erhalten.

Bedienung:

```bash
systemkatalogctl status
systemkatalogctl url
systemkatalogctl restart
```

Die geplante Zielidentität des Repositories bleibt `heimgewebe/heimgewebe-katalog`; die Umbenennung ist ein eigener Referenzmigrationsschritt.

## Nicht verwechseln

- Der lesbare Katalog ist eine Projektion, keine Live- oder Merge-Wahrheit.
- Mermaidkarten sind Orientierung, kein Wahrheitsbeweis.
- Das öffentliche Consumer-Usage-Artefakt enthält nur redaktierte Aggregataussagen; Runtime-Details bleiben privat.
- Die externe Cabinet-App ist retired und kein aktiver Runtime-Unterbau.
- Ein wiederkehrender Gemini-Maintenance-Scout wird nicht eingerichtet.
