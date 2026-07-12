#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
BIN_DIR="$HOME/.local/bin"
STATE_DIR="$HOME/.local/state/systemkatalog"
NEW_UNIT="$UNIT_DIR/systemkatalog.service"
OLD_UNITS=("$UNIT_DIR/heimgewebe-systemkatalog.service" "$UNIT_DIR/cabinet.service")
OLD_DROPIN="$UNIT_DIR/cabinet.service.d"
BACKUP_DIR="$STATE_DIR/runtime-cutovers/$(date -u +%Y%m%dT%H%M%SZ)"
CUTOVER=0

case "${1:-}" in
  "") ;;
  --cutover) CUTOVER=1 ;;
  *) echo "Verwendung: $0 [--cutover]" >&2; exit 2 ;;
esac

die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
render() {
  python3 - "$1" "$2" "$HOME" "$REPO_ROOT" <<'PY'
from pathlib import Path
import sys
source, destination, home, root = map(Path, sys.argv[1:])
text = source.read_text(encoding="utf-8").replace("@HOME@", str(home)).replace("@SYSTEMKATALOG_ROOT@", str(root))
destination.write_text(text, encoding="utf-8")
PY
}

for tool in cp date find git install mkdir mktemp python3 rmdir sed seq sleep systemctl; do
  command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1 || die "Kein Systemkatalog-Repository: $REPO_ROOT"
python3 "$REPO_ROOT/scripts/validate_system_catalog.py" >/dev/null
python3 "$REPO_ROOT/scripts/render_system_catalog.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/render_ecosystem_registry_map.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/serve_system_catalog.py" --check >/dev/null

mkdir -p "$UNIT_DIR" "$BIN_DIR" "$BACKUP_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
render "$REPO_ROOT/ops/systemd/systemkatalog.service.tmpl" "$TMP/systemkatalog.service"

backup_one() {
  local source="$1"
  if [[ -e "$source" || -L "$source" ]]; then
    local name
    name="$(printf '%s' "$source" | sed 's#^/##;s#/#__#g')"
    cp -a -- "$source" "$BACKUP_DIR/$name"
  fi
}
for path in "$NEW_UNIT" "${OLD_UNITS[@]}" "$OLD_DROPIN" \
  "$BIN_DIR/systemkatalog" "$BIN_DIR/systemkatalogctl" "$BIN_DIR/heimgewebe-systemkatalog" \
  "$BIN_DIR/cabinet" "$BIN_DIR/cabinet-session" "$BIN_DIR/cabinetctl" "$BIN_DIR/cabinet-security-gate"
do
  backup_one "$path"
done

if (( CUTOVER )); then
  systemctl --user stop systemkatalog.service || true
  systemctl --user disable systemkatalog.service || true
  systemctl --user stop heimgewebe-systemkatalog.service || true
  systemctl --user disable heimgewebe-systemkatalog.service || true
  systemctl --user stop cabinet.service || true
  systemctl --user disable cabinet.service || true
fi

install -m 0644 "$TMP/systemkatalog.service" "$NEW_UNIT"
install -m 0755 "$REPO_ROOT/ops/bin/systemkatalog" "$BIN_DIR/systemkatalog"
install -m 0755 "$REPO_ROOT/ops/bin/systemkatalogctl" "$BIN_DIR/systemkatalogctl"

if [[ -d "$OLD_DROPIN" ]]; then
  find "$OLD_DROPIN" -mindepth 1 -maxdepth 1 -delete
  rmdir "$OLD_DROPIN"
fi
rm -f -- "${OLD_UNITS[@]}" \
  "$BIN_DIR/heimgewebe-systemkatalog" \
  "$BIN_DIR/cabinet" "$BIN_DIR/cabinet-session" "$BIN_DIR/cabinetctl" "$BIN_DIR/cabinet-security-gate"

systemctl --user daemon-reload

if (( CUTOVER )); then
  systemctl --user enable --now systemkatalog.service
  ready=0
  for _ in $(seq 1 40); do
    if python3 - <<'PY' >/dev/null 2>&1
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:4001/healthz", timeout=1) as response:
    assert response.status == 204
PY
    then ready=1; break; fi
    sleep 0.25
  done
  [[ $ready -eq 1 ]] || die "Systemkatalog wurde nicht erreichbar"
  "$REPO_ROOT/ops/install/audit-local-runtime.sh" --allow-dirty
fi

echo "Backup: $BACKUP_DIR"
echo "INSTALL-SYSTEMKATALOG-RUNTIME: PASS"
