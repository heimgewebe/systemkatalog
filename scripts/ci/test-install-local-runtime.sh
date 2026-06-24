#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Beweis: echtes Repository ist unverändert ---
REAL_HEAD_BEFORE="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_BEFORE="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"
if [[ -n "$REAL_STATUS_BEFORE" ]]; then
    echo "FAIL: Real repository is not clean before test."
    exit 1
fi

TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEMP_ROOT"' EXIT

TEMP_REPO="$TEMP_ROOT/repo"
TEMP_HOME="$TEMP_ROOT/home"
STUB_BIN="$TEMP_ROOT/stub-bin"
SYSTEMCTL_LOG="$TEMP_ROOT/systemctl.log"

mkdir -p "$TEMP_REPO" "$TEMP_HOME" "$STUB_BIN"
touch "$SYSTEMCTL_LOG"

# Materialisiere aktuellen HEAD-Stand in isoliertes Verzeichnis
git -C "$REAL_REPO" archive --format=tar HEAD | tar -xf - -C "$TEMP_REPO"

# systemctl-Stub
cat > "$STUB_BIN/systemctl" <<EOF
#!/usr/bin/env bash
echo "\$@" >> "$SYSTEMCTL_LOG"
if [[ "\$1" == "--user" && "\$2" == "daemon-reload" && -z "\${3:-}" ]]; then
    exit 0
fi
echo "systemctl stub called with invalid args: \$*" >&2
exit 1
EOF
chmod +x "$STUB_BIN/systemctl"

# App-Fixture für Dark-Patch
APP_ROOT="$TEMP_HOME/.cabinet/app/v0.4.4"
mkdir -p "$APP_ROOT"

cat > "$APP_ROOT/package.json" <<'EOF'
{
  "version": "0.4.4"
}
EOF

mkdir -p "$APP_ROOT/src/lib"
cat > "$APP_ROOT/src/lib/themes.ts" <<'EOF'
export const themes = [
  { name: "black", type: "dark" }
];
EOF

mkdir -p "$APP_ROOT/src/app"
cat > "$APP_ROOT/src/app/layout.tsx" <<'EOF'
defaultTheme="light"
EOF

mkdir -p "$APP_ROOT/src/components/layout"
cat > "$APP_ROOT/src/components/layout/theme-initializer.tsx" <<'EOF'
const themeName = stored || "paper";
EOF

cat > "$APP_ROOT/src/components/layout/room-theme-sync.tsx" <<'EOF'
room?.theme || getStoredThemeName() || "paper";
EOF

# Pre-existierende runtime.env (muss 0600 sein)
mkdir -p "$TEMP_HOME/.config/cabinet"
echo "CABINET_TEST_PLACEHOLDER=1" > "$TEMP_HOME/.config/cabinet/runtime.env"
chmod 0600 "$TEMP_HOME/.config/cabinet/runtime.env"
RUNTIME_HASH="$(sha256sum "$TEMP_HOME/.config/cabinet/runtime.env" | awk '{print $1}')"

run_installer() {
    env -i \
      HOME="$TEMP_HOME" \
      USER="cabinet-ci" \
      LOGNAME="cabinet-ci" \
      PATH="$STUB_BIN:/usr/local/bin:/usr/bin:/bin" \
      XDG_CONFIG_HOME="$TEMP_HOME/.config" \
      XDG_STATE_HOME="$TEMP_HOME/.local/state" \
      bash "$TEMP_REPO/ops/install/install-local-runtime.sh"
}

run_checker() {
    python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
        --home "$TEMP_HOME" \
        --repo-root "$TEMP_REPO" \
        --app-root "$APP_ROOT" \
        --systemctl-log "$SYSTEMCTL_LOG" \
        --expected-systemctl-calls "$1" \
        --runtime-env-sha256 "$RUNTIME_HASH"
}

capture_state() {
    local outfile="$1"
    python3 - <<PYEOF
import os, json, hashlib
from pathlib import Path

home = Path("$TEMP_HOME")
targets = [home / ".local/bin", home / ".config/systemd/user", home / ".cabinet/app/v0.4.4/src"]

state = {}
for t in targets:
    if not t.exists():
        continue
    for path in t.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        rel = str(path.relative_to(home))
        if "ops-backups" in rel or "theme-backups" in rel:
            continue
        entry = {}
        if path.is_symlink():
            entry["type"] = "symlink"
            entry["target"] = os.readlink(path)
            try:
                entry["resolved"] = str(path.resolve())
            except Exception:
                entry["resolved"] = "broken"
        else:
            entry["type"] = "file"
            with open(path, "rb") as f:
                entry["sha256"] = hashlib.sha256(f.read()).hexdigest()
            entry["mode"] = oct(path.stat().st_mode & 0o7777)[2:]
        state[rel] = entry

with open("$outfile", "w") as f:
    json.dump(state, f, sort_keys=True, indent=2)
PYEOF
}

# --- Lauf 1 ---
echo "=== First Install Run ==="
run_installer

echo "=== Korrektheit nach Lauf 1 ==="
run_checker 1

echo "TARGET-PROOF: FIRST INSTALL MATCHES REPOSITORY CONTRACT"

# Dark-Patch-Check nach Lauf 1
echo "=== Dark-Patch Check ==="
python3 "$TEMP_REPO/ops/patches/cabinet-v0.4.4-dark-default.py" --app-root "$APP_ROOT" --check

capture_state "$TEMP_ROOT/state1.json"

# --- Lauf 2 ---
echo "=== Second Install Run (Idempotence) ==="
run_installer 2>&1 | tee "$TEMP_ROOT/install2.log"

echo "=== Korrektheit nach Lauf 2 ==="
run_checker 2

patches_found=$(grep -c "PASS  bereits gepatcht:" "$TEMP_ROOT/install2.log" || true)
if [[ "$patches_found" -ne 3 ]]; then
    echo "FAIL: Expected 3 'bereits gepatcht' messages, found $patches_found."
    exit 1
fi

capture_state "$TEMP_ROOT/state2.json"

if ! diff -u "$TEMP_ROOT/state1.json" "$TEMP_ROOT/state2.json"; then
    echo "FAIL: Target state changed between run 1 and run 2."
    exit 1
fi

echo "TARGET-PROOF: SECOND INSTALL IS IDEMPOTENT"
echo "TARGET-PROOF: SYSTEMCTL CALL CONTRACT VERIFIED"

# --- Negative Checker-Tests ---
expect_install_contract_failure() {
    local desc="$1"
    local expected_msg="$2"
    # Remaining args are mutation commands to run in the fixture home
    local fixture_home="$TEMP_ROOT/neg-home-$$-${RANDOM}"
    cp -a "$TEMP_HOME" "$fixture_home"
    # Run the mutation function passed as third argument
    (
        FIXTURE_HOME="$fixture_home"
        eval "${3:-}"
    )
    local out
    if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
        --home "$fixture_home" \
        --repo-root "$TEMP_REPO" \
        --app-root "$APP_ROOT" \
        --systemctl-log "$SYSTEMCTL_LOG" \
        --expected-systemctl-calls 2 \
        --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
        echo "FAIL [$desc]: Expected failure but checker passed."
        rm -rf "$fixture_home"
        exit 1
    fi
    if ! echo "$out" | grep -qF "$expected_msg"; then
        echo "FAIL [$desc]: Expected marker not found."
        echo "  Expected: $expected_msg"
        echo "  Got: $out"
        rm -rf "$fixture_home"
        exit 1
    fi
    rm -rf "$fixture_home"
    echo "PASS [$desc]"
}

echo "=== Negative Checker Tests ==="

# T-N1: Kein systemctl-Aufruf
neg_fixture="$TEMP_ROOT/neg-home-n1"
cp -a "$TEMP_HOME" "$neg_fixture"
neg_log="$TEMP_ROOT/neg-systemctl-empty.log"
touch "$neg_log"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$neg_fixture" \
    --repo-root "$TEMP_REPO" \
    --app-root "$APP_ROOT" \
    --systemctl-log "$neg_log" \
    --expected-systemctl-calls 1 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N1]: expected failure but checker passed"
    exit 1
fi
if ! echo "$out" | grep -qF "systemctl call count: gefunden=0, erwartet=1"; then
    echo "FAIL [T-N1]: expected systemctl count marker, got: $out"
    exit 1
fi
rm -rf "$neg_fixture"
echo "PASS [T-N1: kein systemctl-Aufruf]"

# T-N2: Falscher Binary-Inhalt
neg_fixture="$TEMP_ROOT/neg-home-n2"
cp -a "$TEMP_HOME" "$neg_fixture"
echo "CABINET_CI_DUMMY_CONTENT" > "$neg_fixture/.local/bin/cabinet"
chmod 0755 "$neg_fixture/.local/bin/cabinet"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$neg_fixture" \
    --repo-root "$TEMP_REPO" \
    --app-root "$APP_ROOT" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N2]: expected failure but checker passed"
    exit 1
fi
if ! echo "$out" | grep -qF "content mismatch"; then
    echo "FAIL [T-N2]: expected content mismatch marker, got: $out"
    exit 1
fi
rm -rf "$neg_fixture"
echo "PASS [T-N2: falscher Binary-Inhalt]"

# T-N3: Falsche Unit-Zeile
neg_fixture="$TEMP_ROOT/neg-home-n3"
cp -a "$TEMP_HOME" "$neg_fixture"
echo "CABINET_CI_DUMMY_UNIT=1" >> "$neg_fixture/.config/systemd/user/cabinet.service"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$neg_fixture" \
    --repo-root "$TEMP_REPO" \
    --app-root "$APP_ROOT" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N3]: expected failure but checker passed"
    exit 1
fi
if ! echo "$out" | grep -qF "content mismatch"; then
    echo "FAIL [T-N3]: expected content mismatch marker, got: $out"
    exit 1
fi
rm -rf "$neg_fixture"
echo "PASS [T-N3: falsche Unit-Zeile]"

# T-N4: Falsches Symlink-Ziel
neg_fixture="$TEMP_ROOT/neg-home-n4"
cp -a "$TEMP_HOME" "$neg_fixture"
rm -f "$neg_fixture/.local/bin/cabinet-safe-export"
ln -s "/tmp/cabinet-ci-dummy-target" "$neg_fixture/.local/bin/cabinet-safe-export"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$neg_fixture" \
    --repo-root "$TEMP_REPO" \
    --app-root "$APP_ROOT" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N4]: expected failure but checker passed"
    exit 1
fi
if ! echo "$out" | grep -qF "symlink raw target mismatch"; then
    echo "FAIL [T-N4]: expected symlink mismatch marker, got: $out"
    exit 1
fi
rm -rf "$neg_fixture"
echo "PASS [T-N4: falsches Symlink-Ziel]"

# T-N5: Veränderte runtime.env
neg_fixture="$TEMP_ROOT/neg-home-n5"
cp -a "$TEMP_HOME" "$neg_fixture"
echo "CABINET_TEST_PLACEHOLDER=2" > "$neg_fixture/.config/cabinet/runtime.env"
chmod 0600 "$neg_fixture/.config/cabinet/runtime.env"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$neg_fixture" \
    --repo-root "$TEMP_REPO" \
    --app-root "$APP_ROOT" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N5]: expected failure but checker passed"
    exit 1
fi
if ! echo "$out" | grep -qF "hash mismatch"; then
    echo "FAIL [T-N5]: expected hash mismatch marker, got: $out"
    exit 1
fi
rm -rf "$neg_fixture"
echo "PASS [T-N5: veränderte runtime.env]"

echo "TARGET-PROOF: INSTALL CONTRACT NEGATIVE TESTS PASS"

# --- Beweis: echtes Repository unverändert ---
REAL_HEAD_AFTER="$(git -C "$REAL_REPO" rev-parse HEAD)"
REAL_STATUS_AFTER="$(git -C "$REAL_REPO" status --porcelain=v1 --untracked-files=all)"

if [[ "$REAL_HEAD_BEFORE" != "$REAL_HEAD_AFTER" ]]; then
    echo "FAIL: Real repository HEAD changed during test."
    exit 1
fi
if [[ -n "$REAL_STATUS_AFTER" ]]; then
    echo "FAIL: Real repository is dirty after test."
    exit 1
fi

echo "TARGET-PROOF: SOURCE REPOSITORY WAS NOT MODIFIED"
echo "TARGET-PROOF: CABINET INSTALLER SHADOW TEST PASS"
