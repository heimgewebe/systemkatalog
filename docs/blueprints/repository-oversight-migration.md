# Repository Oversight Migration Plan

Mapping bisheriger Raumfunktionen:
- Vorzimmer: Eingang, Klärung, Verteilung
- Heimgewebe: Contracts, Kohärenz, Governance
- Weltgewebe: Produkt, Architektur
- Werkstatt: Bau, Test, Abnahme
- Betrieb: Lauf, Wartung, Incidents
- Labor: Experimente, Hypothesen, Replikation

Mapping relevanter Configdateien:
- policy/cabinet-layout.json: Raum-IDs, defaultRoom, Namensverbote
- .home/home.json: defaultRoom, lastActiveRoom
- .cabinet (pro Raum): Raumidentifikation
- Repository Reference.md: Repositorykarten
- .gitignore: local-only Ausschlüsse bleiben unverändert
- ops/manifest.json: Installation bleibt unverändert

Zu erhaltende Inhalte:
- Räumliche Struktur mit Operating Rules und Sources of Truth
- Bestehende Repository Reference.md (weltgewebe, werkstatt, labor)
- CABINET-Modell-Semantik als Dokumentation
- policy/cabinet-layout.json als Vertrag
- .home/home.json als lokale Heimsteuerung

Zu archivierende Platzhalter:
- Veraltete oder leere Indexdateien ohne Inhalt werden als historische Platzhalter archiviert
- Versuchsstände ohne aktive Relevanz werden in Labor/80 Verworfen oder Archiv verschoben

Nicht zu migrierende Runtimeoberflächen:
- .agents/.runtime, .conversations, .memory, .messages
- .agents/.config und workspace.json
- .cabinet.db und WAL/SHM Dateien
- Systemd-Unit unter ~/.config/systemd/user/cabinet.service*
- Lokale Binaries unter ~/.local/bin/cabinet*
- Runtime.env unter ~/.config/cabinet/runtime.env

Abhängigkeiten:
- Scheduler bleibt deaktiviert bis Slice F
- Modellprofile müssen technisch nachweisbar sein vor Slice E
- CI-Validierung muss vor jedem Migrationstep grün sein
- Repo-Scope-Änderung >50 % erzwingt Neubewertung der Architektur

Gestufte Migrationsphasen:
- Slice A (dieser PR): Audit und Zielentscheidung
- Slice B: Zielstruktur parallel testen; alte Struktur bleibt aktiv
- Slice C: Deterministischer Sammler; zunächst 1-3 öffentliche Repos
- Slice D: Minimale Artefakte und Validator; nur nachgewiesene Typen
- Slice E: Ein begrenzter Modellagent; genau ein Repository, manuell
- Slice F: Zweite Prüfrolle und Deduplizierung; Evidence-Pflicht
- Slice G: Übersicht und menschlich freigegebene Aufträge; keine automatische Umsetzung
- Slice H: Migration alter Struktur; erst nach bewiesenem Zielbetrieb
- Slice I: Automatisierung; erst nach reproduzierbaren manuellen Läufen

Stop-Gates:
- Exit wenn lokale Configs committed werden sollen
- Exit wenn Runtime-Dateien moved oder versioniert werden sollen
- Exit wenn Secrets oder Tokens in Docs auftauchen
- Exit wenn CI-Validierung fehlschlägt
- Exit wenn Modellanbieter automatisch eskaliert werden soll

Rollback:
- Jeder Slice bleibt isoliert reversibel durch Branch-Revert
- Alte Räume bleiben bis Slice H erhalten
- Neue Struktur wird parallel betrieben; keine Löschung vor Slice H
- Im Fehlerfall: Feature-Branch löschen, main bleibt unverändert
- Dokumentiere Rollback-Trigger und -Schritte pro Slice

Testmatrix:
- CI: validate-repository.sh besteht
- CI: test-validate-repository.sh besteht
- CI: test-install-local-runtime.sh besteht (wenn Runtime vorhanden)
- Gitleaks-Check besteht
- Keine Lokalpfade in Diffs außerhalb erlaubter Ausnahmen
- Keine Runtime-Mutationen in Diffs
- Modellprofil-Protokollierung prüfbar

Folge-PRs:
- PR Repository Oversight Slice B
- PR Repository Oversight Slice C
- PR Repository Oversight Slice D
- PR Repository Oversight Slice E
Jeweils als Draft-PR mit eigenem Audit, Zielsetzung und Testmatrix.

Kein Big Bang:
- Migration schrittweise, reversibel, mit paralleler Betriebsphase
- Alte Räume und neue Struktur koexistieren bis Slice H
- Keine automatische Übernahme von Inhalten ohne menschliche Prüfung