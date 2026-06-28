# Legacy-Room-Visibility-Cutover v1

## Versionierter Zustand

Die Navigation unterscheidet drei aktive Räume von sechs erhaltenen Legacy-Sammlungen.

Aktive Räume:

- `bestand`
- `pruefung`
- `steuerung`

Die Verzeichnisse Vorzimmer, Heimgewebe, Weltgewebe, Werkstatt, Labor und Betrieb bleiben erhalten. Ihre `.cabinet`-Dateien verwenden `kind: legacy-collection`, damit sie nicht mehr als aktive Räume erkannt werden.

## Prüfung

```bash
python3 scripts/check-cabinet-layout.py --mode repository .
python3 -m unittest discover -s scripts/tests -p 'test_phase4_*.py'
```

Der Validator gleicht Layout, Navigation, Registry und alle neun Manifestpfade ab. Eine fehlende Sammlung, ein widersprüchlicher Nachfolger oder `kind: room` in einer Legacy-Sammlung führt zum Fehler.

## Lokale Verifikation

Nach dem Aktualisieren des lokalen Repositories sind der lokale Layout-Check, ein Neustart des Cabinet-Dienstes und eine Sichtprüfung der Oberfläche erforderlich. Ein Repositorytest allein belegt nicht, welche Räume eine bereits laufende Instanz anzeigt.

## Inhaltsmigration

Dieser Sichtbarkeitsschritt verschiebt und löscht keine Fachinhalte. Einzelne Dateien werden weiterhin anhand belegter Links und Consumer als `keep`, `move`, `split`, `archive` oder `delete` klassifiziert.
