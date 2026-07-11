# Lenskit Conflict Stop 2026-07-04

## These

Lenskit remains the only repository observation candidate, but refresh/apply must stop.

## Live check

repository: lenskit
path: /home/alex/repos/lenskit
branch: rb-artifact-ref-contract
head: 20768d7eff2709ccc451e0f3f0d9d7d3ccbbc8be
origin_main: 20768d7eff2709ccc451e0f3f0d9d7d3ccbbc8be
open_pr_for_branch: none
worktree: conflict
status: A merger/lenskit/contracts/repobrief-artifact-ref.v1.schema.json
status: UU merger/lenskit/tests/test_repobrief_snapshot_cli.py

## Decision

Stop. Do not update the Lenskit Repository Reference while the source checkout contains an unmerged conflict.

## Boundary

- No Lenskit Reference change.
- No generated repository surfaces changed.
- No Lenskit source repository change.
- No Bureau task.
