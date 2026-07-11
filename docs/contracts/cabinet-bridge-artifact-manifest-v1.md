# Systemkatalog Bridge Artifact Manifest v1

This versioned compatibility contract defines the evidence-only manifest emitted by the Heimgewebe-Systemkatalog Bridge Probe workflow.

It is a Cabinet contract. Bureau owns the import-review policy and its validator. Cabinet owns the bridge evidence bundle surface and the manifest that describes that bundle.

## Scope

The manifest records the evidence files produced during the Cabinet-to-Bureau bridge CI run.

It does not approve import. It does not create Bureau tasks. It does not mutate queues, dispatch work, write Bureau registry files, or touch runtime state.

## Producer

The manifest is produced by:

```text
scripts/write_bridge_artifact_manifest.py
```

The Heimgewebe-Systemkatalog Bridge Probe workflow runs the script after these files exist:

```text
bridge-import-policy-review.json
bridge-probe-report.json
bridge-probe-summary.md
bridge-preview.json
bridge-review.json
bridge-receipt.json
```

## Required manifest shape

The manifest JSON object must contain:

- `schemaVersion: 1`
- `kind: cabinet_bridge_artifact_manifest`
- `contractVersion: "1"`
- `contractPath: docs/contracts/cabinet-bridge-artifact-manifest-v1.md`
- `schemaPath: docs/contracts/cabinet-bridge-artifact-manifest-v1.schema.json`
- `mode: evidence_only`
- `bureauRef`: the pinned Bureau commit SHA used by the workflow
- `artifactCount: 6`
- `artifacts`: the ordered artifact list
- `effectFlags`: all false

## Required artifact list

The ordered artifact list is:

1. `bridge-import-policy-review.json` with kind `bureau.cabinet_bridge_import_review_contract_policy_review`
2. `bridge-probe-report.json` with kind `cabinet_bureau_bridge_probe`
3. `bridge-probe-summary.md` with kind `markdown_summary`
4. `bridge-preview.json` with kind `cabinet_bridge_promotion_preview`
5. `bridge-review.json` with kind `cabinet_bridge_preview_review_gate`
6. `bridge-receipt.json` with kind `cabinet_bridge_review_receipt`

## Effect closure

For every JSON artifact, if any of these fields is present, it must be `false`:

```text
importAllowed
dispatchAllowed
queueMutationAllowed
taskCreationAllowed
```

The manifest itself must also carry these fields under `effectFlags`, all set to `false`.

## Import review markers

The manifest writer must additionally verify:

```text
bridge-import-policy-review.json.importReviewRequired == true
bridge-receipt.json.importReviewRequired == true
```

## Stop conditions

Manifest creation must stop if:

- any required artifact is missing
- a JSON artifact has the wrong `kind`
- a JSON artifact has an effect flag set to `true`
- policy review or receipt does not require import review
- the markdown summary is empty
- `bureauRef` is empty

## Schema

The JSON schema for the manifest is:

```text
docs/contracts/cabinet-bridge-artifact-manifest-v1.schema.json
```

The schema describes the manifest output. The script remains the executable contract for validating the input artifact bundle before the manifest is written.

## Compatibility naming

The `cabinet_*` JSON kind values are retained as versioned wire-format identifiers so historical receipts remain verifiable. They are not executable aliases or current repository names.
