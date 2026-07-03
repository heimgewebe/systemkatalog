#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1

cd "$REPO_ROOT"

echo "=== Git-Whitespace ==="
EMPTY_TREE="$(git hash-object -t tree /dev/null)"
git diff --check "$EMPTY_TREE" HEAD
echo "Git-Whitespace: PASS"

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
    echo "FAIL: Working tree is not clean (untracked files and local modifications must be empty for accurate CI)."
    exit 1
fi

echo "=== Repository Contract Checker ==="
python3 scripts/ci/check-repository-contract.py --repo-root "$REPO_ROOT" --tree-ish HEAD

echo "=== Repository Inventory ==="
python3 scripts/build-repository-index.py --check --repo-root "$REPO_ROOT"
echo "Repository Inventory: PASS"

echo "=== Reference Refresh Proposal Guard ==="
python3 scripts/check-reference-refresh-proposals.py --repo-root "$REPO_ROOT"
echo "Reference Refresh Proposal Guard: PASS"

echo "=== Materialize HEAD Snapshot ==="
SNAPSHOT_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$SNAPSHOT_ROOT"' EXIT
git archive --format=tar HEAD | tar -xf - -C "$SNAPSHOT_ROOT"

cd "$SNAPSHOT_ROOT"

echo "=== JSON ==="
find . -type f -name '*.json' -print0 | while IFS= read -r -d '' f; do
    python3 -m json.tool "$f" >/dev/null
done
echo "JSON: PASS"

echo "=== Python ==="
find . -type f -name '*.py' -print0 | while IFS= read -r -d '' f; do
    python3 -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$f"
done
echo "Python: PASS"

echo "=== Bash ==="
find . -type f -print0 | while IFS= read -r -d '' f; do
    if [[ -f "$f" ]]; then
        line=$(head -n 1 "$f" 2>/dev/null || true)
        if [[ "$line" =~ ^#!(.*)bash ]]; then
            bash -n "$f"
        fi
    fi
done

for f in ops/bin/* ops/install/*.sh scripts/cabinet-safe-export.sh scripts/ci/*.sh; do
    if [[ -f "$f" ]]; then
        bash -n "$f"
    fi
done
echo "Bash: PASS"

echo "=== Layout ==="
python3 scripts/check-cabinet-layout.py --mode repository "$SNAPSHOT_ROOT"

echo "TARGET-PROOF: CABINET REPOSITORY CONTRACT VALID"
