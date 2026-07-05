# Cabinet QA Radar v1

Status: draft
Datum: 2026-07-05
Owner: Cabinet
Bridge candidate: `claim:cabinet-qa-radar-cab-qa-001-v0`

## These

Cabinet should scan the ecosystem registry, bridge policy and maintenance-facing evidence for inconsistency, stale claims and missing handoff readiness.

## Antithese

Cabinet must not become the dump producer, task executor, auto-dispatcher or runtime repair organ. The scanner must not create Bureau tasks, trigger Grabowski, merge, push, clean up or mutate runtime state.

## Synthese

CAB-QA-RADAR is a read-only coherence radar. It produces a maintenance report that classifies findings and Bureau candidate readiness, while every report remains a candidate signal and never an authorization.

## Scope

The first slice, `CAB-QA-001`, covers:

- registry and bridge input presence;
- claim freshness from `expires_at`;
- local evidence-path existence when evidence is a Cabinet repo path;
- handoff readiness for admissible Bureau candidates;
- explicit effect-closure flags;
- an epistemic gap for externally generated RepoBrief/Lenskit dumps until their manifest shape, path, cadence and hash contract are known.

## Out of scope

This slice does not:

- generate RepoBrief or Lenskit dumps;
- query GitHub, CI or runtime systems;
- create Bureau tasks;
- schedule jobs or heartbeats;
- dispatch Grabowski;
- mutate repositories or runtime;
- prove semantic truth.

## Authority order

- GitHub is primary truth for PR, branch and review state.
- CI is primary truth for check state.
- Runtime, systemd and logs are primary truth for service state.
- Contracts, schemas and tests are primary truth for repository invariants.
- Cabinet registry and map surfaces are semantic navigation and evidence organization, not external truth.

## Finding classes

| Class | Meaning |
|---|---|
| `consistency` | Registry, claim, bridge or reference mismatch. |
| `error` | Missing or malformed local input that prevents reliable interpretation. |
| `freshness` | Expired or near-expiring claim or evidence. |
| `handoff` | A candidate is not Bureau-ready. |
| `authority` | A claim appears to use the wrong source type for its authority. |
| `risk` | A finding may affect safety, data, release or operator load. |

## Severity classes

| Severity | Meaning |
|---|---|
| `P0` | Secret, data-loss, runtime, deploy or safety danger. |
| `P1` | Wrong readiness, broken gate or blocking main-path defect. |
| `P2` | Drift, stale evidence, missing proof or blocked handoff. |
| `P3` | Hygiene, style, weak link or low-risk redundancy. |

## Bureau boundary

Bureau may consume the report and candidate claim read-only. A Bureau-ready candidate still means only this: the candidate has the minimum fields needed for Bureau to decide whether a task candidate should be created.

It does not establish:

- task approval;
- merge readiness;
- runtime correctness;
- claim truth;
- autonomous dispatch;
- Bureau import completion.

## Alternative Sinnachse

The scanner is not a larger Cabinet brain. It is a smaller Cabinet conscience. It asks whether a proposed context is coherent enough to deserve work, not whether work should start automatically.

## Epistemische Leere

External RepoBrief/Lenskit automation is intentionally outside Cabinet, but its current manifest, path convention, cadence, hash surface and retention policy are not specified in this repository. That is needed for a full external-dump freshness scan.
