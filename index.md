# Cabinet Home — Heimgewebe-Systemkatalog

Cabinet wird zu einem app-unabhängigen Katalog für Systeme, Zwecke, Wahrheitszuständigkeiten, stabile Beziehungen und Einstiegspunkte.

## Aktive Einstiege

- [README](README.md) — Zielrolle und Schnellstart.
- [Agent Entry](AGENTS.md) — Lesereihenfolge, Wahrheitsgrenzen und Stop-Kriterien.
- [Lesbarer Systemkatalog](rendered/system-catalog.md) — deterministisch erzeugte Katalogansicht ohne Live-, Task- oder Merge-Status.
- [Systemkatalog-Policy](policy/system-catalog.v1.json) — maschinenlesbare Rollen- und Wirkungsgrenze.
- [Authority Matrix](registry/ecosystem/authority-matrix.v1.json) — Zuordnung der Wahrheitsdomänen zu ihren Primärquellen.
- [Knoten](registry/ecosystem/nodes.json) und [Beziehungen](registry/ecosystem/edges.json) — kanonische stabile Katalogregistry.
- [Migrationsmatrix](docs/migration/cabinet-surface-matrix-v1.md) — Keep/Simplify/Move/Archive/Remove für die bestehende Oberfläche.
- [Runtime-Rückbau-Preflight](docs/migration/cabinet-runtime-retirement-preflight-v1.json) und [Autorisierungs-/Rollbackpaket](docs/migration/cabinet-runtime-retirement-authorization-v1.md) — datierter T013-Entscheidungsbeleg ohne Abschaltfreigabe.
- [Zielformat](catalog/system-catalog.schema.v1.json) und [nichtkanonisches Beispiel](catalog/system-catalog.example.v1.json) — app-unabhängiger Datenvertrag.

## Wahrheitsrouting

- Aufgaben, Queue und Receipts → Bureau.
- Repository-, PR- und Reviewzustand → GitHub.
- technische Prüfergebnisse → CI und Review-Gates.
- laufender Dienstzustand → Runtime, Healthchecks, systemd und Logs.
- lokale und repositorybezogene Ausführung → Grabowski.
- allgemeine Live-Anzeige → Leitstand.
- Snapshots und zitierfähiger Repositorykontext → RepoBrief / Lenskit.

Cabinet verweist auf diese Quellen, führt aber keine zweite Kopie ihrer wechselnden Zustände.

## Migrationsflächen

Die bisherigen Bereiche [Bestand](bestand/index.md), [Prüfung](pruefung/index.md) und [Steuerung](steuerung/index.md) sowie alte Karten-, Radar-, Gemini- und Runtime-Dokumente bleiben vorerst lesbar. Sie sind jedoch Migrations- oder historische Flächen und nicht automatisch Bestandteil des Zielkatalogs.

Die externe Cabinet-App ist nur noch ein vorübergehender optionaler Viewer. Abschaltung, Datenexport und Repository-Rename werden separat im Bureau gesteuert.
