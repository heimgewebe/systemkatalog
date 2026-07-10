# Operator Ecosystem Redundancy Audit v1

Status: evidence-bound snapshot

Erhebung: 2026-07-10

Owner: Cabinet

Maschinenlesbarer Befund: [`registry/ecosystem/operator-redundancy-audit.v1.json`](../../registry/ecosystem/operator-redundancy-audit.v1.json)

## Dialektische Eröffnung

**These:** Die vielen Organe liefern echte Trennung von Aufgaben, Ausführung, Kontext, Darstellung, Lernen und Historie.

**Antithese:** Dieselbe Trennung erzeugt inzwischen parallele Statusflächen, mehrere Scheduler, doppelte Karten, viele Evidence-Formate und Systeme ohne belegten Runtime-Konsumenten.

**Synthese:** Nicht pauschal Repositories löschen. Zuerst Autorität und aktive Konsumenten erhalten, abgeleitete Flächen vereinfachen und unbewiesene Lern-/Experimentpfade einfrieren.

## Methode und Beleggrenze

Der Audit kombiniert:

1. aktuelle Git-Zustände und offene PRs der Zielrepos;
2. Grabowski Deployment-, Worktree- und Runtime-Zustand;
3. lokale User-/System-systemd-Units;
4. Querverweise in Source, Config, Workflows, Policies, Schemas und Registries;
5. die erklärten Autoritätsgrenzen aus Bureau und Cabinet.

Dokumentationsverweise allein gelten nicht als aktiver Konsument. Ein Source-Verweis belegt Integration oder Abhängigkeit, aber nicht deren fachliche Korrektheit. Das Fehlen einer lokalen Unit beweist nicht, dass kein entfernter Dienst existiert.

## Live-Befunde

- Bureau hat **10 aktive Timer** für Kuratierung, Discovery, Closure, Review, Verifikation und Bridges.
- Grabowski ist gesund und runtime-identisch, besitzt aber **44 Worktrees** und **21 fehlgeschlagene oder fehlerhaft konfigurierte transiente Units**.
- Cabinet, Leitstand, rLens und Grabowski laufen aktiv.
- Schauwerk besitzt einen aktiven Keepalive-Timer.
- Für Chronik, Heimlern und Vibe-Lab wurden lokal keine aktiven Units gefunden.

Diese Zahlen sind datierte Ist-Belege, keine dauerhaften Eigenschaften.

## Entscheidungsmatrix

| Organ | Konkreter Nutzen | Hauptredundanz | Pflege | Abschaltbarkeit | Entscheidung |
|---|---|---|---|---|---|
| Bureau | deterministische Aufgaben, Claims, Receipts, Parallelität | viele Ops-Timer und Statusprojektionen | hoch | Core niedrig, einzelne Timer hoch | Core behalten; Scheduler-Lanes konsolidieren |
| Grabowski | tatsächliche lokale/Fleet-Ausführung | alte Worktrees, transiente Units, Statuskopien | hoch | Core niedrig, optionale Lanes hoch | Core behalten; Lifecycle-Hygiene vor neuen Rollen |
| RepoBrief/Lenskit | zitierfähiger, frischer Agentenkontext | viele Export- und Bundleformen | mittel-hoch | mit Qualitätsverlust ersetzbar | Query/Range/Context-Pack behalten; Vollreports diagnostisch |
| Cabinet | Sinn, Evidence, Entscheidungen, Karten-Canon | Maps, Registry, Seeds, Räume, Prosa parallel | hoch | Service hoch, Repo mittel | auf eine Autoritätsmatrix und eine generierte Karte reduzieren |
| Steuerboard | Repo-State und Readiness-Ableitung | überschneidet GitHub, Grabowski und Bureau | hoch | nach Migration hoch | Scope einfrieren; Bibliothek extrahieren oder auslaufen lassen |
| Leitstand | eine menschliche Operatoransicht | kopiert Quellstatus | mittel | hoch, mit Komfortverlust | als einzige Anzeige behalten, keine Autorität |
| Schauwerk | spezialisierte Visualisierung/Miro/Publikation | generische Karten überlappen Cabinet/Leitstand | mittel | hoch | Spezialrenderer behalten; kein zweiter Ecosystem-Canon |
| Chronik | append-only Ereignishistorie | Git, Receipts und Logs speichern bereits Historie | mittel | aktuell eher hoch | nur wenige wertvolle Events mit benanntem Consumer |
| Heimlern | rückblickende Policy-Vorschläge | überlappt Friction, Cabinet Outcomes, Vibe-Lab | mittel-hoch | aktuell hoch | Ausbau pausieren bis ein messbarer Closed Loop existiert |
| Vibe-Lab | kontrollierte Experimente | Evidence-/Schema-Fläche ohne Produktionskonsumenten | relativ hoch | sehr hoch | Experimente nur mit Sponsor, Entscheidungsziel und Ablaufdatum |
| WGX | gemeinsame Fleet-Checks und Templates | überschneidet Repo-CI und Grabowski-Motorik | mittel-hoch | nach CI-Migration mittel | nur echte gemeinsame Checks behalten |
| GitHub/CI/Runtime | harte Realität | lokale Kopien können stale werden | notwendig | nicht abschaltbar | immer primäre Quelle bleiben |

## Was konkret überflüssig oder zu breit ist

### 1. Bureau-Ops als Timer-Fächer

Die einzelnen Organe können fachlich sinnvoll sein. Zehn unabhängige Timer erhöhen jedoch Reihenfolge-, Diagnose- und Pflegekosten. Ziel ist nicht blindes Löschen, sondern ein Ablauf mit wenigen Scheduler-Lanes und expliziten Stufen.

### 2. Grabowski-Historien im aktiven Runtime-Namensraum

Alte Worktrees und fehlgeschlagene transiente Units sind Evidence, aber im aktiven Namespace werden sie zu Betriebslast. Vor Löschung braucht es Klassifikation, Archivref und Task-Abgleich.

### 3. Steuerboard als zweite Operator-Halbebene

Steuerboard ist zugleich Beobachter, Readiness-Ableiter, Fetch-Werkzeug und Besitzer zweier Git-Mutatoren. Das ist zu breit neben Grabowski und Bureau. Der nützliche Kern ist wahrscheinlich ein kleiner Repo-State-/Readiness-Adapter.

### 4. Mehrere semantische und visuelle Karten

Cabinet, Schauwerk und Leitstand dürfen unterschiedliche Darstellungen haben. Nur Cabinet sollte die Semantik halten; die übrigen Ansichten müssen daraus oder aus Primärquellen erzeugt werden.

### 5. Lernen und Experimente ohne Consumer-Gate

Heimlern und Vibe-Lab sind nicht wertlos. Überflüssig ist Arbeit ohne benannten Empfänger, messbare Entscheidung und Ende. Proposal-only darf nicht permanenten Pflegeanspruch bedeuten.

## Alternative Sinnachse

Wenn maximale Geschwindigkeit höher als Nachvollziehbarkeit gewichtet wird, könnten Steuerboard, Chronik, Heimlern, Vibe-Lab und große Teile von Cabinet pausiert werden. Das reduzierte System wäre Bureau, Grabowski, RepoBrief, GitHub/CI/Runtime und eine Leitstand-Anzeige.

Wenn dagegen Forschung, langfristiges Lernen und institutionelles Gedächtnis höher gewichtet werden, bleiben Chronik, Heimlern und Vibe-Lab sinnvoll — aber nur mit explizitem Consumer-, Erfolgs- und Retention-Gate.

## Priorisierte Folgeschritte

1. **P1:** Bureau-Timer nach Input, Output, Reihenfolge und tatsächlichem Consumer inventarisieren.
2. **P1:** Grabowski-Worktrees und transiente Units klassifizieren, reconciliieren und erst danach archivieren.
3. **P1:** Steuerboard-Rollenentscheid treffen und neue Features bis dahin einfrieren.
4. **P2:** Cabinet auf eine Autoritätsmatrix, eine Registry und eine generierte Karte reduzieren.
5. **P2:** Heimlern-/Vibe-Lab-Arbeit an Consumer, Zielmetrik und Ablaufdatum binden.
6. **P2:** Chronik auf ein kleines Set zusätzlicher, tatsächlich abgefragter Events beschränken.

## Belegt / plausibel / spekulativ

**Belegt:** lokale Runtime-Units, Timeranzahl, Grabowski-Runtimebindung, Worktreezahl, fehlgeschlagene Units, Querverweise und deklarierte Autoritätsgrenzen.

**Plausibel:** Steuerboard lässt sich auf einen kleinen Adapter reduzieren; Cabinet-Projektionen können deutlich konsolidiert werden; Bureau-Timer können zusammengeführt werden.

**Spekulativ:** genaue Einsparung an Pflegezeit und die minimale optimale Timerzahl. Dafür fehlen Laufzeitmessungen und Consumer-Telemetrie.

Fehlt: entfernte Runtime-Inventur und belastbare Nutzungsfrequenz pro Ansicht; nötig für endgültige Abschaltentscheidungen.

- Unsicherheit: **0,19** — lokale Live-Sicht ist stark, entfernte Konsumenten sind nicht vollständig erfasst.
- Interpolationsgrad: **0,31** — Redundanzurteile verbinden gemessene Strukturen mit Architekturfolgen.

## Nicht-Claims

Dieser Audit genehmigt keine Abschaltung, Löschung, Queue-Mutation, Merge-Entscheidung oder Runtime-Änderung. Er beweist weder vollständige Remote-Inventur noch fachliche Korrektheit der beobachteten Consumer.
