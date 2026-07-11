# Systemkatalog

Der Systemkatalog beschreibt die stabilen Bestandteile des Heimgewebe-Ökosystems: vorhandene Systeme, ihren Zweck, ihre Grenzen, Wahrheitszuständigkeiten, dauerhafte Beziehungen und Einstiegspunkte.

Er ist **kein Steuerungs- oder Statussystem**. Aufgaben, Prioritäten, Laufzustände, Pull Requests, Prüfungen und Ausführung bleiben bei den dafür zuständigen Primärsystemen.

## Einstieg

1. [Erzeugte Leseansicht](rendered/system-catalog.md)
2. [Katalogpolicy](policy/system-catalog.v1.json)
3. [Systeme](registry/ecosystem/nodes.json)
4. [Stabile Beziehungen](registry/ecosystem/edges.json)
5. [Wahrheitszuständigkeiten](registry/ecosystem/authority-matrix.v1.json)
6. [Agenteneinstieg](AGENTS.md)
7. [Architektur](docs/architecture/systemkatalog.md)
8. [Audit der früheren Cabinet-Räume](docs/audits/systemkatalog-room-audit-v1.md)

## Was der Systemkatalog beantwortet

- Welche Systeme existieren?
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
| Zitierfähiger Repositorykontext | RepoBrief / Lenskit |
| Allgemeine Live-Anzeige | Leitstand |

## Aktive Struktur

```text
catalog/              Schema und nichtkanonisches Beispiel
policy/               Rollen- und Projektionsgrenzen
registry/ecosystem/   Kanonische Systeme, Beziehungen, Claims und Zuständigkeiten
rendered/             Deterministisch erzeugte Leseansicht und Karte
scripts/              Validatoren, Renderer und read-only Dienst
ops/                  Reproduzierbare lokale Runtime
```

Die frühere Cabinet-Raumstruktur liegt ausschließlich unter `docs/archive/cabinet-era/`. Sie ist historisches Material, keine aktive Navigation, kein zweiter Katalog und keine Wahrheitsquelle.

## Lokale Leseoberfläche

Der Katalogkanon benötigt keinen Server. Optional stellt `systemkatalog.service` eine zustandslose, read-only Oberfläche auf Loopback bereit.

```bash
./ops/install/install-local-runtime.sh --cutover
systemkatalogctl status
```

Die Runtime enthält keine Datenbank, keinen Scheduler, keinen Agenten und keine Schreibschnittstelle.

## Validierung

```bash
./scripts/ci/validate-repository.sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

Ein grüner Lauf belegt Struktur- und Vertragskonsistenz. Er belegt nicht automatisch Runtime-Korrektheit, fachliche Vollständigkeit oder Merge-Reife.
