#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
ALLOW_DIRTY=0
case "${1:-}" in
  "") ;;
  --allow-dirty) ALLOW_DIRTY=1 ;;
  *) echo "Verwendung: $0 [--allow-dirty]" >&2; exit 2 ;;
esac

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT="$HOME/.config/systemd/user/systemkatalog.service"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
render() {
  python3 - "$1" "$2" "$HOME" "$REPO_ROOT" <<'PY'
from pathlib import Path
import sys
source, destination, home, root = map(Path, sys.argv[1:])
destination.write_text(source.read_text().replace("@HOME@", str(home)).replace("@SYSTEMKATALOG_ROOT@", str(root)))
PY
}

status="$(git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all)"
[[ -z "$status" || $ALLOW_DIRTY -eq 1 ]] || die "Working Tree ist nicht sauber"
python3 "$REPO_ROOT/scripts/validate_system_catalog.py" >/dev/null
python3 "$REPO_ROOT/scripts/render_system_catalog.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/render_ecosystem_registry_map.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/serve_system_catalog.py" --check >/dev/null
render "$REPO_ROOT/ops/systemd/systemkatalog.service.tmpl" "$TMP/unit"
cmp -s "$TMP/unit" "$UNIT" || die "Installierte Unit driftet"
for name in systemkatalog systemkatalogctl; do
  cmp -s "$REPO_ROOT/ops/bin/$name" "$HOME/.local/bin/$name" || die "Installiertes Werkzeug driftet: $name"
done
for path in \
  "$HOME/.config/systemd/user/heimgewebe-systemkatalog.service" \
  "$HOME/.local/bin/heimgewebe-systemkatalog" \
  "$HOME/.local/bin/cabinet" "$HOME/.local/bin/cabinet-session" "$HOME/.local/bin/cabinetctl" "$HOME/.local/bin/cabinet-security-gate" \
  "$HOME/.config/systemd/user/cabinet.service" "$HOME/.config/systemd/user/cabinet.service.d"
do
  [[ ! -e "$path" && ! -L "$path" ]] || die "Alte Runtimefläche noch aktiv: $path"
done
[[ "$(systemctl --user show systemkatalog.service -p LoadState --value)" == loaded ]] || die "Unit nicht geladen"
[[ "$(systemctl --user show systemkatalog.service -p ActiveState --value)" == active ]] || die "Unit nicht aktiv"
[[ "$(systemctl --user show systemkatalog.service -p SubState --value)" == running ]] || die "Unit läuft nicht"
[[ "$(systemctl --user is-enabled systemkatalog.service)" == enabled ]] || die "Unit nicht aktiviert"

python3 - <<'PY'
import json, socket, urllib.request
base = "http://127.0.0.1:4001"
with urllib.request.urlopen(base + "/healthz", timeout=3) as response:
    assert response.status == 204
with urllib.request.urlopen(base + "/api/catalog.json", timeout=3) as response:
    data = json.load(response)
assert data["kind"] == "system_catalog"
assert data["title"] == "Systemkatalog"
assert len(data["systems"]) == 19
assert len(data["relations"]) == 24
with urllib.request.urlopen(base + "/", timeout=3) as response:
    assert response.status == 200 and b"Systemkatalog" in response.read()
try:
    socket.create_connection(("127.0.0.1", 4100), timeout=0.5)
except OSError:
    pass
else:
    raise SystemExit("STOP: alter externer Workspace-Port ist weiterhin offen")
PY

echo "TARGET-PROOF: SYSTEMKATALOG RUNTIME MATCHES REPOSITORY"
