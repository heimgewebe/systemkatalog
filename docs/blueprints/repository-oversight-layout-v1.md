# Repository-Oversight-Layout v1

## Ziel

Cabinet wird zur lokalen, repoübergreifenden Arbeits- und Entscheidungsfläche. Git, Contracts, CI und überprüfbare Runtime-Ausgaben bleiben die fachlichen Sources of Truth. Cabinet hält datierte Karten, Befunde, Entscheidungen und Übergaben zusammen.

## Zielräume

### Bestand

Beantwortet: **Was existiert, wie hängt es zusammen und auf welchem belegten Stand?**

Enthält Repositorykarten, Projektkarten, Quellen, Beziehungen sowie Frische- und Provenienzangaben.

### Prüfung

Beantwortet: **Was ist belegt, widersprüchlich, veraltet oder fehlerhaft?**

Enthält Prüfläufe, Evidence Packs, Befunde, Widersprüche, Risiken und epistemische Leerstellen.

### Steuerung

Beantwortet: **Was wird entschieden und was geschieht als Nächstes?**

Enthält Lageübersicht, Entscheidungen, priorisierte Aufgaben, Blocker und Übergaben.

`steuerung` ist der Ziel-Default. Im Parallelbetrieb bleibt `vorzimmer` der technische Default, bis die lokale Workspace-Konfiguration gesichert und kontrolliert umgestellt wurde.

## Grenzen

- Maschinen dürfen Bestand und Prüfung vorbereiten.
- Befunde ohne Evidence bleiben Hinweise.
- Nur der Mensch bestätigt Entscheidungen und Aufträge.
- Cabinet-Agenten verändern keine Quell-Repositories automatisch.
- Externe Modelle erhalten nur freigegebene, redigierte Inputs.
- Private Repositoryinhalte bleiben lokal, solange keine ausdrückliche Freigabe vorliegt.

## Minimale Artefakte

1. **Repositorykarte** – Identität, Rolle, Quellen, Beziehungen, Commit und Frische.
2. **Projektkarte** – Ziel, Repositories, Stand, Blocker und nächste Aktion.
3. **Befund** – Beobachtung, Erwartung, Evidence, Schweregrad, Vertrauen und Status.
4. **Laufprotokoll** – Quellen, Commits, Modellprofil, tatsächliches Modell, Zeitpunkt und Ergebnis.
5. **Entscheidung oder Auftrag** – zunächst strukturiertes Markdown.

## Arbeitsfluss

```text
Quellen sammeln
→ Bestand aktualisieren
→ deterministisch prüfen
→ semantisch anreichern
→ Befunde deduplizieren
→ Mensch entscheidet
→ Auftrag mit Target-Proof übergeben
→ Ergebnis verifizieren
```

## Modellprofile

- `free-default`: Extraktion, Klassifikation, Zusammenfassung und begrenzter Claim-Code-Vergleich.
- `manual-deep-review`: nur nach menschlicher Freigabe.
- Keine automatische kostenpflichtige Eskalation.
- Jeder Lauf protokolliert Profil, Modell, Provider, Fallback, Quellen und Zeitpunkte.

## Legacy-Räume

| Bisher | Primärer Nachfolger |
|---|---|
| Vorzimmer | Steuerung |
| Heimgewebe | Bestand |
| Weltgewebe | Bestand |
| Werkstatt | Steuerung |
| Labor | Prüfung |
| Betrieb | Prüfung |

Bestehende Inhalte werden einzeln als `keep`, `move`, `split`, `archive` oder `delete` klassifiziert. Es gibt keine automatische Massenverschiebung.

## Phasen

1. Drei Zielräume parallel anlegen; alte Räume bleiben lesbar.
2. Lokale Workspace-Konfiguration sichern und kontrolliert auf `steuerung` umstellen.
3. Bestehende Repository References als Ausgangspunkt für Repositorykarten nutzen.
4. Deterministischen Sammler für freigegebene Repositories bauen.
5. Evidence-Pflicht, stabile Fingerprints und Hinweis/Bestätigt-Trennung einführen.
6. Lage und Aufträge aus validierten Artefakten erzeugen.
7. Alte Räume erst nach belegter Inhaltsmigration entfernen.
8. Automatisierung erst nach wiederholbaren manuellen Läufen aktivieren.

## Neubewertung

Die Dreiraumstruktur wird neu bewertet, wenn getrennte Benutzer, Vertraulichkeitsstufen, technisch erzwungene Agenten-Sandboxes oder stark abweichende Providerregeln entstehen.
