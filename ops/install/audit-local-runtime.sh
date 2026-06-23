#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ALLOW_DIRTY=0

case "${1:-}" in
  "")
    ;;

  --allow-dirty)
    ALLOW_DIRTY=1
    ;;

  *)
    echo "Verwendung:"
    echo "  $0"
    echo "  $0 --allow-dirty"
    exit 2
    ;;
esac

REPO_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
  pwd
)"

APP_VERSION="0.4.4"
APP_ROOT="$HOME/.cabinet/app/v$APP_VERSION"

UNIT="$HOME/.config/systemd/user/cabinet.service"
DROPIN="$HOME/.config/systemd/user/cabinet.service.d/10-loopback-gate.conf"
RUNTIME_ENV="$HOME/.config/cabinet/runtime.env"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TMP_DIR"' EXIT

die() {
  printf '\nSTOP: %s\n' "$*" >&2
  exit 1
}

render_template() {
  local source="$1"
  local destination="$2"

  python3 - \
    "$source" \
    "$destination" \
    "$HOME" \
    "$REPO_ROOT" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
home = sys.argv[3]
repo_root = sys.argv[4]

text = source.read_text(
    encoding="utf-8",
    errors="strict",
)

text = text.replace(
    "@CABINET_ROOT@",
    repo_root,
)

text = text.replace(
    "@HOME@",
    home,
)

destination.write_text(
    text,
    encoding="utf-8",
)
PY
}

echo "=================================================="
echo "CABINET LOCAL RUNTIME AUDIT"
echo "=================================================="

echo
echo "== 1. Werkzeug- und Repository-Gate =="

for command_name in \
  cmp \
  git \
  mktemp \
  python3 \
  readlink \
  rm \
  stat \
  systemctl
do
  command -v "$command_name" >/dev/null 2>&1 ||
    die "Werkzeug fehlt: $command_name"
done

[[ -d "$REPO_ROOT/.git" ]] ||
  die "Kein Cabinet-Repository: $REPO_ROOT"

STATUS="$(
  git -C "$REPO_ROOT" \
    status \
    --porcelain=v1 \
    --untracked-files=all
)"

if [[ -n "$STATUS" ]] && (( ALLOW_DIRTY == 0 )); then
  printf '%s\n' "$STATUS"
  die "Cabinet-Working-Tree ist nicht sauber."
fi

echo "Root: $REPO_ROOT"

if [[ -z "$STATUS" ]]; then
  echo "Working Tree: clean"
else
  echo "Working Tree: dirty, explizit für Pre-Commit-Audit erlaubt"
fi

echo
echo "== 2. Systemd-Templates =="

render_template \
  "$REPO_ROOT/ops/systemd/cabinet.service.tmpl" \
  "$TMP_DIR/cabinet.service"

render_template \
  "$REPO_ROOT/ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl" \
  "$TMP_DIR/10-loopback-gate.conf"

cmp -s \
  "$TMP_DIR/cabinet.service" \
  "$UNIT" ||
  die "Lokale Cabinet-Unit driftet vom Template."

cmp -s \
  "$TMP_DIR/10-loopback-gate.conf" \
  "$DROPIN" ||
  die "Lokales Cabinet-Drop-in driftet vom Template."

echo "Cabinet-Unit: PASS"
echo "Loopback-Drop-in: PASS"

echo
echo "== 3. Lokale Werkzeuge =="

for name in \
  cabinet \
  cabinet-session \
  cabinetctl \
  cabinet-security-gate
do
  repo_file="$REPO_ROOT/ops/bin/$name"
  local_file="$HOME/.local/bin/$name"

  [[ -x "$repo_file" ]] ||
    die "Repo-Werkzeug fehlt oder ist nicht ausführbar: $repo_file"

  [[ -x "$local_file" ]] ||
    die "Lokales Werkzeug fehlt oder ist nicht ausführbar: $local_file"

  cmp -s \
    "$repo_file" \
    "$local_file" ||
    die "Lokales Werkzeug driftet: $name"

  echo "$name: PASS"
done

echo
echo "== 4. Safe-Export-Symlink =="

SAFE_LINK="$HOME/.local/bin/cabinet-safe-export"
EXPECTED_TARGET="$REPO_ROOT/scripts/cabinet-safe-export.sh"

[[ -L "$SAFE_LINK" ]] ||
  die "Safe-Export-Link fehlt."

[[ "$(readlink -f "$SAFE_LINK")" == "$EXPECTED_TARGET" ]] ||
  die "Safe-Export-Link zeigt auf das falsche Ziel."

echo "Safe-Export-Symlink: PASS"

echo
echo "== 5. Runtime-Environment =="

[[ -f "$RUNTIME_ENV" ]] ||
  die "Runtime-Environment fehlt: $RUNTIME_ENV"

MODE="$(
  stat -Lc '%a' "$RUNTIME_ENV"
)"

[[ "$MODE" == "600" ]] ||
  die "runtime.env hat nicht Modus 600: $MODE"

python3 - "$RUNTIME_ENV" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])

required = {
    "CABINET_TELEMETRY_DISABLED",
    "KB_PASSWORD",
    "GEMINI_API_KEY",
}

found: set[str] = set()

for raw_line in path.read_text(
    encoding="utf-8",
    errors="strict",
).splitlines():
    line = raw_line.strip()

    if not line or line.startswith("#"):
        continue

    if "=" not in line:
        raise SystemExit(
            "STOP: Nicht parsebare Zeile in runtime.env"
        )

    key, _ = line.split("=", 1)
    found.add(key.strip())

missing = required - found

if missing:
    raise SystemExit(
        "STOP: Fehlende Runtime-Schlüssel: "
        + ", ".join(sorted(missing))
    )

print("Runtime-Schlüssel: PASS")
PY

echo "Runtime-Dateimodus: PASS"

echo
echo "== 6. Dark-Default =="

"$REPO_ROOT/ops/patches/cabinet-v0.4.4-dark-default.py" \
  --app-root "$APP_ROOT" \
  --check

echo
echo "== 7. Servicevertrag =="

LOAD_STATE="$(
  systemctl --user show cabinet.service \
    -p LoadState \
    --value
)"

ACTIVE_STATE="$(
  systemctl --user show cabinet.service \
    -p ActiveState \
    --value
)"

SUB_STATE="$(
  systemctl --user show cabinet.service \
    -p SubState \
    --value
)"

WORKING_DIRECTORY="$(
  systemctl --user show cabinet.service \
    -p WorkingDirectory \
    --value
)"

[[ "$LOAD_STATE" == "loaded" ]] ||
  die "cabinet.service ist nicht geladen: $LOAD_STATE"

[[ "$ACTIVE_STATE" == "active" ]] ||
  die "cabinet.service ist nicht aktiv: $ACTIVE_STATE"

[[ "$SUB_STATE" == "running" ]] ||
  die "cabinet.service läuft nicht: $SUB_STATE"

[[ "$WORKING_DIRECTORY" == "$REPO_ROOT" ]] ||
  die "Falsches WorkingDirectory: $WORKING_DIRECTORY"

echo "LoadState:        $LOAD_STATE"
echo "ActiveState:      $ACTIVE_STATE"
echo "SubState:         $SUB_STATE"
echo "WorkingDirectory: $WORKING_DIRECTORY"
echo "Servicevertrag:   PASS"

echo
echo "== 8. Health =="

python3 - <<'PY'
from urllib.request import urlopen
import json

checks = (
    (
        "Cabinet-App",
        "http://127.0.0.1:4001/api/health",
    ),
    (
        "Cabinet-Daemon",
        "http://127.0.0.1:4100/health",
    ),
)

for label, url in checks:
    with urlopen(
        url,
        timeout=8,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8",
                errors="strict",
            )
        )

    if payload.get("status") != "ok":
        raise SystemExit(
            f"STOP: {label} meldet nicht ok: {payload}"
        )

    print(f"{label}: PASS")

print("HEALTH-GATE: PASS")
PY

echo
echo "=================================================="
echo "TARGET-PROOF: CABINET LOCAL RUNTIME MATCHES REPOSITORY"
echo "=================================================="
