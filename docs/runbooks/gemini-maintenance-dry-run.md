# Gemini Maintenance Dry Run Runbook

Status: manual-only
Owner: Cabinet
Bureau task: `CABINET-GEMINI-MAINT-V1-T004`
Primary path: local personal Gemini CLI login
Optional path: `.github/workflows/gemini-maintenance-dry-run.yml` with API/Vertex-style machine auth

## Purpose

This runbook describes the first manual, artifact-only Gemini maintenance dry run.

The run is not a schedule, not a Cabinet finding import, not a Bureau task import, not a Grabowski dispatch and not a runtime action.

## Decision

Use the **local personal Gemini CLI path** when the operator wants to use a personal Google/Gemini CLI login instead of a GitHub Actions API key.

The GitHub Actions workflow remains an optional API-auth path. It is not the preferred path for a personal Google AI Pro / Google-account workflow, because GitHub Actions is a headless CI environment and cannot use an interactive personal browser login safely.

## Local personal-login path

### Preconditions

- Cabinet is checked out locally.
- Gemini CLI is installed.
- `gemini` is available on `PATH`.
- The operator has already run `gemini` once locally and completed the Google sign-in flow.
- No `GEMINI_API_KEY` repository secret is required for this path.

Gemini CLI supports signing in with Google in an interactive terminal. Its upstream README describes this as the first authentication option and says to start `gemini`, then choose **Sign in with Google** when prompted.

### Local command

Run from the Cabinet repository root:

```bash
python3 scripts/run_gemini_maintenance_local_dry_run.py --json
```

If the scan is blocked but artifacts should still be retained and reviewed, run:

```bash
python3 scripts/run_gemini_maintenance_local_dry_run.py --allow-blocked --json
```

The command:

1. builds `pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json`,
2. writes the exact prompt used for the run,
3. invokes local `gemini` with the personal login,
4. stores raw Gemini stdout/stderr,
5. unwraps Gemini CLI JSON output when stdout contains a `response` field,
6. extracts and validates `gemini-maintenance-dry-run-scan.json`,
7. writes a review scaffold.

### Local expected artifacts

The local path writes:

- `pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-gemini-wrapper.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-gemini-summary.txt`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-gemini-error.txt`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-raw-output.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-scan.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-review.md`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-prompt.md`

## Optional GitHub Actions API-auth path

Use this path only when API-key, Vertex, or other reviewed machine authentication is desired.

### Preconditions

- Cabinet `main` contains `.github/workflows/gemini-maintenance-dry-run.yml`.
- A reviewed machine auth method exists, such as `GEMINI_API_KEY`, Vertex AI, or another supported CI auth option.
- The workflow input confirmation is exactly:

```text
RUN_ARTIFACT_ONLY_GEMINI_DRY_RUN
```

### Manual GitHub UI path

1. Open GitHub Actions for `heimgewebe/heimgewebe-katalog`.
2. Select **Gemini Maintenance Dry Run**.
3. Use **Run workflow** on `main`.
4. Enter `RUN_ARTIFACT_ONLY_GEMINI_DRY_RUN` as confirmation.
5. Start the workflow.

### Expected GitHub artifact

The workflow uploads one artifact named `gemini-maintenance-dry-run` containing:

- `pruefung/10 Laeufe/gemini-maintenance-evidence-packet-v1.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-raw-output.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-scan.json`
- `pruefung/10 Laeufe/gemini-maintenance-dry-run-review.md`

## Expected success condition

The dry run is successful only if `gemini-maintenance-dry-run-scan.json` validates as a completed `cabinet_gemini_maintenance_scan`.

A blocked scan artifact is still useful evidence, but it does not complete T004.

## Review checklist

Review the uploaded or locally written artifacts before any Bureau or schedule decision.

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

A failed workflow or local run can still be informative.

Common cases:

- Local Gemini CLI not installed: local runner cannot start.
- Local Gemini CLI not signed in: personal-login availability is not established.
- Missing or invalid machine auth on GitHub Actions: CI-auth availability is not established.
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

Only after a reviewed dry-run artifact exists may `CABINET-GEMINI-MAINT-V1-T004` move from `blocked` to `verified`.

`CABINET-GEMINI-MAINT-V1-T005` remains blocked by T004 and must not decide scheduling before a reviewed dry-run artifact exists.
