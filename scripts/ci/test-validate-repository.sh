#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

TEMP_REPO="$(mktemp -d)"
trap 'rm -rf "$TEMP_REPO"' EXIT

echo "Cloning repository to temp directory..."
git clone --no-hardlinks --quiet "$REAL_REPO" "$TEMP_REPO"
cd "$TEMP_REPO"
git config user.name "Cabinet CI Test"
git config user.email "cabinet-ci-test@example.invalid"

BASE_COMMIT="$(git rev-parse HEAD)"

reset_state() {
    git reset --hard "$BASE_COMMIT" >/dev/null
    git clean -ffdx >/dev/null
}

expect_success() {
    local desc="$1"
    echo "=== $desc ==="
    if ! ./scripts/ci/validate-repository.sh >/dev/null; then
        echo "FAIL: Expected success but failed."
        exit 1
    fi
    echo "PASS"
}

expect_failure() {
    local desc="$1"
    local expected_msg="$2"
    echo "=== $desc ==="

    local out
    # Capture output. validate-repository.sh should fail.
    if out=$(./scripts/ci/validate-repository.sh 2>&1); then
        echo "FAIL: Expected failure but succeeded."
        exit 1
    fi

    if ! echo "$out" | grep -qF "$expected_msg"; then
        echo "FAIL: Expected error message not found."
        echo "Expected: $expected_msg"
        echo "Actual output:"
        echo "$out"
        exit 1
    fi
    echo "PASS"
}

# Positive Cases
reset_state
expect_success "Test 1: Unveränderter aktueller Commit besteht"

reset_state
echo "=== Test 2: Repository-Modus besteht im HEAD-Snapshot ohne lokale Workspace- und Editor-Dateien ==="
# Dies ist bereits der Normalzustand im Clone
if ! python3 scripts/check-cabinet-layout.py --mode repository . >/dev/null; then
    echo "FAIL: Repository-Modus scheiterte im Fresh Clone"
    exit 1
fi
echo "PASS"

reset_state
echo "=== Test 3: Ignorierte unversionierte Datei beeinflusst Repository-Validierung nicht ==="
mkdir -p vorzimmer/.agents/.runtime
echo "ignored" > vorzimmer/.agents/.runtime/ignored-state
if ! ./scripts/ci/validate-repository.sh >/dev/null; then
    echo "FAIL: Untracked file influenced validation."
    exit 1
fi
echo "PASS"

echo "=== Test 4: Echter lokaler Modus besteht auf /home/alex/repos/cabinet ==="
if [[ -f "$REAL_REPO/.agents/.config/workspace.json" ]]; then
    if ! python3 "$REAL_REPO/scripts/check-cabinet-layout.py" --mode local "$REAL_REPO" >/dev/null; then
        echo "FAIL: local mode failed on real repo."
        exit 1
    fi
    echo "PASS"
else
    echo "SKIP (not in local dev environment)"
fi

# Verbotene Pfade
reset_state
mkdir -p .agents/.runtime
echo "token" > .agents/.runtime/daemon-token
git add -f .agents/.runtime/daemon-token
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 5: .agents/.runtime/daemon-token" "agent runtime/config: .agents/.runtime/daemon-token"

reset_state
mkdir -p .agents
echo "{}" > .agents/.config.json
git add -f .agents/.config.json
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 6: .agents/.config.json" "local agent config: .agents/.config.json"

reset_state
mkdir -p vorzimmer/.agents/.config
echo "{}" > vorzimmer/.agents/.config/provider.json
git add -f vorzimmer/.agents/.config/provider.json
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 7: vorzimmer/.agents/.config/provider.json" "agent runtime/config: vorzimmer/.agents/.config/provider.json"

reset_state
mkdir -p secrets
echo "SECRET=1" > secrets/runtime.env
git add -f secrets/runtime.env
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 8: secrets/runtime.env" "env file: secrets/runtime.env"

reset_state
echo "PROD=1" > .env.production
git add -f .env.production
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 9: .env.production" "env file: .env.production"

reset_state
echo "DB" > .cabinet.db-wal
git add -f .cabinet.db-wal
git commit -m "add forbidden path" >/dev/null
expect_failure "Test 10: .cabinet.db-wal" "database file: .cabinet.db-wal"

# Manifest
reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["schema"]="wrong"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "break schema" >/dev/null
expect_failure "Test 11: falsches schema" "erwartet=cabinet.local-runtime.v1"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["cabinet_version"]="wrong"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "break version" >/dev/null
expect_failure "Test 12: falsche cabinet_version" "erwartet=0.4.4"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"].pop(); json.dump(m, open("ops/manifest.json","w"))'
git commit -am "remove executable" >/dev/null
expect_failure "Test 13: fehlendes Executable" "FAIL: manifest.executables.sources: fehlend="

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"].append({"source": "ops/bin/cabinet", "destination": "~/.local/bin/cabinet-extra", "mode": "0755"}); json.dump(m, open("ops/manifest.json","w"))'
git commit -am "add executable" >/dev/null
expect_failure "Test 14: zusätzliches Executable" "FAIL: manifest.executables: duplicate source: ops/bin/cabinet"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][0]["destination"]="wrong"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "wrong destination" >/dev/null
expect_failure "Test 15: falsche destination" "FAIL: manifest.executables[ops/bin/cabinet].destination:"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][0]["destination"]="/tmp/abs"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "absolute destination" >/dev/null
expect_failure "Test 16: absolute destination" "FAIL: manifest.executables[ops/bin/cabinet].destination:"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][0]["mode"]="0644"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "wrong manifest mode" >/dev/null
expect_failure "Test 17: falscher Manifestmodus 0644 für Executable" "FAIL: manifest.executables[ops/bin/cabinet].mode: gefunden=0644, erwartet=0755"

reset_state
git update-index --chmod=-x ops/bin/cabinet
git commit -m "wrong git mode" >/dev/null
git reset --hard HEAD >/dev/null
expect_failure "Test 18: falscher Git-Modus 100644 für Executable" "FAIL: manifest.executables[ops/bin/cabinet].git_mode: gefunden=100644, erwartet=100755"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["symlinks"][0]["source"]="missing.sh"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "missing symlink src" >/dev/null
expect_failure "Test 19: fehlende Symlinkquelle" "FAIL: manifest.symlinks.sources: fehlend="

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["local_only"].append("extra"); json.dump(m, open("ops/manifest.json","w"))'
git commit -am "extra local_only" >/dev/null
expect_failure "Test 20: zusätzliches local_only" "FAIL: manifest.local_only:"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["local_only"].pop(); json.dump(m, open("ops/manifest.json","w"))'
git commit -am "missing local_only" >/dev/null
expect_failure "Test 21: fehlendes local_only" "FAIL: manifest.local_only:"

# Layout
reset_state
python3 -c 'import json; m=json.load(open(".home/home.json")); m["defaultRoom"]="wrong"; json.dump(m, open(".home/home.json","w"))'
git commit -am "wrong default room" >/dev/null
expect_failure "Test 22: falsches defaultRoom" "defaultRoom="

reset_state
python3 -c 'import json; m=json.load(open(".home/home.json")); m["lastActiveRoom"]="wrong"; json.dump(m, open(".home/home.json","w"))'
git commit -am "wrong last active room" >/dev/null
expect_failure "Test 23: falsches lastActiveRoom" "lastActiveRoom="

reset_state
git rm -r vorzimmer >/dev/null
git commit -m "remove room" >/dev/null
expect_failure "Test 24: fehlender Room" "Room-Menge weicht ab"

reset_state
mkdir -p vorzimmer/.agents
echo "tracked" > vorzimmer/.agents/unexpected.txt
git add -f vorzimmer/.agents/unexpected.txt
git commit -m "unexpected tracked agent file" >/dev/null
expect_failure "Test 25: unerwartete versionierte Datei in Room-.agents" "unerwartete Agentendatei: unexpected.txt"

reset_state
echo "=== Test 26: lokaler Modus scheitert im Fresh Clone ohne Workspace und Editor ==="
if python3 scripts/check-cabinet-layout.py --mode local . >/dev/null 2>&1; then
    echo "FAIL: local mode unexpectedly succeeded in fresh clone."
    exit 1
fi
echo "PASS"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); e=m["executables"][0]; m["executables"]=[e.copy() for _ in range(4)]; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "duplicate source" >/dev/null
expect_failure "Test 27: Doppelte Quellen Executables" "duplicate source: ops/bin/cabinet"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); t=m["templates"][0]; m["templates"]=[t.copy(), t.copy()]; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "duplicate template source" >/dev/null
expect_failure "Test 28: Doppelte Template-Quellen" "duplicate source: ops/systemd/cabinet.service.tmpl"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][1]["source"] = "ops/bin/cabinet"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "wrong valid source" >/dev/null
expect_failure "Test 29: Erlaubte Quelle ersetzt erwartete Quelle" "duplicate source: ops/bin/cabinet"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][0]["unexpected"]="value"; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "unexpected field" >/dev/null
expect_failure "Test 30: Unerwartetes Feld" "manifest.executables[0].fields: gefunden="

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"][0].pop("mode"); json.dump(m, open("ops/manifest.json","w"))'
git commit -am "missing mode" >/dev/null
expect_failure "Test 31: Fehlendes mode-Feld" "manifest.executables[0].fields: fehlend="

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["executables"]={}; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "executables type" >/dev/null
expect_failure "Test 32: executables als dict" "erwartet list, gefunden dict"

reset_state
python3 -c 'import json; m=json.load(open("ops/manifest.json")); m["local_only"]=[1]; json.dump(m, open("ops/manifest.json","w"))'
git commit -am "local_only type" >/dev/null
expect_failure "Test 33: local_only element type" "erwartet string, gefunden int"

reset_state
git update-index --chmod=-x scripts/cabinet-safe-export.sh
git commit -m "wrong git mode for safe-export" >/dev/null
git reset --hard HEAD >/dev/null
expect_failure "Test 34: Safe-Export nicht ausführbar" "git_mode: gefunden=100644, erwartet=100755"

reset_state
git rm scripts/cabinet-safe-export.sh >/dev/null
ln -s something scripts/cabinet-safe-export.sh
git add scripts/cabinet-safe-export.sh
git commit -m "safe-export symlink" >/dev/null
expect_failure "Test 35: Safe-Export als Git-Symlink" "git_mode: gefunden=120000, erwartet=100755"

reset_state
echo "=== Test 36: Zu früher Target-Proof ==="
# Erzeuge echten Bash-Syntaxfehler in einem Bash-Skript:
# validate-repository.sh prüft alle *.sh-Dateien mit bash -n;
# ein unkorrekt geschlossenes if-Statement schlägt fehl
printf '#!/usr/bin/env bash\nif true\n# missing then/fi\n' > scripts/cabinet-safe-export.sh
git commit -am "bash syntax error" >/dev/null
out=$(./scripts/ci/validate-repository.sh 2>&1 || true)
if ./scripts/ci/validate-repository.sh >/dev/null 2>&1; then
    echo "FAIL: Expected validation to fail."
    exit 1
fi
if echo "$out" | grep -qF "TARGET-PROOF: CABINET REPOSITORY CONTRACT VALID"; then
    echo "FAIL: TARGET-PROOF printed prematurely"
    exit 1
fi
echo "PASS"

echo "TARGET-PROOF: CABINET REPOSITORY VALIDATOR TESTS PASS"
echo "TARGET-PROOF: REPOSITORY MODE IGNORES UNTRACKED LOCAL STATE"
