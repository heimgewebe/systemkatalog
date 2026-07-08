# Gemini Maintenance Dry Run Runbook

Status: manual-only
Owner: Cabinet
Bureau task: `CABINET-GEMINI-MAINT-V1-T004`
Workflow: `.github/workflows/gemini-maintenance-dry-run.yml`

## Purpose

This runbook describes the first manual, artifact-only Gemini maintenance dry run.

The run is not a schedule, not a Cabinet finding import, not a Bureau task import, not a Grabowski dispatch and not a runtime action.

## Preconditions

- Cabinet `main` contains `.github/workflows/gemini-maintenance-dry-run.yml`.
- The repository secret `GEMINI_API_KEY` exists if API-key authentication is used.
- The workflow input confirmation is exactly:

```text
RUN_ARTIFACT_ONLY_GEMINI_DRY_RUN
```

## Manual GitHub UI path

1. Open GitHub Actions for `heimgewebe/cabinet`.
2. Select **Gemini Maintenance Dry Run**.
3. Use **Run workflow** on `main`.
4. Enter `RUN_ARTIFACT_ONLY_GEMINI_DRY_RUN` as confirmation.
5. Start the workflow.

## Expected artifacts

The run uploads one artifact named `gemini-maintenance-dry-run` containing:

- `pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-raw-output.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-scan.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-review.md`

## Expected success condition

The workflow is successful only if `gemini-maintenance-dry-run-scan.json` validates as a completed `cabinet_gemini_maintenance_scan`.

A blocked scan artifact is still useful evidence, but it does not complete T004.

## Review checklist

Review the uploaded artifacts before any Bureau or schedule decision.

Check:

- Did Gemini produce strict JSON matching `docs/contracts/cabinet-gemini-maintenance-scan-v1.md`?
- Are all `effectFlags` false?
- Are observed findings backed by packet evidence refs?
- Are plausible and speculative findings labelled correctly?
- Did Gemini hallucinate missing refs?
- Did it overclaim task approval, claim truth, merge readiness, runtime correctness, Bureau import, autonomous dispatch or schedule approval?
- Are findings useful enough to justify another manual run?
- Are false positives low enough to consider later scheduling?

## Failure interpretation

A failed workflow can still be informative.

Common cases:

- Missing or invalid `GEMINI_API_KEY`: Gemini availability is not established.
- Invalid Gemini JSON: scan quality is not established.
- Blocked scan artifact: raw output must be reviewed manually.
- Effect flag violation: output is invalid and must not feed Bureau.
- Missing evidence refs on observed findings: output is invalid and must not feed Bureau.

## Explicit non-effects

This runbook does not approve:

- scheduled Gemini scans
- GitHub issue creation
- GitHub pull request creation
- GitHub comments
- Bureau task creation
- Bureau queue mutation
- Grabowski dispatch
- push or merge authority
- runtime mutation
- cleanup actions

## Next state transition

Only after a reviewed workflow artifact exists may `CABINET-GEMINI-MAINT-V1-T004` move from `blocked` to `verified`.

`CABINET-GEMINI-MAINT-V1-T005` remains blocked by T004 and must not decide scheduling before a reviewed dry-run artifact exists.
