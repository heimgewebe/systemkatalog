#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain=v1 --untracked-files=all)" ]]; then
  echo "FAIL: Working tree is not clean; commit or stash changes before repository validation."
  exit 1
fi
SOURCE_COMMIT="$(git rev-parse HEAD)"

echo "=== Git whitespace ==="
EMPTY_TREE="$(git hash-object -t tree /dev/null)"
git diff --check "$EMPTY_TREE" HEAD

echo "=== Tracked repository contract ==="
python3 scripts/ci/check-repository-contract.py --repo-root "$REPO_ROOT" --tree-ish HEAD

SNAPSHOT_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$SNAPSHOT_ROOT"' EXIT
git archive --format=tar HEAD | tar -xf - -C "$SNAPSHOT_ROOT"
cd "$SNAPSHOT_ROOT"

echo "=== JSON syntax ==="
find . -type f -name '*.json' -print0 | while IFS= read -r -d '' file; do
  python3 -m json.tool "$file" >/dev/null
done

echo "=== Python syntax ==="
find . -type f -name '*.py' -not -path './docs/archive/*' -print0 | while IFS= read -r -d '' file; do
  python3 -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$file"
done

echo "=== Bash syntax ==="
find ops scripts/ci -type f -print0 | while IFS= read -r -d '' file; do
  first="$(head -n 1 "$file" 2>/dev/null || true)"
  if [[ "$first" =~ ^#!(.*)bash ]]; then
    bash -n "$file"
  fi
done

echo "=== Catalog contracts ==="
python3 scripts/validate_system_catalog.py
python3 scripts/validate_ecosystem_map.py
python3 scripts/render_system_catalog.py --check
python3 scripts/render_ecosystem_registry_map.py --check
python3 scripts/write_ecosystem_map_artifact_manifest.py --check --source-commit "$SOURCE_COMMIT"
python3 scripts/serve_system_catalog.py --check

echo "=== Unit tests ==="
python3 -m unittest discover -s scripts/tests -p 'test_*.py'

echo "TARGET-PROOF: SYSTEMKATALOG REPOSITORY CONTRACT VALID"
