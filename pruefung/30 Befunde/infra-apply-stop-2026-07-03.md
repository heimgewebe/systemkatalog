# Infra Apply Stop 2026-07-03

## These

Apply stopped because source checkout is dirty.

## Live check

repository infra; path /home/alex/repos/infra; branch main; head equals origin/main; worktree dirty; local change scripts/ssh-cockpit/heimctl.

## Decision

Stop. No reference apply while the source checkout is dirty.

## Boundary

- No Infra Reference change.
- No generated repository surfaces changed.
- No source repository change.
- No task handoff.
