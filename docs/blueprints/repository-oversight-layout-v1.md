# Repository Oversight Layout v1

## Ziel

Cabinet wird zur lokalen, repo-uebergreifenden Arbeitsflaeche. Git, Contracts, CI und pruefbare Runtime-Ausgaben bleiben die primaeren Quellen. Cabinet haelt datierte Karten, Hinweise, Entscheidungen und Uebergaben zusammen.

## Zielraeume

### Bestand

Beantwortet: Was existiert, wie haengt es zusammen und auf welchem Stand?

Enthaelt Repositorykarten, Projektkarten, Quellen und Beziehungen.

### Pruefung

Beantwortet: Was ist belegt, widerspruechlich, veraltet oder fehlerhaft?

Enthaelt Laeufe, Belege, Hinweise, Risiken und offene Fragen.

### Steuerung

Beantwortet: Was wird als Naechstes bearbeitet?

Enthaelt Lage, Aufgaben, Blocker und Uebergaben.

`steuerung` ist der Ziel-Default. Im Parallelbetrieb bleibt `vorzimmer` der technische Default, bis die lokale Workspace-Konfiguration gesichert und kontrolliert umgestellt wurde.

## Grenzen

- Maschinen duerfen Bestand und Pruefung vorbereiten.
- Hinweise ohne Beleg bleiben Hinweise.
- Nur der Mensch bestaetigt Entscheidungen und Auftraege.
- Cabinet veraendert keine Quell-Repositories automatisch.
- Externe Modelle erhalten nur freigegebene und redigierte Inputs.
- Private Repositoryinhalte bleiben lokal, solange keine Freigabe vorliegt.

## Minimale Artefakte

1. Repositorykarte: Identitaet, Rolle, Quellen, Beziehungen, Commit und Frische.
2. Projektkarte: Ziel, Repositories, Stand, Blocker und naechste Aktion.
3. Befund: Beobachtung, Erwartung, Beleg, Schweregrad, Vertrauen und Status.
4. Laufprotokoll: Quellen, Commits, Modellprofil, tatsaechliches Modell, Zeit und Ergebnis.
5. Entscheidung oder Auftrag: zunaechst strukturiertes Markdown.

## Arbeitsfluss

```text
Quellen sammeln
-> Bestand aktualisieren
-> deterministisch pruefen
-> semantisch anreichern
-> Hinweise deduplizieren
-> Mensch entscheidet
-> Auftrag mit Target-Proof uebergeben
-> Ergebnis verifizieren
```

## Modellprofile

- `free-default`: Extraktion, Klassifikation, Zusammenfassung und begrenzter Claim-Code-Vergleich.
- `manual-deep-review`: nur nach menschlicher Freigabe.
- Keine automatische kostenpflichtige Eskalation.
- Jeder Lauf protokolliert Profil, Modell, Provider, Fallback, Quellen und Zeitpunkte.

## Legacy-Raeume

| Bisher | Primaerer Nachfolger |
|---|---|
| Vorzimmer | Steuerung |
| Heimgewebe | Bestand |
| Weltgewebe | Bestand |
| Werkstatt | Steuerung |
| Labor | Pruefung |
| Betrieb | Pruefung |

Bestehende Inhalte werden einzeln als `keep`, `move`, `split`, `archive` oder `delete` klassifiziert. Es gibt keine automatische Massenverschiebung.

## Phasen

1. Drei Zielraeume parallel anlegen; alte Raeume bleiben lesbar.
2. Lokale Workspace-Konfiguration sichern und kontrolliert auf `steuerung` umstellen.
3. Bestehende Repository References als Ausgangspunkt fuer Repositorykarten nutzen.
4. Deterministischen Sammler fuer freigegebene Repositories bauen.
5. Belegpflicht, stabile Fingerprints und Hinweis-Bestaetigt-Trennung einfuehren.
6. Lage und Auftraege aus validierten Artefakten erzeugen.
7. Alte Raeume erst nach belegter Inhaltsmigration entfernen.
8. Automatisierung erst nach wiederholbaren manuellen Laeufen aktivieren.

## Neubewertung

Die Dreiraumstruktur wird neu bewertet, wenn getrennte Benutzer, Vertraulichkeitsstufen, technisch erzwungene Agenten-Sandboxes oder stark abweichende Providerregeln entstehen.
