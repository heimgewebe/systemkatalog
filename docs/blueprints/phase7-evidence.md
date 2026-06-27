# Phase 7 Evidence und Befund v1

## Zweck

Dieser Vertrag setzt Phase 7 der Repository-Oversight-Roadmap um: Evidence-Pflicht, stabile Fingerprints und eine klare Trennung zwischen maschinellem Hinweis und menschlich bestätigtem Befund.

Ein Finding beschreibt eine beobachtete Abweichung. Es erzeugt weder eine Lagebewertung noch einen Auftrag. Diese Ableitungen gehören in spätere Phasen und nach `steuerung`.

## Statusmodell

Zulässig sind genau zwei Status:

- `hint`: maschineller oder noch nicht menschlich bestätigter Hinweis. Evidence darf fehlen oder bereits vorhanden sein. `confirmation` muss `null` sein.
- `confirmed`: strukturell als menschlich geprüft deklarierter Befund. Mindestens ein Evidence-Eintrag und ein `confirmation`-Objekt sind Pflicht.

`confirmation.actor_type` muss `human` und `confirmation.method` muss `human-review` sein. Der Validator prüft diese Deklaration, authentifiziert aber keine Person und beweist nicht, dass die Prüfung tatsächlich stattgefunden hat.

## Stabile Fingerprints

Der Fingerprint ist `sha256:<64 lowercase hex>` über kanonisches JSON dieser Identitätsfelder:

- Fingerprint-Schema `cabinet.finding-fingerprint.v1`;
- `rule_id`;
- `subject.kind` und `subject.id`;
- `scope.kind` und `scope.value`;
- `expectation_code`.

Nicht enthalten sind Status, Schweregrad, Confidence, Texte, tatsächlicher Wert, Zeitpunkte, Evidence und Bestätigung. Dadurch bleibt derselbe wiederkehrende Befund über mehrere Läufe stabil, während eine andere Regel, ein anderes Subjekt, ein anderer Scope oder eine andere Erwartung einen neuen Fingerprint erhält.

Ein Verzeichnis darf jeden Fingerprint höchstens einmal enthalten.

## Evidence

Jeder Evidence-Eintrag enthält:

- einen Typ;
- einen quellenbezogenen Locator in `source`;
- einen Digest mit Algorithmus und Wert;
- einen kanonischen UTC-Zeitpunkt in `captured_at`.

Zulässige Typen:

- `git_commit`
- `git_diff`
- `contract`
- `ci_run`
- `test_output`
- `evidence_pack`
- `runtime_output`
- `repository_observation`

`git_commit` benötigt `git-oid` mit 40 oder 64 Hexzeichen. Alle übrigen Typen benötigen SHA-256. Evidence wird in kanonischer Sortierung geführt und darf nicht doppelt vorkommen.

Ein Digest beweist nur die Identität der referenzierten Bytes oder des Git-Objekts. Der Validator prüft weder die Existenz noch die Wahrheit oder sachliche Relevanz der Quelle.

## Zeit

Alle Zeitpunkte verwenden kanonisches RFC3339 in UTC, ganze Sekunden und das Suffix `Z`.

Bei `confirmed` gilt:

- `confirmed_at` liegt nicht vor `observed_at`;
- kein Evidence-Zeitpunkt liegt nach `confirmed_at`.

## JSON-Oberfläche

```json
{
  "schema": "cabinet.finding.v1",
  "fingerprint": "sha256:...",
  "rule_id": "repository.head.detached",
  "subject": {"kind": "repository", "id": "lenskit"},
  "scope": {"kind": "field", "value": "head_state"},
  "expectation_code": "repository-head-on-branch",
  "status": "hint",
  "severity": "medium",
  "confidence": "high",
  "summary": "Repository HEAD is detached",
  "observation": {"expected": "branch", "actual": "detached"},
  "observed_at": "2026-06-28T00:00:00Z",
  "evidence": [],
  "confirmation": null,
  "next_check": "Return the repository to a named branch."
}
```

Der Parser lehnt unbekannte oder fehlende Felder, doppelte JSON-Schlüssel, `NaN`, `Infinity`, ungültige Digests, unsortierte Evidence und Symlinkpfade fail-closed ab.

## Ablage

Versionierte Finding-Dateien liegen direkt unter `pruefung/30 Befunde/` als `.json`. `index.md` bleibt die menschliche Navigation. Unterverzeichnisse und andere Dateitypen sind dort nicht zulässig.

Der Vertrag erlaubt zunächst ein leeres Finding-Verzeichnis. Phase 7 führt das Modell ein; reale Findings entstehen erst aus freigegebenen Prüfregeln und Evidence.

## Bedienung

Fingerprint aus den Identitätsfeldern berechnen:

```bash
python3 scripts/validate-finding.py fingerprint finding.json
```

Ein Finding prüfen:

```bash
python3 scripts/validate-finding.py validate finding.json
```

Das versionierte Finding-Verzeichnis prüfen:

```bash
python3 scripts/validate-finding.py validate-directory "pruefung/30 Befunde"
```

## Aussagegrenze

Ein grüner Validator beweist nur Vertragskonformität. Er beweist nicht:

- dass Evidence existiert oder erreichbar ist;
- dass Evidence die Beobachtung tatsächlich stützt;
- dass eine deklarierte Person selbst bestätigt hat;
- dass der Befund wahr, aktuell, vollständig oder priorisiert ist;
- dass aus dem Befund automatisch eine Aufgabe entstehen darf.
