#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CHECKER="$REPO_ROOT/scripts/ci/check-gitleaks-result.py"
WRAPPER="$REPO_ROOT/scripts/ci/run-gitleaks.sh"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

pass_count=0
fail_count=0

expect_gitleaks_pass() {
    local desc="$1"
    local report="$2"
    local label="$3"
    local rc="$4"
    echo "=== $desc ==="
    if python3 "$CHECKER" --label "$label" --return-code "$rc" --report "$report"; then
        echo "PASS"
        pass_count=$((pass_count + 1))
    else
        echo "FAIL: expected PASS"
        fail_count=$((fail_count + 1))
    fi
}

expect_gitleaks_fail() {
    local desc="$1"
    local report="$2"
    local label="$3"
    local rc="$4"
    local expected_msg="$5"
    echo "=== $desc ==="
    local out
    if out=$(python3 "$CHECKER" --label "$label" --return-code "$rc" --report "$report" 2>&1); then
        echo "FAIL: expected failure but got success"
        echo "Output: $out"
        fail_count=$((fail_count + 1))
    elif echo "$out" | grep -qF "$expected_msg"; then
        echo "PASS (correctly failed with: $expected_msg)"
        pass_count=$((pass_count + 1))
    else
        echo "FAIL: expected error message not found"
        echo "Expected: $expected_msg"
        echo "Got: $out"
        fail_count=$((fail_count + 1))
    fi
}

# --- check-gitleaks-result.py unit tests (no Docker required) ---

echo "[]" > "$TEMP_DIR/ok.json"
expect_gitleaks_pass "T01: empty array + rc=0 → PASS" "$TEMP_DIR/ok.json" "checker-fixture" 0

echo "[]" > "$TEMP_DIR/rc_err.json"
expect_gitleaks_fail "T02: empty array + rc=2 → FAIL (scanner error)" \
    "$TEMP_DIR/rc_err.json" "history" 2 "gitleaks history scanner return code: 2"

echo "not json at all" > "$TEMP_DIR/bad_json.json"
expect_gitleaks_fail "T03: invalid JSON → FAIL" \
    "$TEMP_DIR/bad_json.json" "history" 0 "gitleaks history report is invalid JSON"

echo "{}" > "$TEMP_DIR/obj.json"
expect_gitleaks_fail "T04: object top-level → FAIL" \
    "$TEMP_DIR/obj.json" "history" 0 "gefunden=dict, erwartet=array"

echo '[{"Description":"safe test finding"}]' > "$TEMP_DIR/finding.json"
expect_gitleaks_fail "T05: one finding + rc=0 → FAIL" \
    "$TEMP_DIR/finding.json" "history" 0 "findings: gefunden=1, erwartet=0"

expect_gitleaks_fail "T06: missing report → FAIL" \
    "$TEMP_DIR/nonexistent.json" "history" 0 "gitleaks history report missing"

if [[ "$fail_count" -gt 0 ]]; then
    echo "FAIL: $fail_count gitleaks contract test(s) failed — skipping Target-Proof."
    exit 1
fi

echo "TARGET-PROOF: GITLEAKS RESULT CONTRACT TESTS PASS"

# --- wrapper integration tests (require Docker) ---

if ! command -v docker &>/dev/null; then
    echo "FAIL: gitleaks integration tests require Docker — a mandatory security proof was not executed."
    exit 1
fi

SAFE_REPO="$TEMP_DIR/safe-repo"
SAFE_WORKTREE="$TEMP_DIR/safe-worktree"
SAFE_OUT="$TEMP_DIR/safe-out"
mkdir -p "$SAFE_REPO" "$SAFE_OUT"
git -C "$SAFE_REPO" init -q
git -C "$SAFE_REPO" config user.name "Systemkatalog CI"
git -C "$SAFE_REPO" config user.email "systemkatalog-ci@example.invalid"
echo "safe content" > "$SAFE_REPO/content.txt"
git -C "$SAFE_REPO" add content.txt
git -C "$SAFE_REPO" commit -q -m "safe fixture"
git -C "$SAFE_REPO" worktree add -q -b linked-scan "$SAFE_WORKTREE"

echo "=== T07: linked worktree history scan → PASS with commits ==="
if linked_out=$("$WRAPPER" \
    --mode git \
    --source "$SAFE_WORKTREE" \
    --report "$SAFE_OUT/linked-history.json" \
    --label linked-history 2>&1); then
    grep -qF "TARGET-PROOF: GITLEAKS LINKED HISTORY SCAN PASS" <<<"$linked_out" || {
        echo "FAIL: linked-worktree scan omitted target proof"
        echo "$linked_out"
        exit 1
    }
    grep -Eq '(^|[^0-9])[1-9][0-9]* commits scanned\.' <<<"$linked_out" || {
        echo "FAIL: linked-worktree scan omitted positive commit proof"
        echo "$linked_out"
        exit 1
    }
    echo PASS
else
    echo "FAIL: linked-worktree history scan failed"
    echo "$linked_out"
    exit 1
fi

EMPTY_REPO="$TEMP_DIR/empty-repo"
EMPTY_OUT="$TEMP_DIR/empty-out"
mkdir -p "$EMPTY_REPO" "$EMPTY_OUT"
git -C "$EMPTY_REPO" init -q
echo '[]' > "$EMPTY_OUT/stale.json"
echo "=== T08: empty repository + stale report → FAIL closed ==="
if empty_out=$("$WRAPPER" \
    --mode git \
    --source "$EMPTY_REPO" \
    --report "$EMPTY_OUT/stale.json" \
    --label empty-history 2>&1); then
    echo "FAIL: empty repository scan unexpectedly passed"
    echo "$empty_out"
    exit 1
elif ! grep -qF "gitleaks empty-history source has no commits" <<<"$empty_out"; then
    echo "FAIL: empty repository scan used the wrong failure reason"
    echo "$empty_out"
    exit 1
elif [[ -e "$EMPTY_OUT/stale.json" ]]; then
    echo "FAIL: stale report survived the failed scan"
    exit 1
else
    echo PASS
fi

MISSING_OUT="$TEMP_DIR/missing-out"
mkdir -p "$MISSING_OUT"
echo '[]' > "$MISSING_OUT/stale.json"
echo "=== T09: missing source + stale report → FAIL closed ==="
if missing_out=$("$WRAPPER" \
    --mode git \
    --source "$TEMP_DIR/does-not-exist" \
    --report "$MISSING_OUT/stale.json" \
    --label missing-history 2>&1); then
    echo "FAIL: missing source scan unexpectedly passed"
    echo "$missing_out"
    exit 1
elif ! grep -qF "gitleaks missing-history source directory missing" <<<"$missing_out"; then
    echo "FAIL: missing source scan used the wrong failure reason"
    echo "$missing_out"
    exit 1
elif [[ -e "$MISSING_OUT/stale.json" ]]; then
    echo "FAIL: stale report survived the missing-source scan"
    exit 1
else
    echo PASS
fi

# --- gitleaks:allow bypass test (requires Docker) ---

FAKE_REPO="$TEMP_DIR/fake-repo"
FAKE_CONFIG="$TEMP_DIR/gitleaks-test.toml"
FAKE_OUT="$TEMP_DIR/gitleaks-out"
BYPASS_LOG="$FAKE_OUT/allow-bypass.log"
mkdir -p "$FAKE_REPO" "$FAKE_OUT"

git -C "$FAKE_REPO" init -q
git -C "$FAKE_REPO" config user.name "Systemkatalog CI Test"
git -C "$FAKE_REPO" config user.email "systemkatalog-ci-test@example.invalid"

# A unique artificial marker that no real tool or provider would use.
FAKE_MARKER="SYSTEMKATALOG_FAKE_LEAK_FOR_TEST_0123456789"

# File with marker AND a gitleaks:allow comment
cat > "$FAKE_REPO/test-secret.txt" <<EOF
# gitleaks:allow
SYSTEMKATALOG_TEST_VALUE=${FAKE_MARKER}
EOF
git -C "$FAKE_REPO" add test-secret.txt
git -C "$FAKE_REPO" commit -q -m "add test secret with allow comment"

# Minimal custom config that recognizes only the artificial marker
cat > "$FAKE_CONFIG" <<EOF
title = "Systemkatalog CI allow-bypass test"

[[rules]]
id = "systemkatalog-fake-test-rule"
description = "Detects artificial CI test marker"
regex = '''SYSTEMKATALOG_FAKE_LEAK_FOR_TEST_[0-9A-Z]+'''
EOF

GITLEAKS_IMAGE="ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"

set +e
docker run --rm \
    -v "${FAKE_REPO}:/testrepo:ro" \
    -v "${TEMP_DIR}:/cfg:ro" \
    -v "${FAKE_OUT}:/out:rw" \
    --network none \
    --user "$(id -u):$(id -g)" \
    "$GITLEAKS_IMAGE" \
    dir /testrepo \
    --config /cfg/gitleaks-test.toml \
    --ignore-gitleaks-allow \
    --report-format=json \
    --report-path /out/allow-bypass.json \
    -v >"$BYPASS_LOG" 2>&1
bypass_rc=$?
set -e

BYPASS_REPORT="$FAKE_OUT/allow-bypass.json"

# Verify: bypass_rc == 1 (gitleaks finds leaks, exits 1)
if [[ "$bypass_rc" -ne 1 ]]; then
    echo "FAIL: gitleaks:allow bypass test expected rc=1 (findings), got rc=$bypass_rc"
    cat "$BYPASS_LOG"
    exit 1
fi

# Verify: report is valid JSON list with exactly 1 finding
if [[ ! -f "$BYPASS_REPORT" ]]; then
    echo "FAIL: gitleaks:allow bypass test did not produce a report"
    exit 1
fi

finding_count=$(python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
print(len(d))
" "$BYPASS_REPORT" 2>/dev/null || echo "-1")

if [[ "$finding_count" -ne 1 ]]; then
    echo "FAIL: gitleaks:allow bypass test expected exactly 1 finding, got $finding_count"
    exit 1
fi

# Verify: the finding matches the artificial test marker (not some other leak)
python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
assert len(d) == 1
f = d[0]
assert 'SYSTEMKATALOG_FAKE_LEAK_FOR_TEST_0123456789' in f.get('Match', ''), f'Marker not found in finding: {f}'
" "$BYPASS_REPORT" 2>/dev/null || {
    echo "FAIL: gitleaks:allow bypass test finding does not match the artificial test marker"
    exit 1
}

# Now confirm the production checker correctly rejects this result.
if checker_out=$(python3 "$CHECKER" \
    --label "allow-bypass" \
    --return-code "$bypass_rc" \
    --report "$BYPASS_REPORT" 2>&1); then
    echo "FAIL: checker did not reject the bypass finding"
    exit 1
elif ! grep -qF "gitleaks allow-bypass findings: gefunden=1, erwartet=0" <<<"$checker_out"; then
    echo "FAIL: checker rejected the bypass finding for the wrong reason"
    echo "$checker_out"
    exit 1
else
    echo "PASS: checker rejected the allow-bypass finding"
fi

echo "TARGET-PROOF: GITLEAKS ALLOW BYPASS TEST PASS"

if [[ "$fail_count" -gt 0 ]]; then
    echo "FAIL: $fail_count gitleaks contract test(s) failed."
    exit 1
fi
