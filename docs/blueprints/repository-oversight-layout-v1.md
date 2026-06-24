# Repository-Oversight-Layout v1

## Ziel

Cabinet wird zur lokalen, repoübergreifenden Arbeits- und Entscheidungsfläche.
Es hält datierte Beobachtungen, Repository- und Projektkarten, Befunde,
Entscheidungen und Übergaben zusammen. Git, Contracts, CI und überprüfbare
Runtime-Ausgaben bleiben die fachlichen Sources of Truth.

## Aktive Räume

### Bestand

Frage: **Was existiert, wie hängt es zusammen und auf welchem belegten Stand?**

Enthält:

- Repositorykarten
- Projektkarten
- Quellenregister
- Beziehungen zwischen Repositories und Vorhaben
- Frische- und Provenienzangaben

### Prüfung

Frage: **Was ist belegt, widersprüchlich, veraltet oder fehlerhaft?**

Enthält:

- Prüfläufe
- Evidence Packs
- Befunde
- Widersprüche
- Risiken und epistemische Leerstellen

### Steuerung

Frage: **Was wird entschieden und was geschieht als Nächstes?**

Enthält:

- Lageübersicht
- Entscheidungen
- priorisierte Aufgaben
- Blocker
- Übergaben an Coding- und Diagnoseagenten

`steuerung` ist der Default-Room.

## Eigentumsgrenzen

- Maschinen dürfen Bestand und Prüfung vorbereiten.
- Befunde ohne Evidence bleiben Hinweise.
- Nur der Mensch bestätigt Entscheidungen und Aufträge.
- Cabinet-Agenten verändern keine Quell-Repositories automatisch.
- Externe Modelle erhalten nur freigegebene, redigierte Inputs.
- Private Repositoryinhalte bleiben lokal, solange keine ausdrückliche
  Freigabe vorliegt.

## Minimale Artefakte

1. **Repositorykarte** – Identität, Rolle, Quellen, Beziehungen, Commit und Frische.
2. **Projektkarte** – Ziel, beteiligte Repositories, Stand, Blocker und nächste Aktion.
3. **Befund** – Beobachtung, Erwartung, Evidence, Schweregrad, Vertrauen und Status.
4. **Laufprotokoll** – Quellen, Commits, Modellprofil, tatsächliches Modell,
   Zeitpunkt und Ergebnis.
5. **Entscheidung/Auftrag** – zunächst strukturiertes Markdown; ein Schema folgt
   erst bei nachgewiesenem maschinellem Consumer.

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

## Modellstrategie

- `free-default`: Extraktion, Klassifikation, Zusammenfassung und begrenzter
  Claim-Code-Vergleich.
- `manual-deep-review`: nur nach menschlicher Freigabe.
- Keine automatische kostenpflichtige Eskalation.
- Jeder Lauf protokolliert angefordertes Profil, angefordertes und tatsächliches
  Modell, Provider, Fallback, Quellen und Zeitpunkte.

## Legacy-Räume

Die bisherigen sechs Räume bleiben während der Übergangsphase erhalten, sind
aber keine Zielorte für neue Arbeit. Ihre primären Nachfolger sind:

| Legacy-Raum | Primärer Nachfolger |
|---|---|
| Vorzimmer | Steuerung |
| Heimgewebe | Bestand |
| Weltgewebe | Bestand |
| Werkstatt | Steuerung |
| Labor | Prüfung |
| Betrieb | Prüfung |

Bestehende Inhalte werden später einzeln als `keep`, `move`, `split`, `archive`
oder `delete` klassifiziert. Es gibt keine automatische Massenverschiebung.

## Migrationsphasen

1. **Parallelstruktur:** drei neue aktive Räume anlegen; Legacy-Räume bleiben lesbar.
2. **Lokaler Cutover:** Workspace-Konfiguration auf `steuerung` umstellen und
   lokalen Layout-Guard ausführen.
3. **Repository- und Projektkarten:** bestehende Repository References als
   Ausgangspunkt verwenden; keine zweite Wahrheit erzeugen.
4. **Deterministischer Sammler:** zunächst nur freigegebene Repositories und
   Delta-Analysen.
5. **Prüfung:** Evidence-Pflicht, stabile Fingerprints und Hinweis/Bestätigt-Trennung.
6. **Steuerung:** Lage, Entscheidungen und Aufträge aus validierten Artefakten.
7. **Legacy-Räumung:** erst nach belegter Inhaltsmigration und Rückrollprobe.
8. **Automatisierung:** erst nach wiederholbaren manuellen Läufen ohne Secret-Leak
   oder unkontrollierten Schreibzugriff.

## Neubewertung

Die Dreiraumarchitektur wird neu bewertet, wenn mindestens eine echte Grenze
entsteht, die sie nicht abbildet: getrennte Benutzer, getrennte
Vertraulichkeitsstufen, technisch erzwungene Agenten-Sandboxes oder stark
abweichende Providerregeln.
