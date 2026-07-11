# Heimgewebe-Systemkatalog — lokale Runtime

Dieses Verzeichnis beschreibt die aktive, reproduzierbare Leseoberfläche des Heimgewebe-Systemkatalogs.

## Architektur

- Canon: versionierte Dateien unter `policy/`, `registry/ecosystem/` und `rendered/`
- Runtime: `heimgewebe-systemkatalog.service`
- Implementierung: Python-Standardbibliothek
- Bindung: ausschließlich Loopback
- sichtbare Oberfläche: `http://127.0.0.1:4001/`
- alter Daemon-Port: nicht mehr vorhanden
- persistenter Runtimezustand: keiner
- Secrets oder Providerzugänge: keine

Die Runtime liest den Katalog bei jedem Request neu aus dem Repository. Sie schreibt weder Katalogdaten noch Aufgaben-, Runtime- oder Agentenzustand.

## Endpunkte

- `/` — HTML-Leseoberfläche
- `/healthz` — technischer Bereitschaftsendpunkt
- `/api/catalog.json` — zusammengesetzter Katalog
- `/api/nodes.json` — kanonische Systeme
- `/api/edges.json` — kanonische Beziehungen
- `/api/authority-matrix.json` — Wahrheitszuständigkeiten
- `/api/policy.json` — Rollenpolicy
- `/catalog.md` — Markdownprojektion
- `/map.mmd` — Mermaidprojektion

## Installation und Cutover

Nur Dateien installieren, Dienstzustand nicht ändern:

```bash
ops/install/install-local-runtime.sh
```

Alte externe Cabinet-App stoppen und deaktivieren, neue Runtime installieren und aktivieren:

```bash
ops/install/install-local-runtime.sh --cutover
```

Vorhandene Units und Bedienwerkzeuge werden vor dem Cutover unter `~/.local/state/cabinet/runtime-cutovers/` gesichert. Private App-, Konfigurations- und Evidence-Bestände werden nicht als Kataloginhalt übernommen und durch den Installer nicht gelöscht.

## Bedienung

```bash
systemkatalogctl status
systemkatalogctl url
systemkatalogctl restart
```

## Audit

```bash
ops/install/audit-local-runtime.sh
```

Erwarteter Abschluss:

```text
TARGET-PROOF: HEIMGEWEBE SYSTEM CATALOG RUNTIME MATCHES REPOSITORY
```

Der Audit prüft:

- Katalogvalidierung und Renderdrift;
- installierte Unit und Werkzeuge gegen das Repository;
- aktiven und aktivierten Dienst;
- kein Kompatibilitätsalias unter dem alten Cabinet-Namen;
- Abwesenheit der alten App-Starter und Drop-ins;
- HTML- und JSON-Oberfläche;
- geschlossenen früheren Daemon-Port.

## Repository- und CI-Vertrag

- `scripts/ci/check-repository-contract.py` verweigert alte Node-/Next-App-Runtimeflächen.
- `scripts/ci/test-install-local-runtime.sh` prüft Installation und Idempotenz in einem isolierten Home.
- `scripts/tests/test_system_catalog_service.py` prüft Payload, HTML-Escaping, Loopback-Gate und read-only HTTP-Verhalten.
- Secret-Scan und der übrige Cabinet-Testbestand bleiben Bestandteil der CI.

Die CI belegt den versionierten Vertrag. Der lokale Audit belegt den tatsächlich installierten Dienst.
