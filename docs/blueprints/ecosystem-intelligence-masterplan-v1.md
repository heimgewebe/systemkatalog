# Ecosystem Intelligence Masterplan v1

## Status

- Typ: strategischer Masterplan
- Stand: 2026-06-30
- Geltung: Cabinet, Bureau und das weitere Heimgewebe-Repoökosystem
- Entscheidung: noch nicht freigegeben fuer Autonomie; dieser Plan beschreibt die Zielrichtung und die kontrollierte Umsetzung

## Leitgedanke

Cabinet soll sich vom lokalen Ordnungsraum zu einer Ecosystem-Intelligence-Schicht entwickeln.

Das Ziel ist kein einzelner Superagent, sondern ein lernendes, belegorientiertes System, das das Repooekosystem beobachtet, strukturiert, priorisiert, delegiert, prueft und aus wiederkehrenden Fehlern neue Regeln ableitet.

Kurzform:

```text
wahrnehmen -> verstehen -> bewerten -> priorisieren -> delegieren -> pruefen -> lernen -> Regeln verbessern
```

Cabinet wird damit nicht zur alleinigen Source of Truth. Git, CI, Contracts, Runtime-Ausgaben und menschliche Entscheidungen bleiben jeweils in ihrer Domaene primaer. Cabinet verbindet diese Quellen, macht ihre Aussagen vergleichbar und haelt Kontext, Evidenz, Aufgaben, Risiken und Entscheidungen zusammen.

## Zielbild

```text
                       Mensch
          Sinn, Freigabe, Priorisierung, Abbruch
                         |
                         v
                      Cabinet
   Weltmodell, Evidenz, Aufgaben, Risiken, Lernen
             |                         |
             v                         v
          Bureau                 Merge-Dumps
   Zyklus, Queue, Delegation     Kontext, Review, Belege
             |
             v
     Codex / Claude / Jules / lokale Agenten
             |
             v
        Git / CI / Runtime / Contracts
              harte Realitaetspruefung
```

## Prinzipien

1. Beobachtung ist keine Entscheidung.
2. Befund ist keine Ausfuehrung.
3. Aufgabe ist kein Merge-Recht.
4. Score ist keine Wahrheit.
5. Agentenergebnis ist ein Vorschlag, bis Evidenz und Pruefung vorliegen.
6. Cabinet darf Arbeitskandidaten erzeugen, aber Autonomie wird phasenweise freigeschaltet.
7. Wiederkehrende Fehler werden als Fehlerklasse behandelt, nicht nur als Einzelfall.
8. Jede Automatisierung braucht Abbruchkriterium, Rollbackpfad und Evidenzpflicht.
9. Das System optimiert nicht nur auf Geschwindigkeit, sondern auf Stabilitaet, Nachvollziehbarkeit und Oekosystemnutzen.

## Zielorgane

### 1. Sensorium

Cabinet sammelt Signale aus:

- GitHub Pull Requests, Issues, Branches und CI-Laeufen
- lokalen Worktrees
- Bureau-Queue und Bureau-Zyklen
- Merge-Dumps und repoLens-Artefakten
- Runtime-Healthchecks
- systemd-Timern und Betriebslogs
- Security-Scans
- Roadmaps, Blueprints und Vault-Notizen
- Agentenprotokollen
- expliziten menschlichen Entscheidungen

Signale sind Rohwahrnehmung. Sie werden nicht als Wahrheit kanonisiert.

Zielartefakte:

```text
pruefung/00 Signale/*.jsonl
pruefung/10 Laeufe/*.md
bestand/30 Quellen/*.md
```

### 2. Ecosystem Graph

Cabinet haelt einen maschinenlesbaren Graphen des Repooekosystems.

Knoten koennen sein:

- Repository
- Service
- Contract
- CI-Workflow
- Runtime-Instanz
- Agent
- Roadmap
- Task
- Pull Request
- Risiko
- Entscheidung

Kanten koennen sein:

- depends_on
- provides
- validates
- owns
- consumes
- blocks
- supersedes
- contradicts
- delegates_to
- verified_by

Minimaler Knotenausschnitt:

```yaml
kind: ecosystem_node
id: repo:bureau
node_type: repository
role: operative task orchestration
health_dimensions:
  - queue hygiene
  - review steward correctness
  - agent delegation
  - merge discipline
```

### 3. Claim Ledger

Cabinet fuehrt ein Ledger fuer Aussagen.

Jede relevante Aussage wird klassifiziert:

- observed
- plausible
- evidenced
- validated
- canonical
- stale
- contradicted
- refuted

Minimales Claim-Format:

```yaml
kind: ecosystem_claim
id: claim:example
subject: repo:bureau
predicate: has_open_merge_risk
status: evidenced
confidence: 0.72
evidence:
  - type: ci
    ref: github-run-url-or-local-path
expires_at: 2026-07-01T00:00:00+02:00
```

Ziel: Cabinet darf Widersprueche sichtbar halten, statt sie still zu glätten.

### 4. Task Metabolism

Cabinet verwandelt Signale und Claims in Aufgaben-Kandidaten.

Beispiele:

```text
CI rot -> Diagnoseauftrag
P1-Review-Kommentar -> Fixauftrag
Roadmap offen, Code teilweise umgesetzt -> Reconcile-Auftrag
Repo lange nicht geprueft -> Hygieneauftrag
wiederholter Agentenfehler -> Tooling- oder Runbook-Auftrag
```

Zustandsmodell:

```text
candidate -> triaged -> approved -> delegated -> in_progress -> review_needed -> accepted|rejected|archived
```

Nur `approved` darf an Bureau als ausfuehrbarer Kandidat exportiert werden.

### 5. Agent Briefing Builder

Cabinet erzeugt Briefings fuer unterschiedliche Agentenprofile.

Routing-Hypothese:

- Jules: kleine, klare Patches
- Codex: Review, Logikfehler, Sicherheitsinvarianten
- Claude/Opus: Architektur, grosse Refactors, tiefe Konzeptkritik
- lokale Agenten: billige Vorpruefung, repetitive Scans
- ChatGPT: Synthese, Priorisierung, Kontextintegration
- Bureau: Taktung, Queue, Delegation, Merge-Gates

Briefing-Paket:

```yaml
goal:
repo:
allowed_scope:
forbidden_changes:
context_paths:
evidence_required:
acceptance_tests:
known_traps:
rollback_required:
output_contract:
```

### 6. Result Verifier

Cabinet prueft Agentenergebnisse gegen Zielbelege.

Prueffragen:

- Wurde das Ziel erreicht?
- Wurde der Scope eingehalten?
- Sind Tests, CI oder Runtime-Belege vorhanden?
- Wurden Review-Kommentare bearbeitet?
- Gibt es neue Risiken?
- Ist ein Rollbackpfad benannt?
- Wurde eine Fehlerklasse sichtbar?

### 7. Learning Loop

Cabinet extrahiert aus wiederkehrenden Fehlern Regeln.

Beispiel:

```text
Muster: Agenten liefern PRs mit gruener CI, aber ohne lokale Evidence.
Regelvorschlag: merge_candidate requires local_evidence.status in [passed, not_applicable_with_reason].
```

Regelvorschlaege werden als `proposed_policy` abgelegt und muessen vor Aktivierung freigegeben werden.

### 8. Nutzenkompass

Priorisierung erfolgt nicht nur technisch.

Bewertungsachsen:

- Sicherheit
- Stabilitaet
- Nutzerlebensqualitaet
- Entwicklergeschwindigkeit
- Wissensverlust-Vermeidung
- Transparenz und Fairness
- Betriebsaufwand
- Zukunftsfaehigkeit
- Entsperrungswirkung fuer Folgearbeiten

Vorschlag fuer Score:

```text
priority_score = (impact * urgency * confidence * unblock_factor) / risk
```

Der Score darf Entscheidungen vorbereiten, aber nicht ersetzen.

## Phasenplan

### Phase 0: Begriffsklaerung und Contract-Schnitt

Ziel: Keine Autonomie, nur gemeinsame Sprache.

Artefakte:

```text
docs/blueprints/ecosystem-intelligence-masterplan-v1.md
schemas/ecosystem-node.v1.json
schemas/ecosystem-claim.v1.json
schemas/task-candidate.v1.json
schemas/agent-briefing.v1.json
```

Akzeptanz:

- Schemas existieren.
- Beispiele validieren.
- Kein Timer, kein Auto-Dispatch, kein Repo-Write ausserhalb Cabinet.

### Phase 1: Ecosystem Graph v1

Ziel: Repos, Services, Agenten, Contracts und bekannte Abhaengigkeiten als Graph ausdruecken.

Artefakte:

```text
scripts/build-ecosystem-graph.py
steuerung/10 Lage/ecosystem-graph.json
pruefung/10 Laeufe/ecosystem-graph-build-*.md
```

Akzeptanz:

- Graph kann deterministisch aus versionierten Quellen erzeugt werden.
- Fehlende Quellen werden als Leerstelle ausgegeben.
- Keine Aktualitaet wird behauptet, wenn nur Snapshots vorliegen.

### Phase 2: Bureau Bridge v1

Ziel: Cabinet liefert validierte Task-Kandidaten an Bureau; Bureau liefert Laufberichte an Cabinet zurueck.

Artefakte in Cabinet:

```text
schemas/bureau-task-candidate.v1.json
schemas/bureau-run-report.v1.json
scripts/export-bureau-frontier.py
scripts/import-bureau-run.py
```

Artefakte in Bureau:

```text
docs/plans/cabinet-ecosystem-intelligence-masterplan-v1.md
```

Akzeptanz:

- Export ist read-only aus Cabinet-Sicht.
- Import ist append-only.
- Nur approved Tasks werden exportiert.
- Done-Reports brauchen Evidence oder `not_applicable_with_reason`.

### Phase 3: Signal Ingest v1

Ziel: Bureau, GitHub, lokale Worktrees und Runtime-Health als Signale einsammeln.

Artefakte:

```text
scripts/ingest-bureau-state.py
scripts/ingest-local-worktrees.py
scripts/ingest-github-state.py
scripts/ingest-runtime-health.py
pruefung/00 Signale/*.jsonl
```

Akzeptanz:

- Jeder Ingest ist einzeln ausfuehrbar.
- Jeder Ingest hat Trockenlaufmodus.
- Secrets werden nicht exportiert.
- Fehler erzeugen Befund statt stiller Korrektur.

### Phase 4: Claim Ledger v1

Ziel: Signale werden in Aussagen mit Evidenzstatus ueberfuehrt.

Artefakte:

```text
scripts/build-claim-ledger.py
pruefung/20 Belege/claim-ledger.jsonl
pruefung/30 Befunde/claim-contradictions-*.md
```

Akzeptanz:

- Widersprueche bleiben sichtbar.
- Claims haben Ablaufdatum oder Frischeklasse.
- Veraltete Claims werden markiert, nicht geloescht.

### Phase 5: Task Frontier v1

Ziel: Cabinet erzeugt priorisierte Arbeitskandidaten.

Artefakte:

```text
scripts/build-task-frontier.py
steuerung/20 Aufgaben/frontier.json
steuerung/20 Aufgaben/frontier.md
```

Akzeptanz:

- Jeder Kandidat verweist auf Claims und Evidence.
- Risiko und Nutzen sind getrennt ausgewiesen.
- Bureau liest nur validierte Kandidaten.

### Phase 6: Agent Briefings v1

Ziel: Cabinet erstellt reproduzierbare Briefings fuer Codex, Claude, Jules und lokale Agenten.

Artefakte:

```text
scripts/build-agent-briefing.py
steuerung/30 Uebergaben/agent-briefings/*.md
```

Akzeptanz:

- Briefings enthalten Scope, Non-Goals, Akzeptanzkriterien und Evidence-Pflicht.
- Schwere Aufgaben bekommen Kontrastfragen.
- Architekturkritische Aufgaben bekommen mindestens eine alternative Sinnachse.

### Phase 7: Result Verification v1

Ziel: Agentenergebnisse werden vor Uebernahme systematisch geprueft.

Artefakte:

```text
scripts/verify-agent-result.py
pruefung/10 Laeufe/agent-result-verification-*.md
pruefung/30 Befunde/agent-result-*.md
```

Akzeptanz:

- Kein accepted ohne Zielbeleg.
- Kein merge_candidate aus bloss vorhandener Evidence.
- Negative Ergebnisse werden erhalten.

### Phase 8: Learning Loop v1

Ziel: Cabinet erkennt Fehlerklassen und schlaegt Regeln vor.

Artefakte:

```text
scripts/extract-ecosystem-patterns.py
scripts/propose-policy-updates.py
steuerung/40 Regelvorschlaege/*.md
```

Akzeptanz:

- Regelvorschlaege werden nicht automatisch aktiviert.
- Jeder Regelvorschlag nennt Gegenbeispiele und Nebenwirkungen.
- Wiederkehrende Fehlerklassen werden mit konkreten Tasks verbunden.

## Minimaler erster PR-Schnitt

Empfohlenes erstes Inkrement:

```text
CAB-ECO-001: Ecosystem Intelligence Masterplan and Contracts
```

Scope:

```text
docs/blueprints/ecosystem-intelligence-masterplan-v1.md
schemas/ecosystem-node.v1.json
schemas/ecosystem-claim.v1.json
schemas/task-candidate.v1.json
schemas/agent-briefing.v1.json
scripts/tests/test_ecosystem_intelligence_schemas.py
```

Nicht im ersten PR:

- kein GitHub-Ingest
- kein Bureau-Write
- kein Timer
- kein Auto-Dispatch
- kein Agentenstart
- kein Merge-Gate

## Risiken

### Artefaktinflation

Risiko: Cabinet erzeugt zu viele Dateien und wird schwer lesbar.

Gegenmittel: generierte Artefakte klar markieren, Runtime-Artefakte aus Git halten, stabile Indexseiten erzeugen.

### Zirkulaere Evidenz

Risiko: Cabinet stuetzt Cabinet-Claims auf Cabinet-Artefakte.

Gegenmittel: Claim-Ledger verlangt Primaerquelle oder markiert die Aussage als intern/plausibel.

### Score-Glaeubigkeit

Risiko: Prioritaetsscores werden mit Wahrheit verwechselt.

Gegenmittel: Score erklaeren, Prämissen ausgeben, menschliche Freigabe fuer hohe Risiken.

### Agenten-Overreach

Risiko: Agenten bearbeiten mehr als beauftragt.

Gegenmittel: Briefing mit allowed_scope, forbidden_changes, acceptance_tests und rollback_required.

### Verdeckte Drift

Risiko: Snapshots werden als Live-Stand missverstanden.

Gegenmittel: jede Quelle mit Erfassungszeitpunkt, Frischeklasse und Ablaufdatum.

## Entscheidungspunkte

Vor Phase 2:

- Darf Bureau Cabinet-Artefakte schreiben oder nur Reports liefern?
- Wo liegt die Runtime-Frontier: im Cabinet-Repo, in `.cabinet-state`, oder in Bureau-State?
- Welche Tasks brauchen menschliche Freigabe?

Vor Phase 5:

- Welche Priorisierungsgewichte gelten?
- Welche Risiko-Klassen blockieren Auto-Delegation?

Vor Phase 8:

- Wer darf Regelvorschlaege aktivieren?
- Welche Regeln duerfen CI-Gates beeinflussen?

## Naechste konkrete Aktion

1. Masterplan in Cabinet versionieren.
2. Bureau-Anschlussnotiz in Bureau hinterlegen.
3. Danach CAB-ECO-001 als Schema- und Test-PR umsetzen.
4. Erst nach Schema-Gruen: Bureau Bridge v1 bauen.

## Kurzform

Cabinet soll das Oekosystem nicht einfach schneller machen. Es soll es lernfaehig machen.

Der Hebel ist nicht Autopilot, sondern belegorientierte Evolution: bessere Wahrnehmung, bessere Aufgaben, bessere Delegation, bessere Pruefung, bessere Regeln.
