# Private Cabinet Archive v1

Status: migration tooling; no export execution authorized by this document

Bureau task: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T012`

## Zweck

Vor der späteren Entkopplung der externen Cabinet-App müssen nichtversionierte private Daten überprüfbar erhalten werden. `scripts/private_cabinet_archive.py` stellt dafür einen begrenzten, fail-closed Sicherungsweg bereit.

Das Werkzeug ist **nicht** der portable Safe Export. Der Safe Export entfernt private Runtime-Daten für eine kontrollierte Weitergabe. Das Private Cabinet Archive sichert genau diese privaten Daten in ein lokales, nicht öffentliches Archiv.

## Sicherheitsmodell

- Das Ziel muss als absoluter Pfad angegeben werden, darf noch nicht existieren und darf in keinem Repository oder Quellverzeichnis liegen.
- Das Ziel wird atomar und create-only reserviert. Bis zum vollständigen Abschluss markiert `.incomplete` das Archiv als nicht verwendbar.
- Das Archiv wird mit Verzeichnisrechten `0700` und Dateirechten `0600` angelegt.
- Symbolische Links, Spezialdateien, Pfadausbrüche und nachträglich veränderte Quelldateien führen zum Abbruch.
- Die laufende SQLite-Datenbank wird mit der SQLite-Online-Backup-Funktion kopiert. WAL- und SHM-Dateien werden nicht gewöhnlich kopiert.
- Die Sicherungskopie wird auf eine selbständige SQLite-Datei normalisiert und mit `PRAGMA quick_check` geprüft.
- Reproduzierbare Mehr-GiB-Programmdateien, Abhängigkeiten, Builds, Dumps und Snapshots bleiben ausgeschlossen.
- Einzeldatei- und Gesamtgrößenlimits brechen fail-closed ab, statt unerwartet große Datenbäume zu übernehmen.
- Eine private Prüfliste enthält nur relative Archivpfade, Dateimodi, Größen und SHA-256-Werte. Absolute Quellpfade stehen nicht darin.
- Öffentliche Konsolenausgaben enthalten ausschließlich Klassifikation, Umfang, Backupstatus und bekannte Abdeckungslücken.
- `plan` darf bekannte Lücken melden; `export` bricht bei jeder bekannten Abdeckungslücke ab.
- Das Werkzeug stoppt, startet oder deaktiviert keinen Dienst und löscht keine Quelldaten.

Das Archiv wird nicht selbst verschlüsselt. Vor einem echten Lauf muss die separate Bureau-Autorisierung deshalb ein geschütztes Ziel festlegen, etwa ein bereits verschlüsseltes Dateisystem oder einen anschließend kontrolliert verschlüsselnden Backup-Pfad.

## Befehle

Die Beispiele verwenden Platzhalter. Sie sind keine Freigabe für einen echten Export.

### Nur lesen und planen

```bash
python3 scripts/private_cabinet_archive.py plan \
  --home <HOME> \
  --repo <CABINET_REPO> \
  --app-root <CABINET_APP_ROOT>
```

`plan` schreibt nichts. Es gibt nur eine redaktierte Umfangs- und Lückenübersicht aus.

### Privates Archiv erzeugen

```bash
python3 scripts/private_cabinet_archive.py export \
  --home <HOME> \
  --repo <CABINET_REPO> \
  --app-root <CABINET_APP_ROOT> \
  --destination <NEUES_PRIVATES_ZIEL>
```

Dieser Befehl benötigt vor der Ausführung eine eigene, wirkungsgebundene Bureau-Autorisierung. Das Ziel ist create-only; ein vorhandener Pfad wird niemals überschrieben.

### Archiv prüfen

```bash
python3 scripts/private_cabinet_archive.py verify \
  --archive <PRIVATES_ARCHIV>
```

Die Prüfung bindet die private Prüfliste an alle Nutzdaten, kontrolliert Dateirechte und führt für jede SQLite-Datei einen Integritätstest aus. SHA-256 erkennt Änderungen gegenüber der Prüfliste, ist aber keine digitale Signatur und beweist ohne geschützte Aufbewahrung nicht die Herkunft des Archivs.

### Isolierte Wiederherstellung prüfen

```bash
python3 scripts/private_cabinet_archive.py restore \
  --archive <PRIVATES_ARCHIV> \
  --target <NEUES_ISOLIERTES_ZIEL>
```

Die Wiederherstellung schreibt ausschließlich in ein neues, leeres Ziel. Sie kennt absichtlich keine produktiven Zielpfade und überschreibt keine laufende Installation.

## Was die Wiederherstellung beweist

Belegt werden:

- alle im Manifest erfassten Dateien sind lesbar und hashidentisch;
- SQLite-Sicherungen sind strukturell intakt;
- die Nutzdaten lassen sich in einen isolierten Verzeichnisbaum materialisieren;
- der laufende Dienst musste dafür nicht verändert werden.

Nicht belegt werden:

- die externe App startet mit den Daten;
- alle entfernten oder unbekannten Consumer sind erfasst;
- ein Dienststopp ist sicher;
- Daten dürfen gelöscht werden;
- das Repository darf umbenannt werden.

## Wirkungsstufen

1. **Inventur:** nur lesen und klassifizieren.
2. **Werkzeugentwicklung:** Code, Tests und Dokumentation per Pull Request.
3. **Exportausführung:** exaktes Werkzeug, Ziel und create-only Wirkung separat autorisieren.
4. **Restore-Beleg:** Archiv prüfen und nur isoliert wiederherstellen.
5. **Runtime-Rückbau:** erst danach und in einem eigenen Bureau-Task.
