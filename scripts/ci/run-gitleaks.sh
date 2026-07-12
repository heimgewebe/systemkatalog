#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

GITLEAKS_IMAGE="ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"
CHECKER="$REPO_ROOT/scripts/ci/check-gitleaks-result.py"

MODE=""
SOURCE=""
REPORT=""
LABEL=""
MIRROR_ROOT=""
SCAN_LOG=""

cleanup() {
    [[ -z "$MIRROR_ROOT" ]] || rm -rf -- "$MIRROR_ROOT"
    [[ -z "$SCAN_LOG" ]] || rm -f -- "$SCAN_LOG"
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)    MODE="$2";   shift 2 ;;
        --source)  SOURCE="$2"; shift 2 ;;
        --report)  REPORT="$2"; shift 2 ;;
        --label)   LABEL="$2";  shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$MODE" || -z "$SOURCE" || -z "$REPORT" || -z "$LABEL" ]]; then
    echo "Usage: $0 --mode git|dir --source PATH --report PATH --label LABEL" >&2
    exit 2
fi
if [[ "$MODE" != "git" && "$MODE" != "dir" ]]; then
    echo "FAIL: --mode must be 'git' or 'dir', got: $MODE" >&2
    exit 2
fi
REPORT_DIR="$(dirname -- "$REPORT")"
mkdir -p -- "$REPORT_DIR"
REPORT_DIR="$(cd "$REPORT_DIR" && pwd)"
REPORT="$REPORT_DIR/$(basename -- "$REPORT")"
rm -f -- "$REPORT"

if [[ ! -d "$SOURCE" ]]; then
    echo "FAIL: gitleaks $LABEL source directory missing: $SOURCE" >&2
    exit 1
fi
SOURCE="$(realpath -e -- "$SOURCE")"

SCAN_SOURCE="$SOURCE"
EXPECTED_COMMITS=""
if [[ "$MODE" == "git" ]]; then
    if ! git -C "$SOURCE" rev-parse --git-dir >/dev/null 2>&1; then
        echo "FAIL: gitleaks $LABEL source is not a Git repository: $SOURCE" >&2
        exit 1
    fi
    EXPECTED_COMMITS="$(git -C "$SOURCE" rev-list --all --count)"
    if [[ ! "$EXPECTED_COMMITS" =~ ^[0-9]+$ || "$EXPECTED_COMMITS" -eq 0 ]]; then
        echo "FAIL: gitleaks $LABEL source has no commits: $SOURCE" >&2
        exit 1
    fi

    MIRROR_ROOT="$(mktemp -d)"
    SCAN_SOURCE="$MIRROR_ROOT/repository.git"
    git clone --mirror --no-hardlinks "$SOURCE" "$SCAN_SOURCE" >/dev/null
    MIRROR_COMMITS="$(git --git-dir="$SCAN_SOURCE" rev-list --all --count)"
    if [[ "$MIRROR_COMMITS" != "$EXPECTED_COMMITS" ]]; then
        echo "FAIL: gitleaks $LABEL mirror commit count: source=$EXPECTED_COMMITS mirror=$MIRROR_COMMITS" >&2
        exit 1
    fi
fi

SCAN_LOG="$(mktemp)"
set +e
docker run --rm \
    -v "${SCAN_SOURCE}:/code:ro" \
    -v "${REPORT_DIR}:/out:rw" \
    --network none \
    --user "$(id -u):$(id -g)" \
    "$GITLEAKS_IMAGE" \
    "$MODE" /code \
    --redact=100 \
    --ignore-gitleaks-allow \
    --max-decode-depth=2 \
    --max-archive-depth=2 \
    --report-format=json \
    --report-path "/out/$(basename -- "$REPORT")" \
    -v 2>&1 | tee "$SCAN_LOG"
scan_rc=${PIPESTATUS[0]}
set -e

if [[ "$MODE" == "git" ]]; then
    if ! grep -Eq '(^|[^0-9])[1-9][0-9]* commits scanned\.' "$SCAN_LOG"; then
        echo "FAIL: gitleaks $LABEL did not prove a non-empty commit scan (source commits: $EXPECTED_COMMITS)" >&2
        exit 1
    fi
    if grep -Eq '(^|[^0-9])0 commits scanned\.' "$SCAN_LOG"; then
        echo "FAIL: gitleaks $LABEL scanned zero commits" >&2
        exit 1
    fi
fi

python3 "$CHECKER" \
    --label "$LABEL" \
    --return-code "$scan_rc" \
    --report "$REPORT"
