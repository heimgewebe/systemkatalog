# Bureau Agent Routing Fit v0

Status: draft
Date: 2026-07-04
Scope: read-only fit assessment against `policy/agent-routing.json`

## Thesis / antithesis / synthesis

**Thesis:** Bureau is the right future organ for task candidates, receipts, and run-status coordination.

**Antithesis:** Directly wiring Bureau to Chronik or Grabowski now would create premature control-plane coupling.

**Synthesis:** Bureau may become a read-only consumer of summarized local evidence later, but it must not trigger Grabowski runs, Chronik movement, or downstream automation until separate gates exist.

## Policy reading

The routing policy defines Bureau as:

```text
role: coordination_and_receipts
may_mutate: false
requires_local_evidence: true
```

Relevant local-runtime routes stay with Grabowski as default executor:

- `repo_status_drift`
- `worktree_lifecycle`

That means Bureau is not the execution organ for local runtime state. Bureau can coordinate only after local evidence exists.

## Current fit

| Capability | Fit | Decision |
| --- | --- | --- |
| Task candidate tracking | strong | allowed later |
| Receipt indexing | strong | allowed later |
| Agent-run local preview summaries | medium | allowed only as summarized references |
| Chronik ingestion | weak | not allowed now |
| Grabowski task triggering | weak | not allowed now |
| Downstream automation | weak | not allowed now |

## Allowed future shape

Bureau may later store references such as:

- local preview report path;
- PR number and merge commit;
- task id and final state;
- Cabinet decision id;
- Chronik event id only after an explicit manual movement gate.

Bureau must not store raw operational transcripts, prompts, secrets, or full local runtime dumps.

## Required gates before Bureau integration

1. Bureau task model supports external evidence references without copying raw payloads.
2. Cabinet has accepted the routing policy for the task class.
3. Grabowski evidence exists and is previewed.
4. The integration is read-only first.
5. No Bureau action can trigger Grabowski or Chronik side effects.
6. A PR-level self-review confirms the boundary.

## Decision

Do not integrate Bureau now.

Next admissible Bureau slice is a read-only evidence-reference design, not an implementation that triggers runs or moves data.
