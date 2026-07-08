# Cabinet Gemini Maintenance Scan Contract v1

## Status

- Typ: Contract
- Version: 1
- Owner: Cabinet
- Modus: Gemini output, artifact-only, proposal-only
- Bureau-Wirkung: keine direkte Task-Erzeugung
- Validator: `scripts/validate_gemini_maintenance_scan.py`
- Schema: `docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json`
- Execution Manifest: `policy/gemini-maintenance-execution-manifest.v1.json`

## Zweck

`cabinet_gemini_maintenance_scan` beschreibt das einzig zulaessige Output-Format fuer einen spaeteren Gemini-Maintenance-Dry-Run.

Der Output darf Befunde strukturieren. Er darf keine GitHub Issues, Pull Requests oder Kommentare erzeugen, keine Bureau-Tasks schreiben, keine Queue mutieren, Grabowski nicht dispatchen, nicht pushen oder mergen, keine Runtime veraendern, keine Secrets anfordern, keine Dumps erzeugen und keine Cleanup-Aktion ausloesen.

## Organ-Grenze

Cabinet darf diesen Output als untrusted Artifact lesen und validieren. Bureau darf daraus nur nach separatem Review und Apply-Gate Arbeit ableiten. Grabowski darf daraus keine Aktion ableiten, solange kein Bureau-Task oder Operator-Gate existiert.

## Minimales Objekt

```json
{
  "schemaVersion": 1,
  "kind": "cabinet_gemini_maintenance_scan",
  "contractVersion": "1",
  "contractPath": "docs/contracts/cabinet-gemini-maintenance-scan-v1.md",
  "schemaPath": "docs/contracts/cabinet-gemini-maintenance-scan-v1.schema.json",
  "id": "gemini-scan:cabinet:2026-07-08T14-00-00Z",
  "createdAt": "2026-07-08T14:00:00Z",
  "status": "completed",
  "source": {
    "repository": "heimgewebe/cabinet",
    "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "executionManifestRef": "policy/gemini-maintenance-execution-manifest.v1.json",
    "evidenceManifestRef": "pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json",
    "inputRefs": ["evidence:AGENTS.md"]
  },
  "lane": {
    "id": "cabinet-gemini-maintenance",
    "bureauTask": "CABINET-GEMINI-MAINT-V1-T002",
    "mode": "manual_dry_run"
  },
  "findings": {
    "observed": [
      {
        "id": "finding:observed:example",
        "title": "Observed finding title",
        "summary": "A directly evidenced statement from the curated packet.",
        "severity": "low",
        "confidence": "medium",
        "evidenceRefs": ["evidence:AGENTS.md#L1-L10"],
        "recommendedNextAction": "review_only"
      }
    ],
    "plausible": [],
    "speculative": []
  },
  "effectFlags": {
    "issueCreated": false,
    "prCreated": false,
    "commentCreated": false,
    "taskCreated": false,
    "queueMutated": false,
    "grabowskiDispatched": false,
    "pushOrMerge": false,
    "runtimeMutated": false,
    "secretRequested": false,
    "dumpGenerated": false,
    "cleanupAction": false
  },
  "forbiddenEffects": [
    "issue_creation",
    "pr_creation",
    "comment_creation",
    "bureau_task_creation",
    "queue_mutation",
    "grabowski_dispatch",
    "merge_or_push",
    "runtime_mutation",
    "secret_request",
    "dump_generation",
    "cleanup_action"
  ],
  "doesNotEstablish": [
    "task_approval",
    "claim_truth",
    "merge_readiness",
    "runtime_correctness",
    "bureau_import",
    "autonomous_dispatch",
    "bureau_task_created",
    "schedule_approval",
    "gemini_schedulability"
  ]
}
```

## Epistemik

Findings werden strikt getrennt:

- `observed`: direkt aus dem kuratierten Evidence-Paket belegbar; `evidenceRefs` muss nicht leer sein.
- `plausible`: nachvollziehbare Vermutung aus Evidence-Kontext; darf nicht als Claim-Wahrheit gelten.
- `speculative`: Hypothese oder Warnsignal; darf nur als Review-Hinweis gelesen werden.

Observed Findings ohne Evidence-Referenz sind invalid.

## Effektabschluss

Alle `effectFlags` muessen existieren und `false` sein. Der Validator verwirft jeden Output, der irgendeine Wirkung behauptet oder freischaltet.

## Nicht behauptet

Ein valider Gemini-Maintenance-Scan beweist nicht:

- Task-Freigabe;
- Claim-Wahrheit;
- Merge-Reife;
- Runtime-Korrektheit;
- Bureau-Import;
- autonomen Dispatch;
- erzeugte Bureau-Task-Dateien;
- Scheduling-Freigabe;
- Gemini-Schedulability.
