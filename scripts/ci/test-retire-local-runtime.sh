#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
REAL_HEAD_BEFORE="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_BEFORE="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"
[[ -z "$REAL_STATUS_BEFORE" ]] || { echo "FAIL: Real repository is not clean before test."; exit 1; }

TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_ROOT" /tmp/systemkatalog-retire.out' EXIT
TEMP_REPO="$TEMP_ROOT/repo"
TEMP_HOME="$TEMP_ROOT/home"
STUB_BIN="$TEMP_ROOT/stub-bin"
SYSTEMCTL_LOG="$TEMP_ROOT/systemctl.log"
SYSTEMCTL_STATE="$TEMP_ROOT/systemctl.state"
mkdir -p "$TEMP_REPO" "$TEMP_HOME" "$STUB_BIN"
touch "$SYSTEMCTL_LOG"
printf 'active=active\nenabled=enabled\nfail_reload=0\n' > "$SYSTEMCTL_STATE"
git -C "$REAL_REPO" archive --format=tar HEAD | tar -xf - -C "$TEMP_REPO"
git -C "$TEMP_REPO" init -q
git -C "$TEMP_REPO" config user.name systemkatalog-ci
git -C "$TEMP_REPO" config user.email systemkatalog-ci@example.invalid
git -C "$TEMP_REPO" add .
git -C "$TEMP_REPO" commit -qm snapshot
TEMP_HEAD="$(git -C "$TEMP_REPO" rev-parse HEAD)"

cat > "$STUB_BIN/systemctl" <<'EOF_SYSTEMCTL'
#!/usr/bin/env bash
set -Eeuo pipefail
echo "$*" >> "$SYSTEMCTL_LOG"
active="$(sed -n 's/^active=//p' "$SYSTEMCTL_STATE")"
enabled="$(sed -n 's/^enabled=//p' "$SYSTEMCTL_STATE")"
fail_reload="$(sed -n 's/^fail_reload=//p' "$SYSTEMCTL_STATE")"
case "$*" in
  "--user show systemkatalog.service -p ActiveState --value") echo "$active" ;;
  "--user show systemkatalog.service -p MainPID --value") echo 999999 ;;
  "--user is-enabled systemkatalog.service") echo "$enabled"; [[ "$enabled" == enabled ]] ;;
  "--user is-active --quiet systemkatalog.service") [[ "$active" == active ]] ;;
  "--user is-enabled --quiet systemkatalog.service") [[ "$enabled" == enabled ]] ;;
  "--user stop systemkatalog.service") sed -i 's/^active=.*/active=inactive/' "$SYSTEMCTL_STATE" ;;
  "--user disable systemkatalog.service") sed -i 's/^enabled=.*/enabled=disabled/' "$SYSTEMCTL_STATE" ;;
  "--user daemon-reload")
    if [[ "$fail_reload" == 1 ]]; then
      sed -i 's/^fail_reload=.*/fail_reload=0/' "$SYSTEMCTL_STATE"
      exit 1
    fi
    ;;
  "--user reset-failed systemkatalog.service") ;;
  "--user enable systemkatalog.service") sed -i 's/^enabled=.*/enabled=enabled/' "$SYSTEMCTL_STATE" ;;
  "--user start systemkatalog.service") sed -i 's/^active=.*/active=active/' "$SYSTEMCTL_STATE" ;;
  *) echo "unexpected systemctl call: $*" >&2; exit 1 ;;
esac
EOF_SYSTEMCTL
chmod +x "$STUB_BIN/systemctl"

run_installer() {
  env -i HOME="$TEMP_HOME" USER=catalog-ci LOGNAME=catalog-ci \
    PATH="$STUB_BIN:/usr/local/bin:/usr/bin:/bin" \
    SYSTEMCTL_LOG="$SYSTEMCTL_LOG" SYSTEMCTL_STATE="$SYSTEMCTL_STATE" \
    bash "$TEMP_REPO/ops/install/install-local-runtime.sh"
}
run_retirement() {
  env -i HOME="$TEMP_HOME" USER=catalog-ci LOGNAME=catalog-ci \
    PATH="$STUB_BIN:/usr/local/bin:/usr/bin:/bin" \
    SYSTEMCTL_LOG="$SYSTEMCTL_LOG" SYSTEMCTL_STATE="$SYSTEMCTL_STATE" \
    SYSTEMKATALOG_RETIREMENT_TIMESTAMP="${RETIRE_TS:-20260712T120000Z}" \
    bash "$TEMP_REPO/ops/install/retire-local-runtime.sh" "$@"
}

run_installer >/dev/null
: > "$SYSTEMCTL_LOG"
touch "$TEMP_HOME/.local/bin/unrelated-tool"

printf '%s\n' "=== Dry run has no mutation ==="
run_retirement --dry-run
[[ -f "$TEMP_HOME/.config/systemd/user/systemkatalog.service" ]]
[[ -f "$TEMP_HOME/.local/bin/systemkatalog" ]]
[[ -f "$TEMP_HOME/.local/bin/systemkatalogctl" ]]
[[ -f "$TEMP_HOME/.local/bin/unrelated-tool" ]]
[[ ! -e "$TEMP_HOME/.local/state/systemkatalog/runtime-retirements/20260712T120000Z" ]]
[[ "$(wc -l < "$SYSTEMCTL_LOG")" -eq 0 ]]
TEMP_STATUS_AFTER_DRY_RUN="$(git -C "$TEMP_REPO" status --porcelain=v1 --untracked-files=all)"
if [[ -n "$TEMP_STATUS_AFTER_DRY_RUN" ]]; then
  printf 'FAIL: dry run dirtied shadow repository:\n%s\n' "$TEMP_STATUS_AFTER_DRY_RUN" >&2
  exit 1
fi

printf '%s\n' "=== Apply requires authorization and head binding ==="
if run_retirement --apply --expected-head "$TEMP_HEAD" >/tmp/systemkatalog-retire.out 2>&1; then
  echo "FAIL: apply accepted missing authorization"; exit 1
fi
grep -q "Autorisierungsreferenz" /tmp/systemkatalog-retire.out || { cat /tmp/systemkatalog-retire.out; exit 1; }
[[ -f "$TEMP_HOME/.local/bin/systemkatalog" ]]
if run_retirement --apply --authorization-reference TEST-T001 --expected-head "$TEMP_HEAD" >/tmp/systemkatalog-retire.out 2>&1; then
  echo "FAIL: apply accepted a non-Bureau authorization reference"; exit 1
fi
grep -q "Format Bureau:<TASK-ID>" /tmp/systemkatalog-retire.out || { cat /tmp/systemkatalog-retire.out; exit 1; }
[[ -f "$TEMP_HOME/.local/bin/systemkatalog" ]]
if run_retirement --apply --authorization-reference Bureau:TEST-T001 --expected-head 0000000000000000000000000000000000000000 >/tmp/systemkatalog-retire.out 2>&1; then
  echo "FAIL: apply accepted wrong repository head"; exit 1
fi
grep -q "Repository-HEAD driftet" /tmp/systemkatalog-retire.out || { cat /tmp/systemkatalog-retire.out; exit 1; }
[[ -f "$TEMP_HOME/.local/bin/systemkatalog" ]]

printf '%s\n' "=== Drift blocks retirement before mutation ==="
printf 'drift\n' >> "$TEMP_HOME/.local/bin/systemkatalog"
if run_retirement --apply --authorization-reference Bureau:TEST-T001 --expected-head "$TEMP_HEAD" >/tmp/systemkatalog-retire.out 2>&1; then
  echo "FAIL: apply accepted installed binary drift"; exit 1
fi
grep -q "Installiertes Programm driftet" /tmp/systemkatalog-retire.out || { cat /tmp/systemkatalog-retire.out; exit 1; }
[[ "$(wc -l < "$SYSTEMCTL_LOG")" -eq 0 ]]
cp "$TEMP_REPO/ops/bin/systemkatalog" "$TEMP_HOME/.local/bin/systemkatalog"
chmod 0755 "$TEMP_HOME/.local/bin/systemkatalog"

printf '%s\n' "=== Mid-flight failure restores the prior runtime ==="
sed -i 's/^fail_reload=.*/fail_reload=1/' "$SYSTEMCTL_STATE"
if RETIRE_TS=20260712T120001Z run_retirement --apply --authorization-reference Bureau:TEST-T001 --expected-head "$TEMP_HEAD" >/tmp/systemkatalog-retire.out 2>&1; then
  echo "FAIL: injected daemon-reload failure unexpectedly succeeded"; exit 1
fi
grep -q "wiederhergestellt" /tmp/systemkatalog-retire.out || { cat /tmp/systemkatalog-retire.out; exit 1; }
[[ -f "$TEMP_HOME/.config/systemd/user/systemkatalog.service" ]]
[[ -f "$TEMP_HOME/.local/bin/systemkatalog" ]]
[[ -f "$TEMP_HOME/.local/bin/systemkatalogctl" ]]
grep -q '^active=active$' "$SYSTEMCTL_STATE"
grep -q '^enabled=enabled$' "$SYSTEMCTL_STATE"
python3 - "$TEMP_HOME/.local/state/systemkatalog/runtime-retirements/20260712T120001Z/retirement-receipt.json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["status"] == "rolled_back"
assert payload["resultCode"] != 0
PY
: > "$SYSTEMCTL_LOG"

printf '%s\n' "=== Authorized apply backs up and removes exact runtime ==="
RETIRE_TS=20260712T120002Z run_retirement --apply --authorization-reference Bureau:TEST-T001 --expected-head "$TEMP_HEAD"
BACKUP="$TEMP_HOME/.local/state/systemkatalog/runtime-retirements/20260712T120002Z"
[[ ! -e "$TEMP_HOME/.config/systemd/user/systemkatalog.service" ]]
[[ ! -e "$TEMP_HOME/.local/bin/systemkatalog" ]]
[[ ! -e "$TEMP_HOME/.local/bin/systemkatalogctl" ]]
[[ -f "$TEMP_HOME/.local/bin/unrelated-tool" ]]
for name in systemkatalog.service systemkatalog systemkatalogctl manifest.sha256 retirement-receipt.json RESTORE.md; do
  [[ -f "$BACKUP/$name" ]] || { echo "FAIL: backup missing $name"; exit 1; }
done
(cd "$BACKUP" && sha256sum -c manifest.sha256)
python3 - "$BACKUP/retirement-receipt.json" "$TEMP_HEAD" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["kind"] == "systemkatalog_runtime_retirement_receipt"
assert payload["authorizationReference"] == "Bureau:TEST-T001"
assert payload["repositoryHead"] == sys.argv[2]
assert payload["status"] == "retired"
assert payload["resultCode"] == 0
assert len(payload["retiredPaths"]) == 3
PY
grep -q '^--user stop systemkatalog\.service$' "$SYSTEMCTL_LOG"
grep -q '^--user disable systemkatalog\.service$' "$SYSTEMCTL_LOG"
grep -q '^--user daemon-reload$' "$SYSTEMCTL_LOG"

printf '%s\n' "=== Second apply is idempotent ==="
run_retirement --apply --authorization-reference Bureau:TEST-T001 --expected-head "$TEMP_HEAD" | grep -q 'ALREADY-RETIRED'
[[ -f "$TEMP_HOME/.local/bin/unrelated-tool" ]]

REAL_HEAD_AFTER="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_AFTER="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"
[[ "$REAL_HEAD_BEFORE" == "$REAL_HEAD_AFTER" ]] || { echo "FAIL: Real repository HEAD changed."; exit 1; }
[[ -z "$REAL_STATUS_AFTER" ]] || { echo "FAIL: Real repository became dirty."; exit 1; }

echo "TARGET-PROOF: RETIREMENT REQUIRES AUTHORIZATION AND HEAD BINDING"
echo "TARGET-PROOF: RETIREMENT FAILS CLOSED ON INSTALLED DRIFT"
echo "TARGET-PROOF: MID-FLIGHT FAILURE RESTORES THE PRIOR RUNTIME"
echo "TARGET-PROOF: RETIREMENT BACKUP IS HASH-VERIFIED"
echo "TARGET-PROOF: RETIREMENT REMOVES ONLY EXACT RUNTIME PATHS"
echo "TARGET-PROOF: RETIREMENT IS IDEMPOTENT"
echo "TARGET-PROOF: SOURCE REPOSITORY WAS NOT MODIFIED"
echo "TARGET-PROOF: SYSTEMKATALOG RETIREMENT SHADOW TEST PASS"
