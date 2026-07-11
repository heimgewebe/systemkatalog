# Cabinet Surface Migration Matrix v1

Status: T004-Katalogkern und T013-Runtime-Cutover abgeschlossen; nur T014-Repository- und Referenzumbenennung bleibt offen

Bureau tasks: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T011`, `T007`, `T004`, `T013`

## Ziel

Cabinet ist der app-unabhängige Heimgewebe-Systemkatalog. Der aktive Runtimevertrag liefert ausschließlich eine read-only Projektion der kanonischen Katalogdaten; die externe Workspace-App ist retired. Das Repository ist noch nicht umbenannt.

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
| `ops/manifest.json`, `ops/bin/**`, `ops/install/**` | Installation und Audit der read-only Katalogprojektion | `KEEP` | reproduzierbare Systemkatalog-Runtime ohne Provider, Datenbank oder Secrets | T013 abgeschlossen |
| `ops/systemd/**` | `heimgewebe-systemkatalog.service` ohne Cabinet-Alias | `KEEP` | Loopback-only Leseoberfläche; keine Katalogautorität und kein zweiter Daemon | T013 abgeschlossen |
| frühere `ops/patches/**` | Patch der gepinnten Fremd-App | `REMOVE` | aus dem aktiven Repositoryvertrag entfernt | T013 abgeschlossen |
| `.cabinet`-Raumkonfiguration und app-spezifische Räume | private Altbestände der Fremd-App | `ARCHIVE` | kein aktiver Viewer und kein Canon; spätere Retention separat | T013 abgeschlossen |
| lokale App-Daten, Conversations, Memory und Konfiguration | möglicherweise nichtversionierte private Inhalte | `MOVE` in privates Archiv | außerhalb des öffentlichen Repositories | T012 |
| `scripts/private_cabinet_archive.py` | create-only Sicherungs- und isoliertes Restore-Werkzeug | `ARCHIVE` nach abgeschlossenem Runtime-Rückbau | migrationsgebundener Schutzmechanismus, kein Bestandteil des Systemkatalogs | T012/T013 |
| `scripts/private_cabinet_restic_handoff.py` | tmpfs-zu-Restic Snapshot- und Restore-Verifier | `ARCHIVE` nach abgeschlossenem Runtime-Rückbau | verschlüsselter migrationsgebundener Handoff; keine Katalogruntime und keine Retentionsteuerung | T012/T013 |
| `docs/migration/cabinet-runtime-retirement-preflight-v1.json` | redaktierter, datierter Runtime-Entscheidungsbeleg | `KEEP` bis T013-Abschluss, danach `ARCHIVE` | bindet privaten Livebeleg per Hash; keine Live-Status- oder Abschaltautorität | T013 Preflight abgeschlossen |
| `docs/migration/cabinet-runtime-retirement-authorization-v1.md` | gestufter Rückbau- und Rollbackplan | `KEEP` bis T013-Abschluss, danach `ARCHIVE` | Phase-A–D-Gates; jede Wirkung benötigt eigene Autorisierung | T013 Preflight abgeschlossen |
| Repositoryname `heimgewebe/heimgewebe-katalog` | mit Fremdprodukt verwechselbare Identität | `MOVE` | `heimgewebe/heimgewebe-katalog` erst nach Runtime-Rückbau | T014 |

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
2. Ein begrenzter Stopptest wurde separat autorisiert, mit Rollback ausgeführt und zeigt, dass der Katalog ohne laufende externe App validiert und rendert. Der aktuelle Preflight bereitet diesen Test nur vor.
3. Aktive Consumer sind soweit möglich bekannt; öffentliche Belege enthalten keine privaten Runtime-Details und Restunsicherheit bleibt sichtbar.
4. Der Runtime-Cutover ist autorisiert und umgesetzt; Repository-Rename und private Daten-/Retentionwirkungen bleiben separat.
5. Jeder destruktive Schritt besitzt Backup, Rollback und Receipt.

## Nicht-Claims dieser Scheibe

- Die externe Cabinet-App ist aus dem aktiven Dienst- und Repositoryvertrag entfernt.
- Private Altbestände sind erhalten und nicht endgültig gelöscht.
- Historische Legacy-Flächen bleiben als Archiv oder Kompatibilität vorhanden.
- Das Repository ist noch nicht umbenannt.
- Die Matrix erteilt keine private Lösch-, Retention- oder Rename-Erlaubnis.
