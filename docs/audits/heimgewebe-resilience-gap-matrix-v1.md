# Heimgewebe-Resilienz: Gap-Matrix v1

Status: commitgebundener Implementierungsaudit für `HEIMGEWEBE-RESILIENZ-V1-T001`
Beobachtungszeit: 2026-07-18, 02:00 Europe/Berlin
Systemkatalog-Basis: `96dabe02774b5159f79755c03a599d69424c58af`
Bureau-Registrierung: Commit `6b7dbe434c671761c0b56f455a135caf1500826b`, PR `heimgewebe/bureau#659`

## Zweck und Grenze

Dieser Audit entscheidet, **wo** die zehn geprüften Resilienzmechanismen hingehören, welche vorhandenen Mechanismen wiederverwendet werden und welche konkrete Lücke geschlossen werden muss. Er führt keinen neuen Livezustand ein und erteilt keine Ausführungs-, Merge-, Deploy- oder Recoveryautorität.

Die zentrale Regel lautet:

> Stabile Bedeutung gehört in den Systemkatalog; Verpflichtung und Kapazität in Bureau; Liveausführung und operative Ressourcen in Grabowski; Evidenzanforderungen in den Konvergenzregelkreis; Geschichte in Chronik; fachlicher Laufzustand in die jeweilige Runtime; Darstellung in Leitstand und Schauwerk; Wirkungsevaluation in Vibe-Lab.

## Livebefund

| Bereich | Beobachtung | Bedeutung | Epistemische Grenze |
|---|---|---|---|
| Grabowski-Runtime | gesund; Release `f1475fe9e5d6-srcset002297e50880-locke6664d600b6c-contractcb5d6d196ea7`; Repo-Head `f1475fe9e5d69e88bd80a85d9bff22a0392a951f`; Deployment, Artefaktintegrität und Audit gültig | Die Operatorbasis ist für kontrollierte Arbeit funktionsfähig. | Belegt nicht die Korrektheit einzelner zukünftiger Aktionen. |
| Audit und Recovery | 16.434 Auditdatensätze; lokales Restic-Backup frisch; Backup-Timer aktiv; Server-Restoreprobe `91cb9220` frisch; Recovery-Gate und Rootbroker bereit | Recoverytechnik existiert und ist derzeit verwendbar. | Ein frischer Recoverybeleg für Grabowski beweist keine Recovery anderer Systeme. |
| Connector | 141/141 Werkzeuge entsprechen dem Deploymentvertrag; Operator und Tunnel aktiv; keine Transportfehler im begrenzten Journalfenster | Der Transport ist aktuell nicht als Störung beobachtet. | Der Client-Snapshot ist serverseitig nicht beobachtbar; Runtimevertrag und tatsächliche Clientbindung bleiben getrennte Wahrheiten. |
| Taskzustand | nach Reconciliation: 0 `running`; 5.397 `completed`; 1.339 `failed`; 77 `interrupted`; 15 `timed_out`; 1 `signalled`; 0 `outcome_unknown` | Die Taskdatenbank kann terminale Zustände differenziert halten. | `attention=1.432` ist eine überlappende Projektion aus Fehlerzuständen, nicht die Zahl unabhängiger offener Aufgaben. |
| Projektionsverzug | Zwei als `running` gespeicherte Tasks wurden live als `completed` beobachtet und am 2026-07-18 um Unix `1784332584` terminalisiert; ihre Claims wurden freigegeben | Lebenszykluskonvergenz ist ein reales Betriebsproblem, kein abstraktes Modellthema. | Der Einzelbefund misst noch keine typische Verzögerungsverteilung. |
| Ressourcenclaims | 13 aktive Leases; darunter fremde Schreibclaims auf Grabowski und RepoGround sowie RepoGround-Runtime, Dienste und Port 8788 | Parallele Arbeit muss bestehende Ownership respektieren und vorhandene Implementierungen später als Evidenz wiederverwenden. | Aktive Lease bedeutet nicht automatisch aktive Prozessausführung; Freigabe braucht Eigentümer- oder terminalitätsgebundene Evidenz. |
| Fleet | fünf registrierte Ziele; `heim-pc`, `heimserver`, `heimberry` und Recoveryziel besitzen weiterhin Wildcard-Kommandoflächen; `wg-prod-1` ist enger begrenzt | Operator-Control und Hostzugang bilden gemeinsame Ausfalldomänen und Governance-Risiken. | Der Registry-Eintrag beweist keine gegenwärtige Erreichbarkeit oder konkrete Gefahr. |

## Bestehende Systemgrundlagen

- **Systemkatalog:** stabile Knoten, Beziehungen, Truth Ownership, Quellenbindungen und Frischeziele; ausdrücklich statusfrei.
- **Bureau:** Aufgaben, Abhängigkeiten, Claims, Capacity-Ressourcen, Reconciliation, Worktree-Lifecycle und revisiongebundene Receipts.
- **Grabowski:** typisierte Leases, Nichtkonfliktbeweise, Task-Reconciliation, Recovery-Gate, Rootbroker, Operator-Verpflichtungen und Auditkette.
- **Konvergenzregelkreis:** getrennte Observation-, Effect-, Verification- und Closure-Belege; R3 verlangt bereits Recovery und Cleanup.
- **Chronik:** append-only Ereignisachse, Provenienz, Qualitätsmarker und Retention.
- **Weltgewebe:** laufender HA- und Recovery-Pilot `WELTGEWEBE-OS-V1-T004`.
- **RepoGround:** laufender canary- und rollbackgebundener Runtime-Cutover; bestehende Claims verhindern Doppelarbeit.
- **Schauwerk und Leitstand:** Projektion ohne Wahrheitsübernahme.
- **Vibe-Lab:** geeigneter Ort für Wirkungsmessung und Rückbauentscheidungen, nicht für operative Autorität.

## Gap-Matrix

| Prinzip | Bereits vorhanden | Konkrete Lücke | Truth Owner der Ergänzung | Erster Beweis | Stop- oder Rückbaukriterium |
|---|---|---|---|---|---|
| 1. Antwortvielfalt | Backups, Rollback, Legacy-Cutover, R3-Recoverybeleg | Primär- und Recoverywege sind nicht systemweit inventarisiert; gemeinsame Fehlerursachen werden nicht klassifiziert | Systemkatalog für stabile Pfade und Abhängigkeiten; jeweilige Runtime und Grabowski für Livebeleg | Weltgewebe-Daten, Grabowski-Runtime, RepoGround-Cutover | Kein zweiter Weg wird gebaut, wenn er denselben Ausfall nur dupliziert oder nie getestet werden kann. |
| 2. Gesteuerte Vernetzung | stabile Kanten und Authority Matrix | Kanten kennen Kopplung, Ausfallpolitik, Nachholbarkeit und Autoritätsrichtung nicht maschinenlesbar | Systemkatalog | Grabowski → Chronik, Bureau → Grabowski, Systemkatalog → Schauwerk | Nur autoritäts- oder ausfallrelevante stabile Kanten erhalten Felder; interne Aufrufgraphen bleiben außen vor. |
| 3. Funktionskohärenz | Truth-Hierarchy; getrennte Systemeigentümer; Konvergenzphasen | Konfliktregeln sind verteilt und nicht durchgängig negativ getestet | Systemkatalog für Autoritätsdomänen; Konvergenzregelkreis für Übergangslogik; Consumer für Negativtests | Widerspruch zwischen Bureau-Abschluss, GitHub, Runtime und Chronik | Kein zentraler Orchestrator und kein zweites Statusmodell. |
| 4. Verfall und Regeneration | TTL-Leases, Reconciliation, Retention, Worktree-Cleanup | Owner, Terminalitätsbeleg, Retention, Orphan-Erkennung und Cleanup sind nicht über Ressourcenarten einheitlich definiert; reale stale-running-Projektion beobachtet | Bureau für Koordinationsvertrag; Grabowski für operative Umsetzung; Chronik für historische Evidenz | Grabowski-Taskprojektion und Claims | Zeit oder Prozessabwesenheit allein darf keine Evidenz löschen oder fremde Arbeit freigeben. |
| 5. Störungsbeweis | R3-Recoverypflicht; Weltgewebe T004; Grabowski-Recoveryprobe | Anforderungen richten sich primär nach Änderungsrisiko, nicht zusätzlich nach Zielkritikalität; Return-to-primary und Split-Brain sind nicht überall Pflicht | Konvergenzregelkreis; jeweilige Runtime; Grabowski führt aus | Weltgewebe, Grabowski, Produktionsrelease, RepoGround | Keine zufällige Produktionsstörung; ohne isolierten Rückweg bleibt der Test statisch oder simuliert. |
| 6. Langsame Variablen | Task- und Eventhistorie, Receipts, Chronik | Alter, Projektionsverzug, Fehlerwiederkehr, Recoverybelegalter, Ressourcenwachstum und Abschlussdauer werden nicht gemeinsam quellengebunden beobachtet | Primärquellen erzeugen Werte; Infra sammelt zustandslos; Chronik historisiert; Leitstand/Schauwerk projizieren | erster Resilienz-Snapshot | Kein undurchsichtiger Gesamtgesundheitsscore; keine automatische Aufgabe aus bloßer Korrelation. |
| 7. Polyzentrische Autorität | klare Eigentumsgrenzen zwischen Bureau, Grabowski, GitHub, Runtime, Chronik und Systemkatalog | Konfliktauflösung und erlaubte Degradation sind nicht für alle kritischen Übergänge explizit | Systemkatalog und Konvergenzregelkreis | Quelle-veraltet-, widersprüchliche-Evidenz- und Projektion-gegen-Primärquelle-Fälle | Keine Mehrheitsabstimmung zwischen Systemen und keine neue Governanceinstanz. |
| 8. Deklaratives Rewiring | Outbox, Rollbackrezepte, Legacy-Fallback, Operation-Pläne | Failovertrigger, maximale Degradationsdauer, Rückkehrbedingung, Idempotenz und Split-Brain-Schutz sind nicht einheitlich | Systemkatalog beschreibt zulässige Pfade; Grabowski und Runtime führen ausschließlich deklarierte Pfade aus | Chronik-Outbox, RepoGround-Rollback, PostgreSQL-Recovery | Keine freie oder selbstlernende Ersatzwegauswahl; kein Failover mit Autoritätsübernahme. |
| 9. Keystone-Kritikalität | R0–R3 klassifizieren Änderungen; Recoverytechnik schützt einzelne Systeme | Zielsysteme besitzen keine stabile Kritikalitätsklasse; Graphzentralität wäre fachlich unzureichend | Systemkatalog | foundational/essential/supporting/optional für Operator- und Weltgewebe-Kernsysteme | Klassifikation bleibt fachlich, quellengebunden und darf `unknown` sein; keine automatische Ableitung aus Knotengrad. |
| 10. Tragfähigkeit | Bureau-Capacity-Claims, Grabowski-Leases und Nichtkonfliktbeweise | Gemeinsame Ausfalldomänen und gemeinsame Recoverypfade sind keine Konfliktachsen | Bureau koordiniert Capacity; Grabowski attestiert Live-Nichtkonflikt | Datenmigration gegen Restore-Test; Rootbrokeränderung gegen Recoverytest | Keine globale Taskzahl oder Rückkehr zum pauschalen Ein-Ball-Lock. |

## Keine Doppelwahrheit

| Information | Einziger kanonischer Eigentümer | Erlaubte Projektion |
|---|---|---|
| stabile Kritikalität und Ausfalldomäne | Systemkatalog | Bureau, Schauwerk, Leitstand, Konvergenzregelkreis |
| Aufgaben, Claims und Capacity | Bureau | Grabowski und Leitstand lesen gebunden |
| lokale Prozesse, Leases und konkrete Ausführung | Grabowski | Bureau beobachtet über Identitäten und Receipts |
| PR, Merge, Reviews und CI | GitHub | Bureau und Konvergenzregelkreis referenzieren |
| fachlicher Laufzustand | jeweilige Runtime | Leitstand und Abschlussbelege |
| historische Ereignisse | Chronik | Timeline und Evaluation |
| Evidenzschwelle für Abschluss | Konvergenzregelkreis | Bureau und Grabowski wenden Profile an |
| Visualisierung | Schauwerk / Leitstand | keine Rückschreibautorität |
| Nutzenbewertung | Vibe-Lab als Methode; Messwerte bleiben bei Quellen | Bureau erhält nur geprüfte Folgerungen |

## Abhängige Umsetzungsreihenfolge

1. **T001 – dieser Audit:** Begriffe, Eigentümer, Lücken, Piloten und Stopkriterien festlegen.
2. **T002/T003 – statische Semantik:** Kritikalität, Ausfalldomänen und relevante Kanten im Systemkatalog.
3. **T004/T005 – Lebenszyklus:** evidence-preserving Terminalität und Projektion zuerst, weil bereits ein Livefehler vorliegt.
4. **T006 – Tragfähigkeit:** vorhandene Claims um kritische Domänen erweitern, ohne globale Sperre.
5. **T007/T008 – Recoverymodell und Evidenzprofile:** erst nach stabiler Semantik.
6. **T009–T011 – reale Piloten:** Weltgewebe, Grabowski und RepoGround; laufende fremde Implementierungen werden geprüft und wiederverwendet statt dupliziert.
7. **T012/T013 – langsame Variablen und Darstellung:** erst nachdem Quellenfelder stabil sind.
8. **T014 – Wirkungsevaluation:** unnütze Felder, falsche Blockaden und nicht entscheidungsrelevante Komplexität wieder entfernen.

## Aktuelle Parallelitätsentscheidung

- **Jetzt zulässig:** Bureau-Registrierung und dieser read-heavy Systemkatalog-Audit, da getrennte Schreibpfade und Komponenten belegt sind.
- **Derzeit nicht zulässig:** neue Grabowski- oder RepoGround-Schreibarbeit, weil fremde Repo- und Runtimeclaims bestehen.
- **Später prüfbar:** vorhandene Grabowski-Task-Ledger-Konvergenz kann T005 ganz oder teilweise erfüllen; der aktive RepoGround-Cutover kann T011 erfüllen. Abschluss erfolgt nur nach Diff-, Test-, PR-, Merge-, Runtime- und Cleanupbelegen.

## Nutzenhypothesen und Messung

| Hypothese | Erwarteter Nutzen | Messbarer Gegenbeleg |
|---|---|---|
| Lebenszyklusvertrag senkt falsche aktive Arbeit | weniger Projektionsverzug und verwaiste Claims | gleiche oder höhere Verzögerung trotz zusätzlicher Gates |
| Ausfalldomänen erhöhen sichere Parallelität | weniger globale Sperren bei unverändertem Schutz kritischer Ressourcen | häufige falsche Blockaden oder keine geänderte Dispatchentscheidung |
| Kritikalität verbessert Recoverypriorität | Recoverybelege werden dort erneuert, wo Ausfallfolgen am höchsten sind | Klassen ändern keine Tests, Prioritäten oder Recoveryentscheidungen |
| Kantensemantik begrenzt Kaskaden | Teilausfälle degradieren vorhersehbar statt global zu blockieren | Felder bleiben rein dokumentarisch oder widersprechen Runtimeverhalten |
| Slow Variables zeigen schleichenden Verfall | Wiederholungsfehler und Belegalter werden früher sichtbar | hohe Alarmmenge ohne handlungsrelevante Entscheidung |

## Entscheidung

Alle zehn Prinzipien besitzen einen realen, vorhandenen Einbaupunkt. Sie werden umgesetzt, **sofern** jeder Slice seine eigene Nutzenhypothese belegt und keine neue zentrale Wahrheit erzeugt. Der stärkste unmittelbare Hebel ist T004/T005; T002/T003 liefern die statische Grundlage; automatische Failovereffekte kommen zuletzt und nur deklarativ.

Unsicherheit: `0,16` – Eigentumsgrenzen und Liveprobleme sind gut belegt; die quantitative Wirkung ist noch nicht gemessen.
Interpolationsgrad: `0,29` – die Maßnahmen leiten sich überwiegend aus vorhandenen Verträgen und beobachteten Defekten ab, nicht aus der Naturmetapher allein.
