# Cabinet Runtime Retirement — Autorisierungs- und Rollbackpaket v1

Status: vorbereitet, **nicht autorisiert und nicht ausgeführt**

Bureau-Task: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013`

Öffentlicher Beleg: [cabinet-runtime-retirement-preflight-v1.json](cabinet-runtime-retirement-preflight-v1.json)

## Ausgangslage

Der Systemkatalog ist seit T004 von der externen Cabinet-App unabhängig. Katalogdaten, Validatoren und Renderer benötigen keinen App- oder Daemonbetrieb.

Der datierte Preflight zeigt zugleich:

- Die externe Runtime lief zum Beobachtungszeitpunkt weiterhin als aktivierter Dienst.
- Ihr Prozessbaum umfasste acht Prozesse.
- Zwei Listener waren ausschließlich lokal gebunden.
- Die externe App belegte rund 1,89 GB.
- Der private Zustand außerhalb des Belegs umfasste rund 1,38 MB und 77 Dateien.
- Die tatsächlich beobachtete Runtime war Version 0.5.0.
- Der versionierte Installations- und Auditvertrag beschreibt noch Version 0.4.4.
- Der vorhandene Audit stoppte deshalb korrekt bei lokalem Wrapperdrift.

Dieser Drift soll **nicht** durch eine neue Pflegegeneration für die Fremd-App behoben werden. Das würde den bereits app-unabhängigen Katalog erneut an die externe Runtime binden. Der Drift ist stattdessen Teil des kontrollierten Rückbaupfads.

## Entscheidungsvorschlag

Empfohlen wird ein gestufter, reversibler Rückbau. Jede Phase erhält eine eigene, zielgebundene Autorisierung. Das Freigeben einer Phase autorisiert keine spätere Phase.

### Phase A — begrenzter Stopptest

**Zweck:** Nachweisen, dass der Katalog und seine CI-/Arbeitswege ohne laufende externe App verwendbar bleiben.

**Wirkung:** Dienst vorübergehend stoppen; keine Datei löschen, verschieben oder deaktivieren.

**Vorprüfung:**

- frischer Dienst- und Prozesssnapshot;
- unveränderte private Evidence- und Exportbelege;
- sauberer Cabinet-Checkout;
- aktuelle Consumer-/Hostunsicherheiten dokumentiert;
- festgelegtes kurzes Beobachtungsfenster.

**Erfolgskriterien:**

- Systemkatalog validiert und rendert;
- keine belegte notwendige Consumerfunktion bricht;
- Dienst bleibt während des Fensters bewusst gestoppt;
- keine Daten- oder Konfigurationsänderung.

**Rollback:** Dienst sofort neu starten und lokalen Loopbackbetrieb sowie Katalogprüfungen verifizieren.

**Stop-Kriterien:** unerwarteter Consumerfehler, fehlende Rollbackfähigkeit, veränderte Evidence-Hashes oder unklare Dienstzuordnung.

### Phase B — Dienst deaktivieren, Dateien behalten

**Voraussetzung:** Phase A wurde separat autorisiert, erfolgreich durchgeführt und reviewt.

**Wirkung:** Autostart deaktivieren; sämtliche App-, Konfigurations-, Zustands- und Wrapperdateien bleiben erhalten.

**Rollback:** Dienst erneut aktivieren, starten und die vorherigen Prüfungen wiederholen.

### Phase C — versionierte Runtimeflächen entfernen

**Voraussetzung:** Phase B ist stabil, und ein eigener PR zeigt den vollständigen Repository-Diff.

**Zielumfang:**

- `ops/bin/**`
- `ops/install/**`
- `ops/systemd/**`
- `ops/patches/**`
- Runtime-Manifest und appbezogene Installerprüfungen

Private Konfiguration, privater Zustand, Exportbelege und Restorebelege sind hiervon ausgeschlossen.

**Rollback:** PR-Revert beziehungsweise Wiederherstellung des letzten appgebundenen Repositorystands.

### Phase D — externe App-Binaries quarantänisieren

**Voraussetzung:** separate Retentionentscheidung nach stabiler Phase B/C.

**Wirkung:** externe App- und CLI-Binaries zunächst reversibel in Quarantäne verschieben; keine sofortige endgültige Löschung.

**Rollback:** quarantänisierte Pfade hashgebunden wiederherstellen.

Private Konfiguration und privater Zustand werden nicht automatisch mitbehandelt. Ihre spätere Archivierung oder Löschung benötigt eine eigene Klassifikation und Freigabe.

## Nicht Teil von T013

Die Repository-Umbenennung zu `heimgewebe/heimgewebe-katalog` bleibt T014. Selbst ein vollständig abgeschlossener Runtime-Rückbau benennt weder GitHub-Repository noch lokalen Checkout automatisch um.

## Erforderliche Autorisierungen

Die folgenden Wirkungen sind derzeit **nicht autorisiert**:

- begrenzter Dienst-Stopptest;
- dauerhafte Dienstdeaktivierung;
- Quarantäne oder Entfernung lokaler Runtime-Dateien;
- Entfernung versionierter Runtimeflächen;
- Änderung von Backup oder Retention;
- Löschung oder Verschiebung privater Daten;
- Repository-Rename.

## Muster für eine spätere Phase-A-Autorisierung

Das folgende Muster ist nur ein Formulierungsvorschlag und keine aktuelle Freigabe:

> Ich autorisiere ausschließlich T013 Phase A: einen zeitlich begrenzten Stopptest von `cabinet.service` mit unverändertem Daten- und Dateibestand sowie verpflichtendem Neustart-Rollback bei jedem Fehler. Diese Autorisierung umfasst weder Deaktivierung noch Dateiänderung, Löschung, Retentionänderung oder Repository-Rename.

Vor Ausführung muss dieses Mandat in Bureau ziel-, task- und wirkungsgebunden registriert werden.

## Noch offene Unsicherheit

- Ein registrierter Ort war im Consumer-Audit nicht erreichbar.
- Ein registrierter Ort war nur teilweise zurechenbar.
- Menschliche Cabinet-Nutzung wurde nicht direkt gemessen.

Diese Unsicherheit verhindert einen pauschalen Sofortabriss. Sie verhindert nicht die Vorbereitung eines begrenzten und vollständig reversiblen Stopptests.
