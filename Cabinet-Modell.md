# Cabinet-Modell

Cabinet ist eine lokale, repoübergreifende Arbeits- und Entscheidungsfläche.
Es ersetzt keine fachliche Source of Truth, sondern verbindet datierte Beobachtungen, Befunde, Entscheidungen und Übergaben.

## Zielräume

- **Bestand** beantwortet: Was existiert, wie hängt es zusammen und auf welchem belegten Stand?
- **Prüfung** beantwortet: Was ist belegt, widersprüchlich, veraltet oder fehlerhaft?
- **Steuerung** beantwortet: Was wird entschieden und was geschieht als Nächstes?

Git, Contracts, CI und überprüfbare Runtime-Ausgaben bleiben die primären Quellen. Cabinet speichert datierte Karten, Befunde und Arbeitsverweise.

Die bisherigen Räume bleiben während der Parallelphase lesbar. Neue Arbeit wird schrittweise in die drei Zielräume überführt. `vorzimmer` bleibt bis zum kontrollierten lokalen Cutover der technische Default.
