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
# Der Installer prüft [[ -d "$REPO_ROOT/.git" ]]; wir geben ihm ein frisches Init
git -C "$TEMP_REPO" init -q
git -C "$TEMP_REPO" config user.name "Cabinet CI Test"
git -C "$TEMP_REPO" config user.email "cabinet-ci-test@example.invalid"

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

echo "=== Negative Checker Tests ==="

# T-N1: Kein systemctl-Aufruf — empty log, but home intact
neg_log="$TEMP_ROOT/neg-systemctl-empty.log"
touch "$neg_log"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" \
    --repo-root "$TEMP_REPO" \
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
echo "PASS [T-N1: kein systemctl-Aufruf]"

# T-N2: Falscher Binary-Inhalt — mutate in place, restore after
ORIG_CABINET="$(cat "$TEMP_HOME/.local/bin/cabinet")"
echo "CABINET_CI_DUMMY_CONTENT" > "$TEMP_HOME/.local/bin/cabinet"
chmod 0755 "$TEMP_HOME/.local/bin/cabinet"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" \
    --repo-root "$TEMP_REPO" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    printf '%s' "$ORIG_CABINET" > "$TEMP_HOME/.local/bin/cabinet"
    chmod 0755 "$TEMP_HOME/.local/bin/cabinet"
    echo "FAIL [T-N2]: expected failure but checker passed"
    exit 1
fi
cp "$TEMP_REPO/ops/bin/cabinet" "$TEMP_HOME/.local/bin/cabinet"
chmod 0755 "$TEMP_HOME/.local/bin/cabinet"
if ! echo "$out" | grep -qF "content mismatch"; then
    echo "FAIL [T-N2]: expected content mismatch marker, got: $out"
    exit 1
fi
echo "PASS [T-N2: falscher Binary-Inhalt]"

# T-N3: Falsche Unit-Zeile — append to service, restore after
echo "CABINET_CI_DUMMY_UNIT=1" >> "$TEMP_HOME/.config/systemd/user/cabinet.service"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" \
    --repo-root "$TEMP_REPO" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N3]: expected failure but checker passed"
    exit 1
fi
# Restore service file by reinstalling
python3 - <<PYEOF
from pathlib import Path
import sys
src = Path("$TEMP_REPO/ops/systemd/cabinet.service.tmpl")
dst = Path("$TEMP_HOME/.config/systemd/user/cabinet.service")
content = src.read_text().replace("@HOME@","$TEMP_HOME").replace("@CABINET_ROOT@","$TEMP_REPO")
dst.write_text(content)
PYEOF
if ! echo "$out" | grep -qF "content mismatch"; then
    echo "FAIL [T-N3]: expected content mismatch marker, got: $out"
    exit 1
fi
echo "PASS [T-N3: falsche Unit-Zeile]"

# T-N4: Falsches Symlink-Ziel — replace symlink, restore after
rm -f "$TEMP_HOME/.local/bin/cabinet-safe-export"
ln -s "/tmp/cabinet-ci-dummy-target" "$TEMP_HOME/.local/bin/cabinet-safe-export"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" \
    --repo-root "$TEMP_REPO" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$RUNTIME_HASH" 2>&1); then
    echo "FAIL [T-N4]: expected failure but checker passed"
    exit 1
fi
rm -f "$TEMP_HOME/.local/bin/cabinet-safe-export"
ln -s "$TEMP_REPO/scripts/cabinet-safe-export.sh" "$TEMP_HOME/.local/bin/cabinet-safe-export"
if ! echo "$out" | grep -qF "symlink raw target mismatch"; then
    echo "FAIL [T-N4]: expected symlink mismatch marker, got: $out"
    exit 1
fi
echo "PASS [T-N4: falsches Symlink-Ziel]"

# T-N5: Veränderte runtime.env — mutate in place, restore after
ORIG_HASH="$RUNTIME_HASH"
echo "CABINET_TEST_PLACEHOLDER=2" > "$TEMP_HOME/.config/cabinet/runtime.env"
chmod 0600 "$TEMP_HOME/.config/cabinet/runtime.env"
out=""
if out=$(python3 "$REAL_REPO/scripts/ci/check-installed-runtime.py" \
    --home "$TEMP_HOME" \
    --repo-root "$TEMP_REPO" \
    --systemctl-log "$SYSTEMCTL_LOG" \
    --expected-systemctl-calls 2 \
    --runtime-env-sha256 "$ORIG_HASH" 2>&1); then
    echo "FAIL [T-N5]: expected failure but checker passed"
    exit 1
fi
echo "CABINET_TEST_PLACEHOLDER=1" > "$TEMP_HOME/.config/cabinet/runtime.env"
chmod 0600 "$TEMP_HOME/.config/cabinet/runtime.env"
if ! echo "$out" | grep -qF "hash mismatch"; then
    echo "FAIL [T-N5]: expected hash mismatch marker, got: $out"
    exit 1
fi
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
