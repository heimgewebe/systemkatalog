# Systemkatalog

Der Systemkatalog beschreibt die stabilen Bestandteile des Heimgewebe-Ökosystems: vorhandene Systeme, ihren Zweck, ihre Grenzen, Wahrheitszuständigkeiten, dauerhafte Beziehungen und Einstiegspunkte.

Er ist **kein Steuerungs- oder Statussystem**. Aufgaben, Prioritäten, Laufzustände, Pull Requests, Prüfungen und Ausführung bleiben bei den dafür zuständigen Primärsystemen.

## Einstieg

1. [Erzeugte Leseansicht](rendered/system-catalog.md)
2. [Veröffentlichtes Kartenmanifest](rendered/ecosystem-map-artifact-manifest.json)
3. [Katalogpolicy](policy/system-catalog.v1.json)
4. [Systeme](registry/ecosystem/nodes.json)
5. [Stabile Beziehungen](registry/ecosystem/edges.json)
6. [Wahrheitszuständigkeiten](registry/ecosystem/authority-matrix.v1.json)
7. [Agenteneinstieg](AGENTS.md)
8. [Architektur](docs/architecture/systemkatalog.md)
9. [Audit der früheren Cabinet-Räume](docs/audits/systemkatalog-room-audit-v1.md)
10. [Resilienz-Gap-Matrix v1](docs/audits/heimgewebe-resilience-gap-matrix-v1.md)

## Was der Systemkatalog beantwortet

- Welche stabilen Systeme sind katalogisiert, und welche Metarepo-Fleet-Repositories sind abgedeckt?
- Welchem Zweck dient jedes System?
- Wofür ist es ausdrücklich nicht zuständig?
- Wem gehört welche Wahrheit?
- Welche stabilen Beziehungen bestehen?
- Wo liegen die verlässlichen Einstiegspunkte?

## Was er nicht beantwortet

- Welche Aufgabe als Nächstes bearbeitet werden soll.
- Ob ein Dienst gerade gesund ist.
- Ob ein Pull Request mergebar ist.
- Ob Tests oder Reviews ausreichend sind.
- Ob eine Ausführung erlaubt ist.
- Ob ein historischer Claim heute noch gilt.

Dafür gelten die Primärquellen:

| Bereich | Primärquelle |
|---|---|
| Aufgaben, Queue, Claims, Receipts | Bureau |
| Lokale und repositorybezogene Ausführung | Grabowski |
| Repositories, Branches, PRs, Issues, Reviews | GitHub |
| Technische Prüfergebnisse | CI und Review-Gates |
| Laufende Dienste | Runtime, systemd, Healthchecks und Logs |
| Verifizierbarer, zitierfähiger Codebase-Kontext | RepoGround |
| Allgemeine Live-Anzeige | Leitstand |

Lenskit und RepoBrief bleiben ausschließlich als Legacy-Namen und Kompatibilitätseinstiege erhalten; die kanonische Produkt- und Repositoryidentität ist RepoGround.

## Aktive Struktur

```text
catalog/              Schema und nichtkanonisches Beispiel
policy/               Rollen- und Projektionsgrenzen
registry/ecosystem/   Kanonische Systeme, Fleet-Abdeckung, Beziehungen, Claims und Zuständigkeiten
rendered/             Deterministisch erzeugte Leseansicht und Karte
scripts/              Validatoren, Renderer und Artefaktmanifest-Werkzeug
```

Die frühere Cabinet-Raumstruktur liegt ausschließlich unter `docs/archive/cabinet-era/`. Sie ist historisches Material, keine aktive Navigation, kein zweiter Katalog und keine Wahrheitsquelle.

Die Fleet-Mitgliedschaft selbst gehört Metarepo (`fleet/repos.yml`). Der Systemkatalog gleicht diese Quelle ab, übernimmt daraus aber weder Zweck noch Architektursemantik. Jedes Fleet-Repository muss katalogisiert sein; Quellausschlüsse wie `fleet: false` müssen ausdrücklich dokumentiert bleiben.

Der vollständige Organisationsumfang steht separat in `registry/ecosystem/organization-scope.v1.json`. Dort ist jedes aktive, nicht geforkte Heimgewebe-Repository entweder als Katalogsystem oder als begründeter Ausschluss klassifiziert. Die Datei enthält die vollständige aktuelle Klassifikation. CI mintet dafür kurzlebig ein ausschließlich lesendes Heimgewebe-App-Token und gleicht den Umfang einschließlich privater Repository-Metadaten live gegen GitHub ab. Die konkreten Anzahlen werden aus den kanonischen Daten berechnet statt in dieser Dokumentation doppelt gepflegt. Private Commit- und Inhaltsmetadaten werden nicht in den öffentlichen Quellenbindungen veröffentlicht.

Konkrete Coding-Agenten sind keine stabilen Katalogsysteme. Die dauerhafte Zuständigkeit für Agent-Auswahl und Rollenrouting liegt bei Grabowski und wird als Authority-Domäne `agent_routing` referenziert.

## Deterministische Abfragen

Für Agenten und lokale Werkzeuge gibt es eine statusfreie Leseoberfläche über die versionierten JSON-Dateien:

```bash
python3 scripts/systemkatalog_query.py system grabowski
python3 scripts/systemkatalog_query.py repository weltgewebe
python3 scripts/systemkatalog_query.py truth-owner agent_routing
python3 scripts/systemkatalog_query.py relations bureau
python3 scripts/systemkatalog_query.py entrypoints leitstand
```

Jede Ausgabe nennt den gelesenen Katalogcommit, die Quellpfade und – soweit öffentlich zulässig – die zugehörige Quellenbindung. Die CLI besitzt keine Datenbank, keine Schreibschnittstelle und keine Runtime-Autorität.

## Quellenbindungen und Frische

`registry/ecosystem/source-bindings.v1.json` bindet jedes System und jede stabile Beziehung an einen geprüften Quellstand, einen Locator, eine Prüfmethode, ein Prüfdatum und eine Unsicherheit. Öffentliche Repositoryquellen werden an Commit und Inhalts-SHA-256 gebunden. Bei privaten Repositories bleiben Commit und Inhalt redigiert; veröffentlicht wird nur ein Digest nichtvertraulicher Klassifikationsmetadaten.

`policy/freshness-slo.v1.json` definiert Erkennungs- und Reviewziele. GitHub- und Fleet-Abweichungen sowie Änderungen gebundener Primärdokumente erzeugen einen maschinenlesbaren Driftbericht. Der Folgeschritt bleibt ausdrücklich **proposal-only**: Er darf einen deduplizierten Bureau-Kandidaten und einen Änderungsvorschlag erzeugen, aber keine neue Semantik automatisch mergen.

```bash
python3 scripts/read_github_catalog_observations.py --output /tmp/systemkatalog-observations.json
python3 scripts/system_catalog_drift.py \
  --github-observations /tmp/systemkatalog-observations.json \
  --fleet-file /pfad/zu/metarepo/fleet/repos.yml \
  --check
```

Der Systemkatalog bleibt damit statisch. Laufzustand und Alarmanzeige gehören weiterhin in Bureau, Leitstand, CI und die lokale Operatorumgebung.

## Bereitstellung

Der Systemkatalog wird ausschließlich als versionierte, statische Repositoryartefakte bereitgestellt:

- `rendered/system-catalog.md` als lesbare Katalogansicht;
- `rendered/ecosystem-registry-map.mmd` als Mermaidkarte;
- `registry/ecosystem/*.json` und `claims.jsonl` als kanonische Daten;
- `rendered/ecosystem-map-artifact-manifest.json` als veröffentlichter, commit- und hashgebundener Übergabevertrag für Verbraucher wie Leitstand und Schauwerk.

Eine eigene HTTP-Runtime, Datenbank, Queue oder Schreibschnittstelle gehört nicht zum Produkt. Aktuelle Betriebszustände werden weiterhin an ihren jeweiligen Runtime-Primärquellen geprüft.

Cabinet- und Agentenlaufzeitpfade werden absichtlich **nicht** durch `.gitignore` verborgen. Falls solche Pfade erneut entstehen, bleiben sie im Working Tree sichtbar; der Repository-Vertrag verhindert zusätzlich, dass sie außerhalb von `docs/archive/cabinet-era/` versioniert werden.

### Manifest veröffentlichen

Das Manifest wird absichtlich in einem zweiten Commit veröffentlicht: Der erste Commit enthält die Katalogdaten und Projektionen. Danach bindet das Manifest exakt diesen Artefakt-Commit und die SHA-256-Prüfsummen der fünf ausgelieferten Dateien. So entsteht keine unmögliche Selbstreferenz auf den Commit, der das Manifest selbst enthält.

```bash
# 1. Katalogdaten und Projektionen committen
python3 scripts/render_system_catalog.py
python3 scripts/render_ecosystem_registry_map.py
git commit

# 2. Manifest an diesen Artefakt-Commit binden und separat committen
python3 scripts/write_ecosystem_map_artifact_manifest.py --source-commit "$(git rev-parse HEAD)"
git add rendered/ecosystem-map-artifact-manifest.json
git commit
```

`--check` liest die tatsächlich veröffentlichte Datei. Es scheitert, wenn das Manifest fehlt, die aktuellen Artefakte abweichen, der gebundene Commit nicht in der Git-Historie liegt oder die dort gespeicherten Bytes nicht zu den Manifest-Hashes passen.

## Validierung

```bash
./scripts/ci/validate-repository.sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/check_fleet_coverage.py --fleet-file /pfad/zu/metarepo/fleet/repos.yml
python3 scripts/check_organization_scope.py
python3 scripts/check_organization_scope.py --github-inventory /pfad/zur/github-inventory.json
```

Ein grüner Lauf belegt Struktur- und Vertragskonsistenz. Er belegt nicht automatisch Runtime-Korrektheit, fachliche Vollständigkeit oder Merge-Reife.
