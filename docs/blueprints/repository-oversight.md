# Repository Oversight Architecture

Mission: Repositoryübergreifende Übersicht, Konsistenzprüfung und vorbereitete Befunde mit Provenienz für menschlich freigegebene Aufträge an Coding-Agenten.

Nichtziele:
- Automatische Umbenennung, Löschung oder Aktivierung von Räumen.
- Änderung von Providern, Modellen, Default-Room oder Runtime.
- Erzeugung von Jobs/Heartbeats oder produktive Schemas.
- Automatische Umsetzung von Befunden ohne menschliche Freigabe.

Rollen:
- Sammler: Deterministisch, verifiziert Git-State, Commit-Hashes, Dateipfade.
- Prüfer: Strukturierter Befund mit Provenienz, Scope, Risiko und Target-Proof.
- Moderator: Menschliche Freigabe für Coding-Aufträge.
- Operator: Wartung von Räumen, Repository Reference.md und Wartungsjobs.

Sources of Truth:
- Git: Code, Historie, Working Tree, Branch.
- Repository Reference.md: Repositoriekarte mit Provenienz.
- policy/cabinet-layout.json: Raum- und Namensregeln.
- CI: Integrität und Vertrag.

Beobachtungsfluss:
1. Deterministische Sammlung: Repository-State, Dateipfade, CI-Status, Commit-Hashes, Dump-Frische.
2. Semantische Prüfung (ggf. durch kleines Modell): Claim vs. Code, Roadmap vs. Implementierung, widersprüchliche Dokumentation.
3. Befund: Bestätigter Befund + betroffene Dateien + Belege + Scope + Risiko + Stop-Kriterium + erwarteter Target-Proof.
4. Übergabe: Markdown-Auftrag mit Owner, Produzent, Consumer, Validierungszeitpunkt, Fehlerverhalten, Migrationsstrategie.
5. Freigabe: Mensch prüft und gibt Coding-Auftrag frei.

Deterministische Aufgaben (ohne LLM):
- Repository und Remote Commit, Branch, Working Tree.
- Datei vorhanden/nicht vorhanden, JSON/YAML-Syntax.
- CI-Zustand, Pfade, IDs, Pflichtfelder, Finding-Fingerprints, Hashes, Provenienz.

Semantische Aufgaben (kleine kostenlose Modelle):
- Extraktion und Klassifikation, Zusammenfassung, begrenzter Claim-Code-Vergleich, Gruppierung ähnlicher Befunde, Benennung fehlender Informationen.
- Keine Architekturfreigabe, Sicherheitsfreigabe, Mergefreigabe, Contractänderung, irreversible Migration oder Produktionsänderung durch Modell.

Evidenzmodell:
- Befundstruktur: Top-Level-Typen `Repository-Karte`, `Projekt-Karte`, `Befund`, `Laufprotokoll`.
- Repository-Karte: In `Repository Reference.md` verankert, Provenienz, Identität, Beleg.
- Projekt-Karte: Markdown mit Zielen, beteiligten Repositories, Stand, Blockern, Risiken, nächster Aktion, offenen Entscheidungen.
- Befund: Strukturiert mit Belegen, betroffenen Repositories/Dateien, Scope, Risiko, Stop-Kriterium, Target-Proof.
- Laufprotokoll: Strukturiert mit Zeitpunkt, Quellen, Hash, Modellprofil, Requested/Actual Model, Provider, Fallback.

Frischemodell:
- Snapshot-Zeitpunkt und aktueller Commit getrennt dokumentieren.
- `aktueller Git-Baum > älterer Dump`.

Datenschutzklassen:
- Öffentlich extern verarbeitbar: öffentliche Repositories, redigierte Diffs, öffentliche CI-Ergebnisse, Safe Exports.
- Nur lokal verarbeitbar: private Repositories ohne Freigabe, lokale Pfade, persönliche Notizen, Runtime-Konfiguration, vollständige Logs, Datenbankinhalte, Agentengespräche.
- Strikt verboten für externe Modelle: Tokens, Schlüssel, Passwörter, `.env`, private Schlüssel, Daemon-Tokens, Cookies, unredigierte Dumps, unredigierte Runtime-Logs.

Modellprofile:
- `free-default`: Kleine kostenlose Modelle für Extraktion, Klassifikation, Zusammenfassung, Claim-Code-Vergleich.
- `manual-deep-review`: Manuelle tiefere Prüfung durch Menschen bei Bedarf.
Keine automatische kostenpflichtige Eskalation.
Protokollpflicht: `requested_profile`, `requested_model`, `actual_model`, `provider`, `fallback_used`, `input_sources`, `started_at`, `completed_at`. Fehlt `actual_model`, gilt Lauf als Blocker für automatische semantische Läufe.

Kostenbegrenzung:
- Bevorzugte Modelle: `free-default`.
- Eskalation nur manuell und dokumentiert.
- Keine automatischen Modellläufe ohne reproduzierbare manuelle Vorläufe.

Befundlebenszyklus:
1. Entdeckung (deterministisch)
2. Anreicherung (semantisch, lokal)
3. Prüfung (menschlich)
4. Freigabe (Auftrag)
5. Umsetzung (externe Coding-Agenten)
6. Verifikation (Target-Proof)
7. Schließung (Archiv, Snapshot)

Spätere Projektmanagementfähigkeit:
- Projektkarten bleiben Markdown mit stabiler Struktur, bis ein nachgewiesener Bedarf für YAML/Schemas besteht.
- Entscheidungen und Aufträge bleiben Markdown; erst bei wiederholtem strukturellen Bedarf Schema prüfen.
- Kein Contract ohne legitimen Consumer, Owner, Produzent und Fehlerverhalten.

Empfohlene Raumarchitektur: Variante B — Wenige funktionale Räume.
Begründung:
- Aktuelle Struktur trennt Bedeutungsräume (Heimgewebe/Weltgewebe) und Arbeitsregime (Werkstatt/Labor/Betrieb) mit Vorzimmer als Eingang.
- Eine Zusammenfassung in einen zentralen Raum (Variante A) würde Kontext verschmieren; separate Repositorieräume (Variante C) erzeugen redundante Pflege und Drift.
- Cabinet als reine Oberfläche (Variante D) würde vorhandene Markdown-Struktur überflüssig machen.
- Hybrid (Variante E) erfordert kluge Grenzen, die bisher nicht belegt sind.
Faustregel: Neue Räume nur bei echten technischen, datenschutzbezogenen oder organisatorischen Grenzen. Drift vermeiden durch klare Zuordnung:
- Vorzimmer: Eingang, Klärung, Verteilung.
- Heimgewebe: Contracts, Kohärenz, Governance.
- Weltgewebe: Produkt, Architektur.
- Werkstatt: Bau, Test, Abnahme.
- Betrieb: Lauf, Wartung, Incidents.
- Labor: Experimente, Hypothesen, Replikation.

Verworfene Alternativen:
- Variante A: Zentraler operativer Raum. Verwurf: geringe Navigationsqualität, hohe Tokenlast, weniger klare Zuordnung.
- Variante C: Repositoryräume. Verwurf: hoher Pflegeaufwand, Duplikation von Struktur, erschwert repoübergreifende Prüfung.
- Variante D: Cabinet nur Oberfläche. Verwurf: existierende wertvolle Markdown-Struktur würde ungenutzt bleiben.
- Variante E: Hybrid. Verwurf: Grenzen müssen erst belegt werden; aktuell nicht nachgewiesen.

Risiken der Empfehlung:
- Erweiterung des Repository-Scopes erfordert disziplinierte Befundstruktur.
- Modell-/Providerbindung bleibt epistemische Leerstelle ohne Runtime-Zugriff.
- Spätere Automatisierung braucht stabile Fingerprints und bewiesene manuelle Läufe.

Bedingungen für Neubewertung:
- Änderung der Anzahl öffentlicher Repositories um >50 %.
- Nachweisbare technische Grenze zwischen privaten und öffentlichen Daten in Cabinet.
- Einführung stabiler Modellprofile mit messbarem Verbrauch.
- Neue Validierungsregeln in CI oder Policy.

Sicherheitsinvarianten:
1. Kein automatischer Schreibzugriff auf Quell-Repositories.
2. Keine automatische Modell-Eskalation.
3. Keine externen Modellläufe mit unredigierten lokalen Daten.
4. Jeder bestätigte Befund hat Provenienz.
5. Entscheidungen brauchen menschliche Bestätigung.
6. Migrationen bleiben rückrollbar.
7. Health-Pässe beweisen keine fachliche Korrektheit.
8. Kein Contract ohne legitimen Consumer.
9. Runtime-Konfiguration bleibt aus Git ausgeschlossen.
10. Kosten- und Laufgrenzen werden vor Automatisierung technisch erzwungen.