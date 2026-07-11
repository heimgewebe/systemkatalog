# Cabinet Frontier Contract v1

## Status

- Typ: Contract
- Version: 1
- Owner: Cabinet
- Modus: proposal-only frontier candidate
- Bureau-Wirkung: keine direkte Task-Erzeugung
- Producer: `scripts/write_cabinet_frontier.py`
- Validator: `scripts/validate_cabinet_frontier.py`
- Schema: `docs/contracts/cabinet-frontier-v1.schema.json`

## Zweck

`cabinet_frontier_candidate` beschreibt einen von Cabinet erkannten, Bureau-preview-faehigen Arbeitskandidaten.

Ein Frontier-Kandidat ist eine strukturierte Uebersetzung aus Cabinet-Wahrnehmung, insbesondere Maintenance-Report und Ecosystem-Signals. Er ist kein Bureau-Task, keine Queue-Aenderung, keine Freigabe, keine Grabowski-Delegation und kein Wahrheitsbeweis.

## These

Cabinet soll Inkonsistenzen, Wartungsbefunde und Live-Signale in eine Form bringen, die Bureau spaeter lesen, pruefen und ggf. importieren kann.

## Antithese

Wenn Cabinet aus einem Befund direkt Tasks schreibt oder Agenten startet, wird Cabinet zum Schatten-Orchestrator und umgeht Bureau-Gates.

## Synthese

Cabinet erzeugt nur proposal-only Frontier-Kandidaten. Bureau entscheidet spaeter ueber Preview, Review, Receipt und optionalen One-Task-Import.

## Minimales Objekt

```json
{
  "schemaVersion": 1,
  "kind": "cabinet_frontier_candidate",
  "contractVersion": "1",
  "contractPath": "docs/contracts/cabinet-frontier-v1.md",
  "schemaPath": "docs/contracts/cabinet-frontier-v1.schema.json",
  "id": "frontier:cabinet:claim.example:0123456789ab",
  "createdAt": "2026-07-08T04:00:00Z",
  "source": {
    "repository": "heimgewebe/heimgewebe-katalog",
    "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "maintenanceReportStatus": "pass",
    "maintenanceReportRef": "scripts/write_cabinet_maintenance_report.py",
    "signalRefs": ["signal:local_git:cabinet:maintenance-report:status:pass:aaaaaaaaaaaa"]
  },
  "target": {
    "repository": "heimgewebe/heimgewebe-katalog",
    "organ": "cabinet"
  },
  "proposal": {
    "title": "Run Cabinet maintenance follow-up",
    "summary": "Cabinet proposes a Bureau-previewable follow-up from a maintenance candidate.",
    "nextAction": "run_cabinet_maintenance_report_before_bureau_task_creation",
    "responsibleOrgan": "cabinet",
    "risk": "low",
    "priorityHint": "later"
  },
  "acceptance": [
    {
      "id": "proposal-only",
      "assertion": "Candidate remains proposal-only until Bureau review."
    }
  ],
  "evidence": [
    {
      "type": "cabinet_maintenance_report_candidate",
      "ref": "claim:cabinet-qa-radar-cab-qa-001-v0"
    }
  ],
  "forbiddenEffects": [
    "bureau_task_creation",
    "queue_mutation",
    "agent_dispatch",
    "merge_or_push",
    "runtime_mutation",
    "cleanup_action",
    "dump_generation",
    "authority_inference"
  ],
  "effectFlags": {
    "taskCreationAllowed": false,
    "queueMutationAllowed": false,
    "dispatchAllowed": false,
    "mergeOrPushAllowed": false,
    "runtimeMutationAllowed": false,
    "cleanupAllowed": false,
    "dumpGenerationAllowed": false,
    "authorityInferenceAllowed": false
  },
  "doesNotEstablish": [
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "autonomous_dispatch",
    "bureau_import_implemented",
    "bureau_task_created"
  ]
}
```

## Effektabschluss

Alle `effectFlags` muessen `false` sein. Ein Frontier-Kandidat darf keine Bureau-Task-Datei schreiben, keine Queue veraendern, keinen Agenten dispatchen, nicht mergen oder pushen, keine Runtime veraendern, keine Cleanup-Aktion ausloesen und keine RepoBrief-/Lenskit-Dumps erzeugen.

## Bureau-Grenze

Bureau darf Frontier-Kandidaten lesen. Ein Import ist erst in einer spaeteren Bureau-Scheibe erlaubt und braucht Review, Receipt, Kollisionspruefung und explizites Apply-Gate.

## Quellenbindung

Jeder Kandidat muss mindestens eine Evidence-Referenz und eine Source-Bindung enthalten. Wenn der Kandidat aus einem Maintenance-Report stammt, wird dessen Status und Repository-Commit ueber `source` gebunden. Wenn Live-Signale vorhanden sind, werden ihre IDs als `signalRefs` gefuehrt.

## Nicht behauptet

Ein valider Frontier-Kandidat beweist nicht:

- Task-Freigabe;
- Merge-Reife;
- Runtime-Korrektheit;
- Claim-Wahrheit;
- autonomen Dispatch;
- Bureau-Import;
- erzeugte Bureau-Task-Dateien.
