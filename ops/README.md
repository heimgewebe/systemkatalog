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

## CI und Validierung

Dieses Repository trennt strikt zwischen dem versionierten Repository-Vertrag und dem lokalen Laufzeitzustand. Die CI prüft ausschließlich den sauberen Repository-Zustand.

- **Pfadguard:** Erkennt verbotene versionierte Dateipfade im Repository-Vertrag.
- **Gitleaks:** Die CI prüft den aktuellen Git-Baum und die Git-Historie mit Gitleaks auf bekannte Secretmuster. Ein erfolgreicher Scan beweist keine vollständige Secret-Abwesenheit.
- **Installer-Shadow-Test:** Beweist die isolierte Dateisysteminstallation in einem temporären Verzeichnis und deren Idempotenz.
- **audit-local-runtime.sh:** Prüft die echte lokale Runtime und den echten systemd-Dienst. Dies wird bewusst nicht in der CI ausgeführt.

**Sicherheitsgrenze:** GitHub CI beweist keinen laufenden Cabinet-Dienst. Sie garantiert lediglich die strukturelle und syntaktische Unversehrtheit des Repositories sowie das Nichtvorhandensein bekannter Dateinamen und Secretmuster.

Lokale Validierung:
```bash
cd ~/repos/cabinet
./scripts/ci/validate-repository.sh
```

Lokale negative Validator-Tests:
```bash
./scripts/ci/test-validate-repository.sh
```

Lokaler isolierter Installer-Shadow-Test:
```bash
./scripts/ci/test-install-local-runtime.sh
```

GitHub Actions Jobs (siehe `.github/workflows/validate.yml`):
- `repository-contract`
- `installer-shadow`
- `secret-scan`
