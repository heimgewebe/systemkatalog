# Architektur des Systemkatalogs

## Zweck

Der Systemkatalog ist eine kleine, app-unabhängige Wissensschicht. Er hält nur Informationen, die sich nicht mit jedem Lauf, Pull Request oder Task ändern.

## Kanon

| Inhalt | Kanonische Datei |
|---|---|
| Systeme | `registry/ecosystem/nodes.json` |
| Beziehungen | `registry/ecosystem/edges.json` |
| stabile, belegte Aussagen | `registry/ecosystem/claims.jsonl` |
| Wahrheitszuständigkeiten | `registry/ecosystem/authority-matrix.v1.json` |
| Repository- und Fleet-Abdeckung | `registry/ecosystem/fleet-coverage.v1.json` |
| Rollen- und Wirkungsgrenze | `policy/system-catalog.v1.json` |
| Verbraucherübergabe | `rendered/ecosystem-map-artifact-manifest.json` |

`rendered/system-catalog.md`, `rendered/ecosystem-registry-map.mmd` und das Karten-Manifest sind deterministische Projektionen. Sie dürfen den Kanon nicht überschreiben.

## Fleet- und Kataloggrenze

Metarepo ist die Primärquelle für die Mitgliedschaft in der Heimgewebe-Fleet. Der Systemkatalog übernimmt daraus keine Zwecke oder Architekturbehauptungen. Er verlangt lediglich, dass jedes Fleet-Repository als Katalogsystem beschrieben oder ein Quellausschluss ausdrücklich dokumentiert ist.

Der Systemkatalog bleibt Primärquelle für Zweck, stabile Beziehungen, Wahrheitszuständigkeiten und Einstiegspunkte. Der Abgleich wird lokal oder in CI mit `scripts/check_fleet_coverage.py` gegen `metarepo/fleet/repos.yml` ausgeführt.

Konkrete Coding-Agenten und Provider sind wechselnde Runtime-Details. Die stabile Zuständigkeit `agent_routing` gehört Grabowski; der Katalog verweist auf dessen Rollenvertrag, statt einzelne Agenten zu spiegeln.

## Projektion und Bereitstellung

Der Systemkatalog besitzt keine eigene Laufzeit. Markdown, Mermaid, JSON/JSONL und das Map-Artefaktmanifest werden deterministisch aus den versionierten Repositorydateien erzeugt und von Verbrauchern read-only übernommen. Das versionierte Manifest wird in einem zweiten Commit erzeugt und bindet den unmittelbar vorher veröffentlichten Artefakt-Commit. Diese Zweistufigkeit verhindert eine Selbstreferenz des Manifests auf seinen eigenen Commit. Vor dem Merge darf der Writer oder die PR-CI einen ausdrücklich angegebenen, lokal gefetchten Remote-Tracking-Ref als Dauerhaftigkeitsbeleg verwenden. Dieser Ref beweist allein die lokale Git-Abstammung; der Aufrufer muss seine Remote-Identität und den erwarteten SHA separat prüfen. Die GitHub-PR-CI fetchte deshalb Repository und Branch aus dem Event und vergleicht den resultierenden Ref bytegenau mit dem Event-Head-SHA. Nach dem Merge verwendet `--check` ohne Override ausschließlich `refs/remotes/origin/main` und prüft Datei, aktuelle Hashes, Git-Abstammung sowie die Bytes im gebundenen Commit. Ein PR mit neuem Artefakt- und Manifestcommit muss deshalb per Merge-Commit integriert werden; Squash oder Rebase würden den gebundenen Quellcommit zerstören und die Post-Merge-Prüfung korrekt scheitern lassen.

Aktuelle Dienstzustände bleiben außerhalb des Katalogs bei Runtime, systemd, Healthchecks und Logs. Diese Grenze verhindert, dass der Systemkatalog selbst zu einem zweiten Status- oder Betriebsmodell wird.

## Archivgrenze

`docs/archive/cabinet-era/` enthält die frühere Cabinet-Oberfläche, Raumgerüste, operative Experimente und Migrationsbelege. Das Archiv wird nicht in den aktiven Katalog eingespeist und nicht von den Validatoren als Kanon interpretiert.

## Änderungsregel

Eine Information gehört nur dann in den Systemkatalog, wenn sie:

1. eine stabile Systemrolle, Grenze oder Beziehung beschreibt;
2. eine benannte Primärquelle besitzt;
3. keinen aktuellen Betriebs-, Task-, PR- oder Reviewzustand kopiert;
4. reproduzierbar validiert und projiziert werden kann.

## Auffindbarkeit und Pflegekreislauf

Der Katalog wird nicht ungefragt in jede Agentenaufgabe geladen. Ein Agent soll ihn konsultieren, wenn eine Frage mehrere Repositories, Systemzwecke, Zuständigkeitsgrenzen, Wahrheitsbesitz, stabile Beziehungen oder Einstiegspunkte betrifft. `scripts/systemkatalog_query.py` liefert dafür eine kleine, deterministische Projektion der kanonischen Dateien.

Quellenbindungen und Frische bleiben getrennte Verträge:

- `registry/ecosystem/source-bindings.v1.json` dokumentiert, worauf eine katalogisierte Aussage geprüft wurde;
- `policy/freshness-slo.v1.json` legt fest, wie schnell unterschiedliche Driftarten erkannt und zur Prüfung vorgelegt werden sollen;
- `scripts/system_catalog_drift.py` erzeugt einen maschinenlesbaren Bericht und einen proposal-only Änderungsvorschlag;
- Bureau oder ein unabhängiger Operator-Watchdog kann materielle Drift als deduplizierten Kandidaten sichtbar machen.

Keiner dieser Schritte darf Zwecke, Grenzen, Wahrheitsbesitz oder Beziehungen ungeprüft in `main` schreiben. Erkennung ist automatisierbar; semantische Annahme bleibt reviewpflichtig.
