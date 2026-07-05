# Cabinet Maintenance Report v1

Status: draft
Owner: Cabinet
Schema: `docs/contracts/cabinet-maintenance-report-v1.schema.json`
Producer: `scripts/write_cabinet_maintenance_report.py`

## Purpose

The Cabinet maintenance report is a deterministic, read-only scan result for the CAB-QA-RADAR surface.

It records:

- the Cabinet source commit;
- the scan date;
- effect-closure flags;
- summary counts by severity;
- findings for consistency, error, freshness, handoff, authority and risk;
- Bureau candidate readiness;
- epistemic gaps;
- explicit non-claims.

## Boundary

The report is maintenance evidence. It is not a task queue, not a dispatch order, not a runtime check and not a semantic proof.

It must not:

- create Bureau tasks;
- delegate Grabowski;
- merge or push;
- mutate runtime;
- clean up files;
- generate RepoBrief or Lenskit dumps;
- infer truth from maps.

## Required effect flags

Every report must contain these flags and every value must be `false`:

- `bureauTaskCreationAllowed`
- `grabowskiDelegationAllowed`
- `mergeOrPushAllowed`
- `runtimeMutationAllowed`
- `cleanupAllowed`
- `dumpGenerationAllowed`
- `authorityInferenceFromMapAllowed`

## Report status

`summary.status` is derived from findings:

- `fail` when at least one `P0` or `P1` finding exists;
- `warn` when there are only `P2` or `P3` findings, or epistemic gaps;
- `pass` when there are no findings and no epistemic gaps.

The producer's default `--check` validates report shape and exits successfully even when the report status is `warn`. A stricter caller may use `--strict` to fail on report status `fail`.

## Bureau candidates

A Bureau candidate may be listed only when the source claim:

- has an admissible bridge status;
- has non-empty evidence;
- has `expires_at` or `expires_at_or_refresh_hint`;
- is not expired at scan date;
- has `next_action`;
- has `responsible_organ`.

A listed candidate is still proposal-only.

## Non-claims

A valid report does not establish:

- claim truth;
- runtime correctness;
- merge readiness;
- task approval;
- Bureau import completion;
- autonomous dispatch;
- external dump freshness completeness.
