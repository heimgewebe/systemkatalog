#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_REPO="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_REPO"' EXIT

git clone --no-hardlinks --quiet "$REAL_REPO" "$TEMP_REPO"
cd "$TEMP_REPO"
git config user.name "System Catalog CI"
git config user.email "system-catalog-ci@example.invalid"
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
mkdir -p .agents/.runtime
echo token > .agents/.runtime/token
git add -f .agents/.runtime/token
git commit -m forbidden >/dev/null
expect_failure "forbidden agent runtime" "agent runtime/config"

reset_state
echo secret > runtime.env
git add -f runtime.env
git commit -m forbidden >/dev/null
expect_failure "forbidden env" "env file"

reset_state
python3 - <<'PY'
import json
p='ops/manifest.json'; d=json.load(open(p)); d['schema']='wrong'; json.dump(d,open(p,'w'))
PY
git commit -am schema >/dev/null
expect_failure "wrong schema" "manifest.schema"

reset_state
python3 - <<'PY'
import json
p='ops/manifest.json'; d=json.load(open(p)); d['service']['port']=4100; json.dump(d,open(p,'w'))
PY
git commit -am port >/dev/null
expect_failure "wrong catalog port" "manifest.service mismatch"

reset_state
python3 - <<'PY'
import json
p='ops/manifest.json'; d=json.load(open(p)); d['executables'].pop(); json.dump(d,open(p,'w'))
PY
git commit -am executable >/dev/null
expect_failure "missing executable" "manifest.executables mismatch"

reset_state
git update-index --chmod=-x ops/bin/heimgewebe-systemkatalog
git commit -m mode >/dev/null
git reset --hard HEAD >/dev/null
expect_failure "wrong executable mode" "git mode mismatch"

reset_state
printf '#!/usr/bin/env bash\nexit 0\n' > ops/bin/cabinet
chmod +x ops/bin/cabinet
git add ops/bin/cabinet
git commit -m legacy >/dev/null
expect_failure "legacy runtime source restored" "retired external-app source still tracked"

reset_state
printf '#!/usr/bin/env bash\nif true\n' > ops/install/install-local-runtime.sh
git add ops/install/install-local-runtime.sh
git commit -m syntax >/dev/null
out=$(./scripts/ci/validate-repository.sh 2>&1 || true)
if grep -qF "TARGET-PROOF: CABINET REPOSITORY CONTRACT VALID" <<<"$out"; then
  echo "FAIL: target proof printed before failure"; exit 1
fi

echo "TARGET-PROOF: CABINET REPOSITORY VALIDATOR TESTS PASS"
