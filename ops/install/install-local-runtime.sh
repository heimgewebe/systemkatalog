#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
  pwd
)"

APP_VERSION="0.4.4"
APP_ROOT="$HOME/.cabinet/app/v$APP_VERSION"

UNIT_DIR="$HOME/.config/systemd/user"
DROPIN_DIR="$UNIT_DIR/cabinet.service.d"
BIN_DIR="$HOME/.local/bin"
RUNTIME_ENV="$HOME/.config/cabinet/runtime.env"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$HOME/.local/state/cabinet/ops-backups/$STAMP"

RESTART=0

case "${1:-}" in
  "")
    ;;

  --restart)
    RESTART=1
    ;;

  *)
    echo "Verwendung:"
    echo "  $0"
    echo "  $0 --restart"
    exit 2
    ;;
esac

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
echo "INSTALL CABINET LOCAL RUNTIME"
echo "=================================================="

for command_name in \
  cp \
  date \
  install \
  ln \
  mkdir \
  mktemp \
  python3 \
  rm \
  sed \
  stat \
  systemctl
do
  command -v "$command_name" >/dev/null 2>&1 ||
    die "Werkzeug fehlt: $command_name"
done

[[ -d "$REPO_ROOT/.git" ]] ||
  die "Kein Cabinet-Repository: $REPO_ROOT"

[[ -f "$RUNTIME_ENV" ]] ||
  die "runtime.env fehlt. Vorlage: ops/env/runtime.env.example"

MODE="$(
  stat -Lc '%a' "$RUNTIME_ENV"
)"

[[ "$MODE" == "600" ]] ||
  die "runtime.env muss Modus 600 besitzen: aktuell $MODE"

mkdir -p \
  "$BACKUP_DIR" \
  "$UNIT_DIR" \
  "$DROPIN_DIR" \
  "$BIN_DIR"

for path in \
  "$UNIT_DIR/cabinet.service" \
  "$DROPIN_DIR/10-loopback-gate.conf" \
  "$BIN_DIR/cabinet" \
  "$BIN_DIR/cabinet-session" \
  "$BIN_DIR/cabinetctl" \
  "$BIN_DIR/cabinet-security-gate" \
  "$BIN_DIR/cabinet-safe-export"
do
  if [[ -e "$path" ]] || [[ -L "$path" ]]; then
    backup_name="$(
      printf '%s' "$path" |
      sed 's#^/##; s#/#__#g'
    )"

    cp -a -- \
      "$path" \
      "$BACKUP_DIR/$backup_name"
  fi
done

TMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TMP_DIR"' EXIT

render_template \
  "$REPO_ROOT/ops/systemd/cabinet.service.tmpl" \
  "$TMP_DIR/cabinet.service"

render_template \
  "$REPO_ROOT/ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl" \
  "$TMP_DIR/10-loopback-gate.conf"

install \
  -m 0644 \
  "$TMP_DIR/cabinet.service" \
  "$UNIT_DIR/cabinet.service"

install \
  -m 0644 \
  "$TMP_DIR/10-loopback-gate.conf" \
  "$DROPIN_DIR/10-loopback-gate.conf"

for name in \
  cabinet \
  cabinet-session \
  cabinetctl \
  cabinet-security-gate
do
  install \
    -m 0755 \
    "$REPO_ROOT/ops/bin/$name" \
    "$BIN_DIR/$name"
done

rm -f -- "$BIN_DIR/cabinet-safe-export"

ln -s \
  "$REPO_ROOT/scripts/cabinet-safe-export.sh" \
  "$BIN_DIR/cabinet-safe-export"

"$REPO_ROOT/ops/patches/cabinet-v0.4.4-dark-default.py" \
  --app-root "$APP_ROOT" \
  --apply

systemctl --user daemon-reload

if (( RESTART == 1 )); then
  systemctl --user restart cabinet.service

  sleep 3

  "$REPO_ROOT/ops/install/audit-local-runtime.sh"
else
  echo
  echo "Installation abgeschlossen."
  echo "Der Dienst wurde nicht neu gestartet."
  echo
  echo "Für Aktivierung und vollständigen Audit:"
  echo "  $0 --restart"
fi

echo
echo "Backup:"
echo "  $BACKUP_DIR"

echo
echo "INSTALL-LOCAL-RUNTIME: PASS"
