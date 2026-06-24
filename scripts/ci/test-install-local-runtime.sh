#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

TEMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TEMP_HOME"' EXIT

export STUB_BIN="$TEMP_HOME/stub-bin"
mkdir -p "$STUB_BIN"

export SYSTEMCTL_LOG="$TEMP_HOME/systemctl.log"
touch "$SYSTEMCTL_LOG"

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
      SYSTEMCTL_LOG="$SYSTEMCTL_LOG" \
      "$REPO_ROOT/ops/install/install-local-runtime.sh"
}

capture_state() {
    local outfile="$1"
    python3 - <<EOF
import os
import json
import hashlib
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
EOF
}

echo "=== First Install Run ==="
run_installer

echo "=== Korrektheit nach Lauf 1 ==="
calls=$(wc -l < "$SYSTEMCTL_LOG")
if [[ "$calls" -ne 1 ]]; then
    echo "FAIL: systemctl called $calls times, expected 1."
    exit 1
fi

python3 - <<EOF
import sys
import os
import hashlib
from pathlib import Path

home = Path("$TEMP_HOME")
repo = Path("$REPO_ROOT")

def check_file(dest: Path, expected_mode: str, src: Path = None, expected_content: str = None):
    if not dest.is_file():
        sys.exit(f"FAIL: Missing file: {dest}")

    mode = oct(dest.stat().st_mode & 0o7777)[2:]
    # For scripts, we can have 0755 but oct() returns 755
    if int(mode, 8) != int(expected_mode, 8):
        sys.exit(f"FAIL: Wrong mode for {dest}: expected {expected_mode}, got {mode}")

    with open(dest, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()

    if src:
        with open(src, "rb") as f:
            expected_hash = hashlib.sha256(f.read()).hexdigest()
    else:
        expected_hash = hashlib.sha256(expected_content.encode("utf-8")).hexdigest()

    if actual_hash != expected_hash:
        sys.exit(f"FAIL: Content mismatch for {dest}")

# Binaries
check_file(home / ".local/bin/cabinet", "0755", src=repo / "ops/bin/cabinet")
check_file(home / ".local/bin/cabinet-session", "0755", src=repo / "ops/bin/cabinet-session")
check_file(home / ".local/bin/cabinetctl", "0755", src=repo / "ops/bin/cabinetctl")
check_file(home / ".local/bin/cabinet-security-gate", "0755", src=repo / "ops/bin/cabinet-security-gate")

# Systemd files
def render(src: Path):
    text = src.read_text("utf-8")
    text = text.replace("@CABINET_ROOT@", str(repo))
    text = text.replace("@HOME@", str(home))
    return text

check_file(home / ".config/systemd/user/cabinet.service", "0644", expected_content=render(repo / "ops/systemd/cabinet.service.tmpl"))
check_file(home / ".config/systemd/user/cabinet.service.d/10-loopback-gate.conf", "0644", expected_content=render(repo / "ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl"))

# Symlink
link = home / ".local/bin/cabinet-safe-export"
if not link.is_symlink():
    sys.exit("FAIL: cabinet-safe-export is not a symlink")
target = os.readlink(link)
if target != str(repo / "scripts/cabinet-safe-export.sh"):
    sys.exit(f"FAIL: Symlink points to wrong target: {target}")

# Runtime env
env_file = home / ".config/cabinet/runtime.env"
if oct(env_file.stat().st_mode & 0o7777)[2:] != "600":
    sys.exit("FAIL: runtime.env mode is not 600")
with open(env_file, "rb") as f:
    if hashlib.sha256(f.read()).hexdigest() != "$RUNTIME_HASH":
        sys.exit("FAIL: runtime.env content changed")

EOF

echo "=== Dark-Patch Check ==="
HOME="$TEMP_HOME" "$REPO_ROOT/ops/patches/cabinet-v0.4.4-dark-default.py" --app-root "$APP_ROOT" --check >/dev/null

capture_state "$TEMP_HOME/state1.json"

echo "=== Second Install Run (Idempotence) ==="
run_installer | tee "$TEMP_HOME/install2.log"

calls=$(wc -l < "$SYSTEMCTL_LOG")
if [[ "$calls" -ne 2 ]]; then
    echo "FAIL: systemctl called $calls times total, expected 2."
    exit 1
fi

patches_found=$(grep -c "PASS  bereits gepatcht:" "$TEMP_HOME/install2.log" || true)
if [[ "$patches_found" -ne 3 ]]; then
    echo "FAIL: Expected 3 'bereits gepatcht' messages, found $patches_found."
    exit 1
fi

capture_state "$TEMP_HOME/state2.json"

if ! diff -u "$TEMP_HOME/state1.json" "$TEMP_HOME/state2.json"; then
    echo "FAIL: Target state changed between run 1 and run 2."
    exit 1
fi

if [[ "$(stat -c "%a" "$TEMP_HOME/.config/cabinet/runtime.env")" != "600" ]]; then
    echo "FAIL: runtime.env mode changed."
    exit 1
fi
if [[ "$(sha256sum "$TEMP_HOME/.config/cabinet/runtime.env" | awk '{print $1}')" != "$RUNTIME_HASH" ]]; then
    echo "FAIL: runtime.env content changed."
    exit 1
fi

echo "TARGET-PROOF: CABINET INSTALLER SHADOW TEST PASS"
echo "TARGET-PROOF: FIRST INSTALL MATCHES REPOSITORY CONTRACT"
echo "TARGET-PROOF: SECOND INSTALL IS IDEMPOTENT"
echo "TARGET-PROOF: SYSTEMCTL CALL CONTRACT VERIFIED"
