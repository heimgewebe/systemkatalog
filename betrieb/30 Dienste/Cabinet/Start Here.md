# Heimgewebe-Systemkatalog-Dienst

Lokale read-only Projektion des versionierten Systemkatalogs.

- Canon: `policy/system-catalog.v1.json` und `registry/ecosystem/**`
- Oberfläche: `http://127.0.0.1:4001/`
- JSON: `http://127.0.0.1:4001/api/catalog.json`
- systemd: `heimgewebe-systemkatalog.service`
- Kompatibilitätsalias: `cabinet.service`
- Implementierung: Python-Standardbibliothek
- persistenter Dienstzustand: keiner
- externer Cabinet-Daemon: retired
- nichtlokale Listener: keine

Bedienung:

```bash
systemkatalogctl status
systemkatalogctl url
systemkatalogctl restart
```

Audit:

```bash
ops/install/audit-local-runtime.sh
```
