# Cabinet Surface Migration Matrix v1

Status: T004 catalog-core consolidation complete; runtime and rename follow-ups remain

Bureau tasks: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T011`, `T007`, `T004`

## Ziel

Cabinet wird zu einem app-unabhängigen Heimgewebe-Systemkatalog. Dieser erste Schritt klassifiziert die bestehende Oberfläche, entfernt aber keine Legacy-Inhalte, stoppt keinen Dienst und benennt kein Repository um.

Kategorien:

- `KEEP`: bleibt Bestandteil des aktiven Katalogs.
- `SIMPLIFY`: bleibt, wird aber auf stabile Katalogsemantik reduziert.
- `MOVE`: die fachliche Autorität liegt in einem anderen Organ.
- `ARCHIVE`: bleibt historisch auffindbar, aber nicht Teil der aktiven Produktfläche.
- `REMOVE`: wird nach gesicherter Migration und eigenem Review gelöscht.

## Matrix

| Oberfläche | Heute | Entscheidung | Ziel / Organ | Abhängigkeit |
|---|---|---|---|---|
| `README.md`, `index.md`, `AGENTS.md` | Einstieg, Rollenbeschreibung und Agentenregeln | `SIMPLIFY` | Systemkatalog-Einstieg ohne Priorisierung, Runtime- oder Merge-Claims | T011 |
| `policy/system-catalog.v1.json` | neuer Zielvertrag | `KEEP` | Maschinenlesbare Rollen- und Wirkungsgrenze | T011 |
| `catalog/system-catalog.schema.v1.json` | neues Zielformat | `KEEP` | App-unabhängiger Datenvertrag | T011 |
| `catalog/system-catalog.example.v1.json` | nichtkanonisches Beispiel | `KEEP` | Formatbeispiel; niemals zweite Wahrheit | T011 |
| `registry/ecosystem/nodes.json` | kanonisches stabiles Systeminventar ohne Betriebsstatus | `KEEP` | Systeme, Zweck und Identität | T004 abgeschlossen |
| `registry/ecosystem/edges.json` | kanonische Beziehungen mit `stable`, `bounded` oder `related` | `KEEP` | stabile Architekturbeziehungen, kein Betriebsstatus | T004 abgeschlossen |
| `registry/ecosystem/claims.jsonl` | langlebige Architektur- und Ownership-Aussagen ohne Status, Confidence oder Ablaufdatum | `KEEP` | stabile Katalogclaims; frühere dynamische Claims archiviert | T004 abgeschlossen |
| `registry/ecosystem/authority-matrix.v1.json` | einzige gepflegte Wahrheitsmatrix | `KEEP` | keine Cabinet-Projektion operativer Zustände | T004 abgeschlossen |
| `registry/ecosystem/consumer-usage.v1.json` | datierter, redaktierter Consumer- und Nutzungsmessbeleg | `KEEP` als Entscheidungsbeleg | keine Live-Statusquelle; private Detailbelege bleiben außerhalb des Repositories | T007 |
| `registry/ecosystem/operator-redundancy-audit.v1.json` | datierter Audit | `ARCHIVE` | Entscheidungsbeleg, keine aktuelle Statusquelle | T004 |
| `rendered/system-catalog.md` | neue lesbare Projektion | `KEEP` | kanonische menschenlesbare Katalogansicht | T011 |
| `rendered/ecosystem-registry-map.mmd` | einzige kanonisch generierte Registry-Karte | `KEEP` | statusfreie Katalogprojektion; keine Claimautorität | T004 abgeschlossen |
| `rendered/ecosystem-map.mmd` | handgepflegte Übersicht | `ARCHIVE` oder spezialisierte Projektion | nur behalten, falls klarer zusätzlicher Nutzen besteht | T004/T007 |
| Registry-, Karten- und Linkvalidatoren | technische Konsistenzprüfung | `SIMPLIFY` | IDs, Beziehungen, Truth Ownership, Links und Render-Drift prüfen | T011/T004 |
| `scripts/validate_system_catalog.py` | neuer Katalogvalidator | `KEEP` | deterministische Katalogprüfung | T011 |
| `scripts/render_system_catalog.py` | neuer Renderer | `KEEP` | deterministische Leseansicht | T011 |
| Cabinet Maintenance Radar und Policy | Findings, Frische, Handoff-Reife und Effektgrenzen | `REMOVE` nach Archivierung | kein Radar im Katalog; Aufgaben nach Bureau, Live-Sicht nach Leitstand | T004 |
| Maintenance-Report-Generator und Findings | zweites Befund- und Statusmodell | `REMOVE` nach Archivierung | repo-lokale CI-Fehler oder Bureau-Tasks | T004 |
| Cabinet Frontier, Candidate- und Handoff-Flächen | tasknahe Kandidaten und Übergaben | `MOVE` | Bureau | T004 |
| Ecosystem Live Signals | kopierte PR-, CI-, Queue- oder Runtime-Signale | `MOVE` | GitHub/CI, Bureau, Runtime und Leitstand | T004 |
| Gemini Maintenance Workflows, Runner, Schemas und Runbooks | manueller proposal-only Versuch | `ARCHIVE`, danach `REMOVE` aus aktiver Oberfläche | kein wiederkehrender Scout; Git-Historie bewahrt den Versuch | T004 |
| `.github/workflows/claude.yml` | ereignisbezogene externe Assistenz | `ARCHIVE` oder `REMOVE` | Reviews gehören in Repo-/Grabowski-Reviewpfade, nicht in den Katalog | T004 |
| `external/repobrief/**`, `external/lenskit/**` | Referenzen auf externe Dump-Artefakte | `SIMPLIFY` | optionale Kontextlinks; keine Frische- oder Claim-Zustandsmaschine | T004 |
| Architekturentscheidungen, Glossar und stabile Begriffe | langlebige Semantik | `KEEP` | `docs/decisions/` und `docs/glossary.md` | T004 |
| alte Rollen-, Radar- und Experimentdokumente | historische Entscheidungsentwicklung | `ARCHIVE` | `docs/archive/cabinet-era/` oder Git-Historie | T004 |
| `steuerung/**`, Projektkarten und lokale Prioritätsflächen | Aufgaben- und Reihenfolgemodell | `MOVE` | Bureau | T004 |
| `pruefung/10 Laeufe/**` | Lauf- und Experimentbelege | `ARCHIVE` | historische Evidence; keine aktuelle Produktfläche | T004 |
| `ops/manifest.json`, `ops/bin/**`, `ops/install/**` | Installation und Steuerung der externen Cabinet-App | `REMOVE` nach privatem Export | Runtime-Rückbau mit Rollback-Beleg | T012/T013 |
| `ops/systemd/**` | lokaler Cabinet-Dienst | `REMOVE` nach bewiesener App-Unabhängigkeit | keine Katalogruntime | T012/T013 |
| `ops/patches/**` | Patch der gepinnten Fremd-App | `REMOVE` | keine fremde App als Katalogfundament | T013 |
| `.cabinet`-Raumkonfiguration und app-spezifische Räume | Darstellung und Arbeitsfläche der Fremd-App | `ARCHIVE` oder `REMOVE` | optionaler Übergangsviewer, kein Canon | T012/T013 |
| lokale App-Daten, Conversations, Memory und Konfiguration | möglicherweise nichtversionierte private Inhalte | `MOVE` in privates Archiv | außerhalb des öffentlichen Repositories | T012 |
| `scripts/private_cabinet_archive.py` | create-only Sicherungs- und isoliertes Restore-Werkzeug | `ARCHIVE` nach abgeschlossenem Runtime-Rückbau | migrationsgebundener Schutzmechanismus, kein Bestandteil des Systemkatalogs | T012/T013 |
| `scripts/private_cabinet_restic_handoff.py` | tmpfs-zu-Restic Snapshot- und Restore-Verifier | `ARCHIVE` nach abgeschlossenem Runtime-Rückbau | verschlüsselter migrationsgebundener Handoff; keine Katalogruntime und keine Retentionsteuerung | T012/T013 |
| Repositoryname `heimgewebe/cabinet` | mit Fremdprodukt verwechselbare Identität | `MOVE` | `heimgewebe/heimgewebe-katalog` erst nach Runtime-Rückbau | T014 |

## Organrouting

| Aussage oder Wirkung | Zuständiges Organ |
|---|---|
| Aufgaben, Queue, Priorität, Handoff und Abschluss | Bureau |
| lokale und repositorybezogene Ausführung | Grabowski |
| PRs, Branches, Reviews und Mergeability | GitHub |
| technische Prüfergebnisse | CI und Review-Gates |
| laufender Dienstzustand | Runtime, Healthchecks, systemd und Logs |
| allgemeine Live-Anzeige | Leitstand |
| Repo-Snapshots und zitierfähiger Kontext | RepoBrief / Lenskit |
| stabile Ökosystem-Semantik und Truth Ownership | Heimgewebe-Systemkatalog |

## Gates vor destruktiven Schritten

1. Private lokale App-Daten sind inventarisiert, exportiert oder ausdrücklich als entbehrlich klassifiziert.
2. Der Katalog validiert und rendert, während `cabinet.service` gestoppt ist.
3. Aktive Consumer sind bekannt; öffentliche Belege enthalten keine privaten Runtime-Details.
4. Bureau autorisiert Runtime-Rückbau und Repository-Rename jeweils separat.
5. Jeder destruktive Schritt besitzt Backup, Rollback und Receipt.

## Nicht-Claims dieser Scheibe

- Die externe Cabinet-App ist noch nicht gestoppt oder entfernt.
- Lokale App-Daten sind noch nicht vollständig inventarisiert.
- Legacy-Registry und Statusfelder sind noch nicht vollständig migriert.
- Das Repository ist noch nicht umbenannt.
- Die Matrix erteilt keine Lösch-, Shutdown-, Rename- oder Merge-Erlaubnis.
