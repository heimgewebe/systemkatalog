# Cabinet Runtime Retirement — Cutover- und Rollbackvertrag v1

Status: **T013 Runtime-Cutover umgesetzt; externe Workspace-Runtime retired**

Bureau-Task: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013`

Ausgangsbeleg: [cabinet-runtime-retirement-preflight-v1.json](cabinet-runtime-retirement-preflight-v1.json)

## Ergebnis

Die externe Cabinet AI Workspace App ist nicht mehr Bestandteil des aktiven Repository- oder Dienstvertrags. An ihre Stelle tritt `heimgewebe-systemkatalog.service`: eine zustandslose, read-only Python-Projektion der versionierten Katalogquellen.

Der Cutover umfasst:

- alten Node-/Next-App-Dienst stoppen und deaktivieren;
- alten Daemon und dessen zweiten Listener aus dem aktiven Vertrag entfernen;
- App-Starter, Session-Wrapper, Security-Gate und Dark-Theme-Patch aus dem Repository entfernen;
- Secret- und Provider-Environment aus der Katalogruntime entfernen;
- neue Loopback-Oberfläche auf dem bisherigen sichtbaren Port bereitstellen;
- `cabinet.service` ausschließlich als Kompatibilitätsalias der neuen Unit erhalten;
- alte aktive Startflächen vor dem Cutover lokal sichern.

## Neue Runtime

- Unit: `heimgewebe-systemkatalog.service`
- Alias: `cabinet.service`
- Implementierung: Python-Standardbibliothek
- Zustand: read-only und zustandslos
- Canon: `policy/system-catalog.v1.json` und `registry/ecosystem/**`
- HTML: `/`
- JSON: `/api/catalog.json`
- Health: `/healthz`

## Erhaltene Altbestände

Der Runtime-Cutover löscht keine privaten App-, Konfigurations-, Evidence-, Backup- oder Restorebestände. Sie bleiben außerhalb des Katalogkanons für Rückfall, Klassifikation oder spätere Retentionentscheidungen erhalten.

Insbesondere sind nicht automatisch Teil des Cutovers:

- private Konfiguration;
- private Datenbanken und App-Zustände;
- verschlüsselte Sicherungs- und Restorebelege;
- historische Preflight-Evidence;
- endgültige Löschung externer App-Binaries.

## Rollback

Der Installer sichert vorhandene Units und Bedienwerkzeuge vor dem Cutover unter `~/.local/state/cabinet/runtime-cutovers/`. Der Git-Rückweg ist der Revert des Cutover-Commits. Private Altbestände werden nicht überschrieben.

## Noch getrennt

Die Umbenennung des GitHub-Repositories und aller Referenzen zu `heimgewebe/heimgewebe-katalog` bleibt T014. Der Runtime-Cutover allein ändert weder Repositoryname noch lokalen Checkoutpfad.

## Nicht-Claims

Dieser Beleg beweist nicht:

- aktuelle Runtime-Gesundheit zu jedem späteren Zeitpunkt;
- vollständige Abwesenheit unbekannter Remote-Consumer;
- Erlaubnis zur Löschung privater Daten oder Backups;
- Retention-, Forget- oder Prune-Erlaubnis;
- abgeschlossene Repository-Umbenennung.
