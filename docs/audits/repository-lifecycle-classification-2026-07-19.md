# Repository-Lifecycle-Klassifikation – 19. Juli 2026

**Beobachtet:** 2026-07-19T13:54:06+02:00

**Autorität:** Diagnose und Aufgabenplanung; keine Archivierungsfreigabe.

## Ergebnis

Die Organisation besitzt **35 Repositories**, davon **0 archiviert**. Die fünf auffälligen Systeme wurden gegen Katalogrolle, Runtime, Consumer, Verträge, Pull Requests und Migrationsfolgen geprüft.

| Repository | Zielrolle | Entscheidung | Grund |
|---|---|---|---|
| Heimlern | historische Referenz | Archivkandidat, blockiert | Keine Runtime, aber vendete HausKI-Bibliotheken, Metarepo-Verträge und deprecated Ingest-Kompatibilität bleiben. |
| Leitwerk | normative Referenz | Archivkandidat, blockiert | Keine Runtime; normative Inhalte und Guard-Workflows müssen zuerst eingefroren werden. |
| Heimgeist | Migrationskompatibilität | behalten | Plexer, Chronik, Leitstand und WGX konsumieren Heimgeist-Semantik noch aktiv. |
| Agent Control Surface | manuelle Kompatibilitäts-GUI | behalten | Leitstand-Consumer und aktivierter Heimserver-Tunnel verhindern Stilllegung. |
| SemantAH | aktiver Semantikprovider | aktiv behalten | Jüngster Merge am 18. Juli, 17 Workflows, laufender Workspace und stabile HausKI-Kante. |

## Archivierungsfolgen

- `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T036`: Heimlern nach Kompatibilitäts-Freeze archivieren.
- `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T037`: Leitwerk nach Normativitäts-Freeze archivieren.
- Heimgeist, ACS und SemantAH bleiben in `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T034`; keine Doppelqueue.

## Abhängigkeiten

### Heimlern

Die README und der Systemkatalog bezeichnen Heimlern ausdrücklich als eingefrorene beziehungsweise stillgelegte Referenz. Das reicht noch nicht zur sofortigen Archivierung: HausKI enthält vendete Heimlern-Crates, Metarepo besitzt normative Heimlern-Verträge, Grabowski bewahrt eine Offline-Lerngrenze und Aussensensor dokumentiert noch einen deprecated Direktpfad. Diese Flächen müssen nicht gelöscht werden, aber ihre Unabhängigkeit vom GitHub-Repository muss vor Archivierung bewiesen sein.

### Leitwerk

Leitwerk besitzt keine Runtime und keine aktuelle Task-, Claim- oder Mergeautorität. Der Systemkatalog weist diese Zuständigkeiten Bureau, Grabowski und Konvergenzregelkreis zu. Vor Archivierung müssen die noch maßgeblichen Grenzdokumente in eine kanonische Referenz überführt und die repository-lokalen Guards terminal klassifiziert werden.

### Heimgeist und ACS

Beide sind keine sofortigen Archivkandidaten. Heimgeist bleibt im Legacy-Plexerpfad ein kritischer Consumer und wird von Chronik, Leitstand und WGX semantisch verarbeitet. ACS bleibt optionaler Leitstand-Datenlieferant; `acs-tunnel.service` ist weiterhin aktiviert und auf Heimserver gerichtet. T034 besitzt diese Consumermigration.

### SemantAH

SemantAH ist aktiv. Die Standalone-Rolle darf später enger werden, aber eine Archivierung würde gegen laufende Entwicklung, aktive Workspaces und die stabile Providerbeziehung zu HausKI verstoßen.

## Alte Dependabot-PRs

- HausKI: **15** offene alte PRs, 6. April bis 11. Mai 2026.
- HausKI-Audio: **7** offene alte PRs, 2. März bis 20. April 2026.
- Metarepo: **2** PRs vom 14. Juli 2026; nicht als alt klassifiziert.

`OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T038` bündelt Rebase-, Ersetzungs-, Konflikt- und Schließungsentscheidungen. Die bloße Alterung eines Dependency-PR beweist weder Mergefähigkeit noch Stilllegungsreife des Repositories.

## Belegbindung

Repositorybelege sind an konkrete Commit- und Dateireferenzen im maschinenlesbaren Audit gebunden. Wo lokale Hauptcheckouts hinter `origin/main` lagen oder fremd dirty waren, wurde ausdrücklich der aktuelle Remote-main-Commit verwendet. Livebelege für systemd und tmux gelten nur für den Prüfzeitpunkt auf heim-pc.

## Grenze

Dieser Audit archiviert kein Repository. Jede spätere Archivierung benötigt einen eigenen ressourcenspezifischen Task, einen frischen Consumer- und PR-Readback sowie eine Aktualisierung von Systemkatalog, Bureau-Ressource und Organisationsprojektion.
