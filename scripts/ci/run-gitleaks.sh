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

REPORT_DIR="$(dirname "$REPORT")"
mkdir -p "$REPORT_DIR"

set +e
docker run --rm \
    -v "${SOURCE}:/code:ro" \
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
    --report-path "/out/$(basename "$REPORT")" \
    -v
scan_rc=$?
set -e

python3 "$CHECKER" \
    --label "$LABEL" \
    --return-code "$scan_rc" \
    --report "$REPORT"
