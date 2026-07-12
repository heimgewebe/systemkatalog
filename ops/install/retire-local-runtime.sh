#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
BIN_DIR="$HOME/.local/bin"
STATE_DIR="$HOME/.local/state/systemkatalog"
UNIT="$UNIT_DIR/systemkatalog.service"
PROGRAM="$BIN_DIR/systemkatalog"
CONTROL="$BIN_DIR/systemkatalogctl"
MODE="dry-run"
AUTHORIZATION_REFERENCE=""
EXPECTED_HEAD=""
TIMESTAMP="${SYSTEMKATALOG_RETIREMENT_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$STATE_DIR/runtime-retirements/$TIMESTAMP"
ROLLBACK_NEEDED=0
WAS_ACTIVE="unknown"
WAS_ENABLED="unknown"
MAIN_PID="0"

die() {
  printf 'STOP: %s\n' "$*" >&2
  return 1
}

usage() {
  cat <<'USAGE'
Verwendung:
  retire-local-runtime.sh [--dry-run]
  retire-local-runtime.sh --apply \
    --authorization-reference <Bureau-Referenz> \
    --expected-head <40-stelliger Git-Commit>

Ohne --apply wird nur geprüft und ein Rückbauplan ausgegeben.
USAGE
}

while (( $# )); do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --apply)
      MODE="apply"
      shift
      ;;
    --authorization-reference)
      (( $# >= 2 )) || die "Wert für --authorization-reference fehlt"
      AUTHORIZATION_REFERENCE="$2"
      shift 2
      ;;
    --expected-head)
      (( $# >= 2 )) || die "Wert für --expected-head fehlt"
      EXPECTED_HEAD="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "Unbekanntes Argument: $1"
      ;;
  esac
done

for tool in cmp cp date git install mkdir mktemp python3 rm sha256sum systemctl; do
  command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
[[ "$TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || die "Ungültiger Retirement-Zeitstempel: $TIMESTAMP"
git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1 || die "Kein Systemkatalog-Repository: $REPO_ROOT"

CURRENT_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
if [[ "$MODE" == "apply" ]]; then
  [[ "$EXPECTED_HEAD" =~ ^[0-9a-f]{40}$ ]] || die "--expected-head muss ein vollständiger Git-Commit sein"
  [[ "$CURRENT_HEAD" == "$EXPECTED_HEAD" ]] || die "Repository-HEAD driftet: aktuell=$CURRENT_HEAD erwartet=$EXPECTED_HEAD"
  [[ -z "$(git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all)" ]] || die "Working Tree ist nicht sauber"
  [[ "$AUTHORIZATION_REFERENCE" =~ ^Bureau:[A-Z0-9][A-Z0-9-]*-T[0-9]{3,}$ ]] || die "Bureau-Autorisierungsreferenz muss das Format Bureau:<TASK-ID> besitzen"
fi

python3 "$REPO_ROOT/scripts/validate_system_catalog.py" >/dev/null
python3 "$REPO_ROOT/scripts/render_system_catalog.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/render_ecosystem_registry_map.py" --check >/dev/null
python3 "$REPO_ROOT/scripts/serve_system_catalog.py" --check >/dev/null

TMP="$(mktemp -d)"
cleanup() { rm -rf -- "$TMP"; }
trap cleanup EXIT
python3 - "$REPO_ROOT/ops/systemd/systemkatalog.service.tmpl" "$TMP/systemkatalog.service" "$HOME" "$REPO_ROOT" <<'PY'
from pathlib import Path
import sys
source, destination, home, root = map(Path, sys.argv[1:])
text = source.read_text(encoding="utf-8").replace("@HOME@", str(home)).replace("@SYSTEMKATALOG_ROOT@", str(root))
destination.write_text(text, encoding="utf-8")
PY

TARGETS=("$UNIT" "$PROGRAM" "$CONTROL")
present=0
for path in "${TARGETS[@]}"; do
  if [[ -e "$path" || -L "$path" ]]; then
    ((present += 1))
    [[ -f "$path" && ! -L "$path" ]] || die "Runtimeziel ist keine reguläre Datei: $path"
  fi
done

if (( present == 0 )); then
  if systemctl --user is-active --quiet systemkatalog.service; then
    die "Runtime-Dateien fehlen, aber der Dienst ist noch aktiv"
  fi
  if systemctl --user is-enabled --quiet systemkatalog.service; then
    die "Runtime-Dateien fehlen, aber der Dienst ist noch aktiviert"
  fi
  echo "SYSTEMKATALOG-RUNTIME-RETIREMENT: ALREADY-RETIRED"
  exit 0
fi
(( present == ${#TARGETS[@]} )) || die "Unvollständige Runtimeinstallation: $present von ${#TARGETS[@]} Zielen vorhanden"

cmp -s "$TMP/systemkatalog.service" "$UNIT" || die "Installierte Unit driftet vom Repository"
cmp -s "$REPO_ROOT/ops/bin/systemkatalog" "$PROGRAM" || die "Installiertes Programm driftet vom Repository"
cmp -s "$REPO_ROOT/ops/bin/systemkatalogctl" "$CONTROL" || die "Installiertes Kontrollwerkzeug driftet vom Repository"

if [[ "$MODE" == "dry-run" ]]; then
  printf 'Rückbau geprüft; keine Änderung ausgeführt.\n'
  printf 'Repository-HEAD: %s\n' "$CURRENT_HEAD"
  printf 'Geplanter Backup-Pfad: %s\n' "$BACKUP_DIR"
  printf 'Geplante Entfernung:\n'
  printf '  %s\n' "${TARGETS[@]}"
  echo "SYSTEMKATALOG-RUNTIME-RETIREMENT-DRY-RUN: PASS"
  exit 0
fi

[[ ! -e "$BACKUP_DIR" ]] || die "Backup-Ziel existiert bereits: $BACKUP_DIR"
WAS_ACTIVE="$(systemctl --user show systemkatalog.service -p ActiveState --value 2>/dev/null || printf 'unknown')"
WAS_ENABLED="$(systemctl --user is-enabled systemkatalog.service 2>/dev/null || true)"
[[ -n "$WAS_ENABLED" ]] || WAS_ENABLED="unknown"
MAIN_PID="$(systemctl --user show systemkatalog.service -p MainPID --value 2>/dev/null || true)"
[[ "$MAIN_PID" =~ ^[0-9]+$ ]] || MAIN_PID=0

mkdir -p "$BACKUP_DIR"
cp -a -- "$UNIT" "$BACKUP_DIR/systemkatalog.service"
cp -a -- "$PROGRAM" "$BACKUP_DIR/systemkatalog"
cp -a -- "$CONTROL" "$BACKUP_DIR/systemkatalogctl"
(
  cd "$BACKUP_DIR"
  sha256sum systemkatalog.service systemkatalog systemkatalogctl > manifest.sha256
)
python3 - "$BACKUP_DIR/retirement-receipt.json" "$AUTHORIZATION_REFERENCE" "$CURRENT_HEAD" "$TIMESTAMP" "$WAS_ACTIVE" "$WAS_ENABLED" "$MAIN_PID" "${TARGETS[@]}" <<'PY'
import json
from pathlib import Path
import sys
output = Path(sys.argv[1])
authorization, head, timestamp, active, enabled, pid = sys.argv[2:8]
targets = sys.argv[8:]
payload = {
    "kind": "systemkatalog_runtime_retirement_receipt",
    "version": 1,
    "authorizationReference": authorization,
    "repositoryHead": head,
    "retirementId": timestamp,
    "status": "prepared",
    "previousRuntime": {
        "activeState": active,
        "enabledState": enabled,
        "mainPid": int(pid),
    },
    "retiredPaths": targets,
    "preservedStateRoot": str(output.parent.parent.parent),
}
output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
cat > "$BACKUP_DIR/RESTORE.md" <<EOF_RESTORE
# Systemkatalog-Runtime wiederherstellen

Dieses lokale Backup gehört zur Autorisierung \`$AUTHORIZATION_REFERENCE\` und zum Repository-Commit \`$CURRENT_HEAD\`.

Wiederherstellung:

\`\`\`bash
install -m 0644 "$BACKUP_DIR/systemkatalog.service" "$UNIT"
install -m 0755 "$BACKUP_DIR/systemkatalog" "$PROGRAM"
install -m 0755 "$BACKUP_DIR/systemkatalogctl" "$CONTROL"
systemctl --user daemon-reload
systemctl --user enable --now systemkatalog.service
\`\`\`

Vor der Wiederherstellung \`manifest.sha256\` prüfen. Private Cabinet- und Systemkatalog-Zustände wurden durch den Rückbau nicht gelöscht.
EOF_RESTORE

set_receipt_status() {
  local status="$1"
  local result_code="$2"
  python3 - "$BACKUP_DIR/retirement-receipt.json" "$status" "$result_code" <<'PY'
import json
from pathlib import Path
import sys
path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["status"] = sys.argv[2]
payload["resultCode"] = int(sys.argv[3])
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

rollback() {
  local rc=$?
  trap - ERR
  if (( ROLLBACK_NEEDED )); then
    printf 'Rückbau fehlgeschlagen; installierte Runtime wird aus %s wiederhergestellt.\n' "$BACKUP_DIR" >&2
    install -m 0644 "$BACKUP_DIR/systemkatalog.service" "$UNIT" || true
    install -m 0755 "$BACKUP_DIR/systemkatalog" "$PROGRAM" || true
    install -m 0755 "$BACKUP_DIR/systemkatalogctl" "$CONTROL" || true
    systemctl --user daemon-reload || true
    if [[ "$WAS_ENABLED" == "enabled" ]]; then
      systemctl --user enable systemkatalog.service || true
    fi
    if [[ "$WAS_ACTIVE" == "active" ]]; then
      systemctl --user start systemkatalog.service || true
    fi
    set_receipt_status "rolled_back" "$rc" || true
  fi
  exit "$rc"
}
trap rollback ERR
ROLLBACK_NEEDED=1

systemctl --user stop systemkatalog.service
systemctl --user disable systemkatalog.service
rm -f -- "$UNIT" "$PROGRAM" "$CONTROL"
systemctl --user daemon-reload
systemctl --user reset-failed systemkatalog.service || true

for path in "${TARGETS[@]}"; do
  [[ ! -e "$path" && ! -L "$path" ]] || die "Runtimeziel blieb nach Rückbau bestehen: $path"
done
if systemctl --user is-active --quiet systemkatalog.service; then
  die "Dienst ist nach Rückbau noch aktiv"
fi
if systemctl --user is-enabled --quiet systemkatalog.service; then
  die "Dienst ist nach Rückbau noch aktiviert"
fi
if (( MAIN_PID > 1 )) && kill -0 "$MAIN_PID" 2>/dev/null; then
  die "Vorheriger Runtimeprozess läuft nach Rückbau weiter: PID $MAIN_PID"
fi

set_receipt_status "retired" 0
ROLLBACK_NEEDED=0
trap - ERR
printf 'Backup: %s\n' "$BACKUP_DIR"
echo "SYSTEMKATALOG-RUNTIME-RETIREMENT: PASS"
