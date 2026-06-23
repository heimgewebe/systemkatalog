# Cabinet Local Runtime

Dieses Verzeichnis beschreibt den reproduzierbaren lokalen
Betriebsvertrag von Cabinet.

## Ebenen

- `~/repos/cabinet`: versionierte Cabinet-Inhalte und Betriebsdefinitionen
- `~/.config/cabinet`: lokale Konfiguration und Secrets
- `~/.local/bin`: installierte Start- und Kontrollwerkzeuge
- `~/.local/state/cabinet`: Logs und Backups
- `~/.cabinet`: installierter, versionsgebundener Cabinet-App-Code

## Enthalten

- systemd-Unit und Loopback-Drop-in als Templates
- Start-, Session-, Control- und Security-Werkzeuge
- secretfreie Runtime-Environment-Vorlage
- versionsgebundener Dark-Default-Patch für Cabinet 0.4.4
- lokaler Installer
- Drift- und Health-Audit

## Nicht versioniert

- `~/.config/cabinet/runtime.env`
- Passwörter und API-Schlüssel
- SQLite-Indizes
- Logs
- Laufzeitstatus
- Cabinet-App-Installation
- Browserpräferenzen

## Erstinstallation

```bash
cd ~/repos/cabinet

mkdir -p ~/.config/cabinet
cp ops/env/runtime.env.example ~/.config/cabinet/runtime.env
chmod 600 ~/.config/cabinet/runtime.env
```

Danach die leeren Werte ausschließlich lokal ergänzen.

```bash
ops/install/install-local-runtime.sh --restart
```

## Audit

```bash
cd ~/repos/cabinet
ops/install/audit-local-runtime.sh
```

Erwarteter Abschluss:

```text
TARGET-PROOF: CABINET LOCAL RUNTIME MATCHES REPOSITORY
```

## Dark-Default

Der Patch ist strikt auf Cabinet `0.4.4` begrenzt.

Prüfen:

```bash
ops/patches/cabinet-v0.4.4-dark-default.py --check
```

Anwenden:

```bash
ops/patches/cabinet-v0.4.4-dark-default.py --apply
```

Ein Cabinet-Update darf nicht blind mit diesem Patch behandelt werden.
Für jede neue Version müssen Pfade, Marker und Theme-Vertrag erneut
geprüft werden.

## Sicherheitsregel

Das Repository enthält keine Secrets. Ein Remote-Push ist nur nach
einem vollständigen Tree- und History-Scan zulässig.
