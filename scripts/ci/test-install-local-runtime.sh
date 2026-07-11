#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
REAL_HEAD_BEFORE="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_BEFORE="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"
[[ -z "$REAL_STATUS_BEFORE" ]] || { echo "FAIL: Real repository is not clean before test."; exit 1; }

TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_ROOT" /tmp/systemkatalog-check.out' EXIT
TEMP_REPO="$TEMP_ROOT/repo"
TEMP_HOME="$TEMP_ROOT/home"
STUB_BIN="$TEMP_ROOT/stub-bin"
SYSTEMCTL_LOG="$TEMP_ROOT/systemctl.log"
mkdir -p "$TEMP_REPO" "$TEMP_HOME" "$STUB_BIN"
touch "$SYSTEMCTL_LOG"
git -C "$REAL_REPO" archive --format=tar HEAD | tar -xf - -C "$TEMP_REPO"
git -C "$TEMP_REPO" init -q

cat > "$STUB_BIN/systemctl" <<EOF
#!/usr/bin/env bash
echo "\$@" >> "$SYSTEMCTL_LOG"
[[ "\$*" == "--user daemon-reload" ]] && exit 0
echo "unexpected systemctl call: \$*" >&2
exit 1
EOF
chmod +x "$STUB_BIN/systemctl"

run_installer() {
  env -i HOME="$TEMP_HOME" USER=catalog-ci LOGNAME=catalog-ci \
    PATH="$STUB_BIN:/usr/local/bin:/usr/bin:/bin" \
    bash "$TEMP_REPO/ops/install/install-local-runtime.sh"
}
run_checker() {
  python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" --repo-root "$TEMP_REPO" \
    --systemctl-log "$SYSTEMCTL_LOG" --expected-systemctl-calls "$1"
}
capture() {
  python3 - "$TEMP_HOME" "$1" <<'PY'
import hashlib, json, sys
from pathlib import Path
home, output = map(Path, sys.argv[1:])
state = {}
for root in (home / ".local/bin", home / ".config/systemd/user"):
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if path.is_file():
            state[str(path.relative_to(home))] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mode": oct(path.stat().st_mode & 0o777),
            }
output.write_text(json.dumps(state, sort_keys=True, indent=2), encoding="utf-8")
PY
}

echo "=== First Install ==="
run_installer
run_checker 1
capture "$TEMP_ROOT/state1.json"

echo "=== Second Install ==="
run_installer
run_checker 2
capture "$TEMP_ROOT/state2.json"
diff -u "$TEMP_ROOT/state1.json" "$TEMP_ROOT/state2.json"

echo "=== Negative Checker: binary drift ==="
printf 'drift\n' >> "$TEMP_HOME/.local/bin/systemkatalog"
if run_checker 2 >/tmp/systemkatalog-check.out 2>&1; then
  echo "FAIL: checker accepted binary drift"; exit 1
fi
grep -q "content mismatch" /tmp/systemkatalog-check.out
cp "$TEMP_REPO/ops/bin/systemkatalog" "$TEMP_HOME/.local/bin/systemkatalog"
chmod 0755 "$TEMP_HOME/.local/bin/systemkatalog"

echo "=== Negative Checker: retired old-name service ==="
ln -s wrong.service "$TEMP_HOME/.config/systemd/user/heimgewebe-systemkatalog.service"
if run_checker 2 >/tmp/systemkatalog-check.out 2>&1; then
  echo "FAIL: checker accepted retired old-name service"; exit 1
fi
grep -q "retired path exists" /tmp/systemkatalog-check.out
rm "$TEMP_HOME/.config/systemd/user/heimgewebe-systemkatalog.service"

echo "=== Negative Checker: retired Cabinet binary ==="
touch "$TEMP_HOME/.local/bin/cabinet"
if run_checker 2 >/tmp/systemkatalog-check.out 2>&1; then
  echo "FAIL: checker accepted retired Cabinet binary"; exit 1
fi
grep -q "retired path exists" /tmp/systemkatalog-check.out
rm "$TEMP_HOME/.local/bin/cabinet"

REAL_HEAD_AFTER="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_AFTER="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"
[[ "$REAL_HEAD_BEFORE" == "$REAL_HEAD_AFTER" ]] || { echo "FAIL: Real repository HEAD changed."; exit 1; }
[[ -z "$REAL_STATUS_AFTER" ]] || { echo "FAIL: Real repository became dirty."; exit 1; }

echo "TARGET-PROOF: SECOND INSTALL IS IDEMPOTENT"
echo "TARGET-PROOF: SYSTEMKATALOG INSTALL CONTRACT NEGATIVE TESTS PASS"
echo "TARGET-PROOF: SOURCE REPOSITORY WAS NOT MODIFIED"
echo "TARGET-PROOF: SYSTEMKATALOG INSTALLER SHADOW TEST PASS"
