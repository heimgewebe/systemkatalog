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

## Vorbereiteter Rückbau

Der lokale HTTP-Dienst ist optional. Sein Rückbau wird mit einem eigenen, standardmäßig rein prüfenden Werkzeug vorbereitet:

```bash
./ops/install/retire-local-runtime.sh --dry-run
```

Ein tatsächlicher Rückbau ist eine abschaltende Betriebsänderung. Er darf erst nach einer gültigen Bureau-Autorisierung und nur gegen den ausdrücklich freigegebenen, gemergten Repository-Commit erfolgen:

```bash
./ops/install/retire-local-runtime.sh --apply \
  --authorization-reference Bureau:<TASK-ID> \
  --expected-head <vollständiger-Git-Commit>
```

Das Vorhandensein dieses Skripts ist **keine Autorisierung**. Vor einer Entfernung prüft es:

- sauberer und exakt gebundener Repository-Stand;
- bytegleiche installierte Unit und Programme;
- vollständige, nicht durch Symlinks ersetzte Runtimeinstallation;
- formal gebundene Bureau-Task-Referenz im Format `Bureau:<TASK-ID>`.

Die tatsächliche Existenz und Freigabe des Tasks muss Grabowski vor dem Aufruf live im Bureau prüfen; das lokale Skript zeichnet die Referenz nur auf. Anschließend sichert es die drei entfernten Runtime-Dateien unter `~/.local/state/systemkatalog/runtime-retirements/`, erzeugt SHA-256-Prüfsummen, ein lokales Receipt und eine Wiederherstellungsanleitung. Andere Programme sowie private Cabinet- und Systemkatalog-Zustände bleiben unberührt. Der Vorgang ist wiederholbar: Eine bereits vollständig entfernte Runtime wird als solcher Zustand erkannt.

## Kontrolle

```bash
systemkatalogctl status
systemkatalogctl url
curl -fsS http://127.0.0.1:4001/api/catalog.json
```

Ein erfolgreicher Runtime-Audit belegt, dass installierte Unit und Programme exakt zum Repository passen und der read-only Dienst antwortet. Er belegt nicht die fachliche Vollständigkeit des Katalogs.
