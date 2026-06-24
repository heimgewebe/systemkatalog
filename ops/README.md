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

Secrets dürfen nicht versioniert werden. Vor Remote-Pushes werden
Tree und Historie auf bekannte Secretmuster geprüft.

## CI und Validierung

Dieses Repository trennt strikt zwischen dem versionierten Repository-Vertrag
und dem lokalen Laufzeitzustand. Die CI prüft ausschließlich den sauberen
Repository-Zustand und niemals den lokalen Betriebszustand.

### Repositoryvertrag (`repository-contract`)

- Prüft den vollständig materialisierten Git-Baum von HEAD.
- Erkennt verbotene versionierte Pfade (Datenbanken, Laufzeitzustand,
  Secrets, Agentenlaufzeitverzeichnisse).
- Verifiziert das Manifest exakt: Quellenmengen, Feldmengen, Git-Dateimodi
  und Duplikatfreiheit.
- Prüft Syntax aller Python- und Bash-Skripte im Snapshot.
- Der globale `TARGET-PROOF: CABINET REPOSITORY CONTRACT VALID` erscheint
  ausschließlich nach allen Teilprüfungen.

### Installer-Shadow-Test (`installer-shadow`)

- Führt den Installer aus einem temporären `git archive`-Snapshot aus,
  nicht aus dem echten Checkout.
- Installiert in ein temporäres Home-Verzeichnis mit `systemctl`-Stub.
- Prüft Binaries, Units, Symlink, `runtime.env`-Hash und systemctl-Aufrufe
  nach Lauf 1 und Lauf 2.
- Beweist, dass der getrackte Git-Zustand und HEAD des echten Repositorys
  vor und nach dem Test unverändert bleiben
  (`TARGET-PROOF: SOURCE REPOSITORY WAS NOT MODIFIED`).
- Prüft fünf negative Zustandsmutationen gegen den Installationschecker
  (`check-installed-runtime.py`).

### Secret-Scan (`secret-scan`)

- Scannt den Git-Commit-Baum (`dir`-Modus) und die vollständige
  Commit-Geschichte (`git`-Modus) mit dem festgepinnten Gitleaks-Image.
- Ergebnis wird durch `check-gitleaks-result.py` ausgewertet: Returncode,
  Berichtsexistenz, JSON-Gültigkeit, Array-Typ und Findingzahl.
- `--ignore-gitleaks-allow` ist gesetzt: gitleaks:allow-Kommentare werden
  nicht als Ausnahme akzeptiert.
- Ein erfolgreicher Scan belegt, dass keine bekannten Secretmuster im
  aktuellen Baum oder der Geschichte enthalten sind. Ein erfolgreicher
  Scan beweist keine vollständige Secret-Abwesenheit.

### Grenzen der CI-Aussagekraft

Die CI erzwingt die definierten Repositoryverträge und prüft bekannte
Secretmuster. Sie beweist weder die reale Laufzeitfunktion noch vollständige
Secret-Abwesenheit.

`audit-local-runtime.sh` bleibt der Beweis für die echte lokale Runtime
und den echten systemd-Dienst. Dieser Schritt wird bewusst nicht in der
CI ausgeführt.

### Lokale Validierung

```bash
cd ~/repos/cabinet
./scripts/ci/validate-repository.sh
./scripts/ci/test-validate-repository.sh
./scripts/ci/test-install-local-runtime.sh
./scripts/ci/test-gitleaks-contract.sh
```

GitHub Actions Jobs (siehe `.github/workflows/validate.yml`):
- `repository-contract`
- `installer-shadow`
- `secret-scan`
