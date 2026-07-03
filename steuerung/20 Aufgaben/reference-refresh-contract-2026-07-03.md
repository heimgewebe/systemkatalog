# Reference Refresh Contract 2026-07-03

## Status

Task-Kandidat, nicht Ausführung.

## Ausgangslage

Vier Live-Prüfungen haben gezeigt: Repository-Kandidaten können gute Prüfhinweise sein, aber sie dürfen nicht direkt als Refresh, Repair oder Bureau-Auftrag ausgeführt werden.

## Ziel

Definiere einen kleinen Contract, wie ein geprüfter Live-Befund später in einen Reference-Refresh-Kandidaten überführt werden darf.

## Scope

- Eingabe: datierter Befund aus `pruefung/30 Befunde`.
- Eingabe: betroffene Repository Reference.
- Ausgabe: Refresh-Plan mit Belegen, Grenze und Stop-Kriterium.

## Organführung

- Prüfung bewertet den Befund.
- Steuerung entscheidet über den Plan.
- Bestand nimmt erst eine spätere geprüfte Aktualisierung auf.
- Bureau bleibt außen vor, solange kein eigenes Task-Artefakt freigegeben ist.

## Stop-Kriterien

- Kein Live-Beleg.
- Befund und Entscheidung sind vermischt.
- Die betroffene Reference-Quelle fehlt.

## Nachweis

Beispielplan mit Grenze liegt vor.
