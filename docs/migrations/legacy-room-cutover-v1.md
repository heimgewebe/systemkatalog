# Legacy-Room-Visibility-Cutover v1

## Zweck

Dieser Cutover trennt Navigation von historischer Ablage.

Nur `bestand`, `pruefung` und `steuerung` sind aktive Cabinet-Räume. Die sechs alten Verzeichnisse bleiben vollständig versioniert und lesbar, besitzen aber kein `.cabinet`-Room-Manifest mehr.

## Sicherheitsprinzip

Der Cutover löscht keine Fachinhalte und verschiebt keine Datei automatisch. Er verändert ausschließlich die Raum-Erkennung und ergänzt maschinenlesbare Migrationsmarker.

Die Registry `legacy-room-cutover-v1.json` hält für jede Sammlung fest:

- stabiler alter Raum-Identifier;
- primärer Nachfolger;
- erhaltene Sinnachse;
- Sichtbarkeit;
- Inhaltsstatus;
- Pflicht zur dateiweisen Klassifikation.

## Folgearbeit

Jede Inhaltsdatei wird später anhand belegter Consumer und Links als `keep`, `move`, `split`, `archive` oder `delete` klassifiziert. Bis dahin bleibt der alte Pfad erhalten.

## Prüfung

```bash
python3 scripts/check-cabinet-layout.py --mode repository .
python3 -m unittest discover -s scripts/tests -p 'test_phase4_*.py'
```

Ein erfolgreicher Repositorytest belegt die Struktur des versionierten Snapshots. Er belegt nicht, dass eine bereits laufende lokale Cabinet-Instanz den neuen Baum ohne Neustart eingelesen hat.
