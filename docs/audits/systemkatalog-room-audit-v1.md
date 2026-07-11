# Komplettaudit der früheren Cabinet-Räume

Datum: 2026-07-11

## Urteil

Die Raumstruktur war als visuelle Ordnung für die externe Cabinet-App nachvollziehbar. Nach deren Stilllegung wurde sie jedoch zu einer zweiten, konkurrierenden Informationsarchitektur neben dem Systemkatalog. Deshalb wurde sie aus der aktiven Repositoryoberfläche entfernt.

## Bewertungsmaßstab

- **Lassen:** stabiler, quellengebundener Kataloginhalt.
- **Ändern:** nützlicher Inhalt mit falscher Ablage oder falscher Zuständigkeit.
- **Archivieren:** historischer Beleg ohne aktive Produktrolle.
- **Entfernen:** leeres Gerüst, Doppelmodell oder operative Funktion außerhalb der Katalogrolle.

## Befund nach Bereich

| Bereich | Befund | Entscheidung |
|---|---|---|
| `bestand` | generierte Repositorylisten und Projektkarten; wechselnder Bestand | archivieren; stabile Systeme in die Registry überführen |
| `pruefung` | dated Scans, Gemini-Läufe, Snapshot- und Reviewbelege | archivieren; aktuelle Prüfungen bleiben bei CI, GitHub und Review-Gates |
| `steuerung` | Aufgaben, Kandidaten, Beobachtung und Organkarten | archivieren; Aufgaben und Queue gehören Bureau |
| `vorzimmer` | überwiegend leeres Eingangs- und Klärungsgerüst | archivieren, nicht aktiv fortführen |
| `heimgewebe` | überwiegend leere Architektur-, Contract- und Übergabeordner | archivieren; stabile Semantik in Registry/Policy |
| `weltgewebe` | leere Produktstruktur plus Repositoryreferenz | archivieren; Produktwahrheit bleibt im Weltgewebe-Repo |
| `werkstatt` | Werkzeugordner und Repositoryreferenzen | archivieren; Werkzeugwahrheit bleibt in den jeweiligen Repos |
| `labor` | Versuchsgerüste und Vibe-Lab-Referenz | archivieren; Experimente bleiben Vibe-Lab |
| `betrieb` | Host-, Dienst-, Runbook- und Incident-Gerüste | archivieren; Livebetrieb bleibt Runtime/Infra/Logs |

## Was aktiv bleibt

- die kanonische Systemregistry;
- stabile Beziehungen;
- Wahrheitszuständigkeiten;
- belegte stabile Claims;
- deterministische Leseansicht und Karte;
- der read-only Karten-Übergabevertrag für Leitstand und Schauwerk;
- die lokale zustandslose Leseoberfläche.

## Was aktiv entfällt

- Raum-Metadaten und Default-Room;
- Projektkarten und Repository-Snapshot-Duplikate;
- Cabinet-Radar, Frontier und Live-Signalmodelle;
- Gemini-Wartungsläufe im Katalogrepo;
- Aufgaben- und Kandidatenmodelle;
- handgepflegte Zweitkarten;
- aktive Cabinet-App-, Agenten- und Schedulerflächen.

## Folgen

Der aktive Root zeigt jetzt nur die tatsächliche Produktarchitektur. Historische Belege bleiben nachvollziehbar, können aber nicht mehr versehentlich als aktueller Zustand oder als zweiter Kanon gelesen werden.
