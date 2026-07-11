# Systemkatalog — lokale Runtime

Die optionale Runtime stellt den versionierten Katalog lokal und ausschließlich lesend bereit.

- Unit: `systemkatalog.service`
- Programm: `~/.local/bin/systemkatalog`
- Bedienung: `~/.local/bin/systemkatalogctl`
- Adresse: `http://127.0.0.1:4001/`
- Datenbank, Scheduler und Schreibschnittstelle: keine

## Installation und Cutover

```bash
./ops/install/install-local-runtime.sh --cutover
./ops/install/audit-local-runtime.sh
```

Der Installer sichert vorhandene Unit- und Programmdateien unter `~/.local/state/systemkatalog/runtime-cutovers/`, entfernt alte Dienst- und Programmaliase und startet anschließend nur `systemkatalog.service`.

Private historische Cabinet-Konfigurationen und -Belege werden nicht gelöscht. Sie sind kein aktiver Kataloginhalt.

## Kontrolle

```bash
systemkatalogctl status
systemkatalogctl url
curl -fsS http://127.0.0.1:4001/api/catalog.json
```

Ein erfolgreicher Runtime-Audit belegt, dass installierte Unit und Programme exakt zum Repository passen und der read-only Dienst antwortet. Er belegt nicht die fachliche Vollständigkeit des Katalogs.
