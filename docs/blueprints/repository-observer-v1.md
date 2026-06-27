# Repository Observer v1

## Zweck

Der Repository Observer ist der deterministische Sammler aus Phase 6 der Repository-Oversight-Roadmap. Er erhebt einen neuen, datierten Git-Zustand ausschließlich für ausdrücklich freigegebene lokale Repositories.

Er ersetzt keine `Repository Reference.md`, aktualisiert keine Projektkarte und erzeugt noch keine bestätigte Lage. Erst spätere Phasen dürfen eine Beobachtung mit Evidence-Regeln prüfen und in Bestand oder Steuerung übernehmen.

## Freigabe

Die versionierte Allowlist liegt in `policy/repository-observation.json`.

Jeder Eintrag enthält:

- eine stabile Repository-ID;
- genau einen direkten Unterordner unter dem zur Laufzeit angegebenen `source-root`;
- den erwarteten kanonischen GitHub-Remote;
- den Pfad einer vorhandenen `Repository Reference.md`.

Die Policy wird gegen die Reference geprüft. Repository-ID und kanonischer Remote müssen dort ausdrücklich vorkommen. Doppelte IDs, Verzeichnisse oder References werden abgewiesen.

Repositories, die nur zufällig neben freigegebenen Repositories unter `source-root` liegen, werden weder geöffnet noch ausgegeben.

## Erhobene Felder

Für jedes freigegebene Repository werden read-only erhoben:

- Branch oder `detached`;
- vollständige HEAD-Commit-ID;
- normalisierter Origin-Remote;
- Upstream und Upstream-HEAD, sofern vorhanden;
- Working-Tree-Zustand `clean` oder `dirty`;
- Anzahl logischer Porcelain-v2-Statusdatensätze;
- SHA-256 der rohen NUL-separierten Statusbytes.

Dateinamen und Inhalte uncommitteter Änderungen werden nicht in das Ergebnis geschrieben. Absolute Hostpfade werden ebenfalls nicht ausgegeben; Pfade bleiben relativ zum übergebenen `source-root`.

## Determinismus

Ein Lauf benötigt einen expliziten RFC3339-Zeitpunkt mit Zeitzone und ganzen Sekunden. Der Zeitpunkt wird nach UTC normalisiert.

Bei identischer Policy, identischen Git-Zuständen und demselben normalisierten Zeitpunkt entstehen identische JSON-Bytes und dieselbe `collection_id`.

Die Policy-SHA-256 ist Teil des Ergebnisses. Änderungen an Freigaben oder Policy-Formatierung bleiben dadurch sichtbar.

## Sicherheitsgrenzen

- Kein Netzwerkzugriff: kein Fetch, Pull oder Remote-Update.
- Keine Mutation der Quell-Repositories.
- Nur direkte, in der Policy benannte Unterordner werden geöffnet.
- Symlink-Komponenten, fehlende Repositories und falsche Repository-Toplevels scheitern fail-closed.
- Der Origin muss nach Normalisierung exakt dem freigegebenen Remote entsprechen.
- Unerwartete Git-Fehler werden nicht als „kein Upstream“ umgedeutet.
- Ausgabedateien werden atomar mit Modus `0600` geschrieben; der Zielordner muss bereits existieren und symlinkfrei sein.
- Die Ausgabe ist eine Beobachtung, keine bestätigte Evidence und keine aktuelle Repository Reference.

## Bedienung

Policy und References prüfen:

```bash
python3 scripts/observe-repositories.py validate-policy --repo-root .
```

Lokalen Lauf vorbereiten und ausführen:

```bash
OBSERVED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_DIR="$HOME/.local/state/cabinet/repository-observations/${OBSERVED_AT//:/-}"
install -d -m 700 "$RUN_DIR"

python3 scripts/observe-repositories.py collect \
  --repo-root . \
  --source-root "$HOME/repos" \
  --observed-at "$OBSERVED_AT" \
  --output "$RUN_DIR/collection.json"
```

Ohne `--output` wird ausschließlich das kanonische JSON auf Standardausgabe geschrieben.

## Prüfung

```bash
python3 scripts/observe-repositories.py validate-policy --repo-root .
python3 -m unittest discover -s scripts/tests -p 'test_repository_observer_*.py'
```

Erwarteter Policy-Abschluss:

```text
REPOSITORY-OBSERVER-POLICY: PASS
Approved repositories: 5
```

## Nicht Bestandteil von v1

- automatische Zeitplanung;
- Git-Fetch oder Hosting-API-Abfragen;
- Aktualisierung von Repository References;
- Ablage von Live-Ausgaben im Git-Repository;
- Bewertung, Befund, Priorisierung oder Auftrag;
- automatische Änderung fremder Repositories.
