#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_REPO="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_REPO"' EXIT

git clone --no-hardlinks --quiet "$REAL_REPO" "$TEMP_REPO"
cd "$TEMP_REPO"
git config user.name "Systemkatalog CI"
git config user.email "systemkatalog-ci@example.invalid"
BASE="$(git rev-parse HEAD)"
reset_state() { git reset --hard "$BASE" >/dev/null; git clean -ffdx >/dev/null; }
expect_failure() {
  local label="$1" expected="$2" out
  echo "=== $label ==="
  if out=$(./scripts/ci/validate-repository.sh 2>&1); then
    echo "FAIL: expected validation failure"; exit 1
  fi
  grep -qF "$expected" <<<"$out" || { echo "FAIL: missing marker $expected"; echo "$out"; exit 1; }
  echo PASS
}

reset_state
./scripts/ci/validate-repository.sh >/dev/null
echo "PASS: unchanged commit"

reset_state
mkdir -p steuerung
echo stale > steuerung/index.md
git add steuerung/index.md
git commit -m forbidden-room >/dev/null
expect_failure "legacy room restored" "legacy room root: steuerung"

reset_state
echo secret > runtime.env
git add -f runtime.env
git commit -m forbidden-env >/dev/null
expect_failure "forbidden env" "env file: runtime.env"

reset_state
printf '#!/usr/bin/env python3\n' > scripts/serve_system_catalog.py
git add scripts/serve_system_catalog.py
git commit -m restored-server >/dev/null
expect_failure "HTTP server source restored" "retired Systemkatalog runtime source still tracked"

reset_state
mkdir -p ops/systemd
printf '[Service]\nExecStart=/bin/false\n' > ops/systemd/systemkatalog.service.tmpl
git add ops/systemd/systemkatalog.service.tmpl
git commit -m restored-unit >/dev/null
expect_failure "systemd source restored" "retired Systemkatalog runtime source still tracked"

reset_state
python3 - <<'PY'
import json
p='policy/system-catalog.v1.json'; d=json.load(open(p)); d['runtimeProjection']={'service':'systemkatalog.service'}; json.dump(d,open(p,'w'))
PY
git commit -am restored-runtime-policy >/dev/null
expect_failure "runtime policy restored" "runtimeProjection must remain absent"

reset_state
git rm rendered/system-catalog.md >/dev/null
git commit -m missing-static-surface >/dev/null
expect_failure "static projection missing" "required static surface missing"

reset_state
printf '#!/usr/bin/env python3\nif True print("broken")\n' > scripts/render_system_catalog.py
git add scripts/render_system_catalog.py
git commit -m syntax-error >/dev/null
out=$(./scripts/ci/validate-repository.sh 2>&1 || true)
if grep -qF "TARGET-PROOF: SYSTEMKATALOG REPOSITORY CONTRACT VALID" <<<"$out"; then
  echo "FAIL: target proof printed before syntax failure"; exit 1
fi

echo "TARGET-PROOF: SYSTEMKATALOG REPOSITORY VALIDATOR TESTS PASS"
