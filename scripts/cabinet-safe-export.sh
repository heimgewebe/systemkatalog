#!/usr/bin/env bash
set -euo pipefail
umask 077

SOURCE="${1:-$HOME/cabinet}"

if [[ $# -ge 2 ]]; then
  DESTINATION="$2"
else
  STAMP="$(date +%Y%m%d-%H%M%S)"
  DESTINATION="$HOME/exports/cabinet-safe/cabinet-$STAMP"
fi

command -v rsync >/dev/null 2>&1 || {
  echo "STOP: rsync fehlt." >&2
  exit 2
}

[[ -d "$SOURCE" ]] || {
  echo "STOP: Quelle fehlt: $SOURCE" >&2
  exit 3
}

[[ ! -e "$DESTINATION" ]] || {
  echo "STOP: Ziel existiert bereits: $DESTINATION" >&2
  exit 4
}

mkdir -p "$DESTINATION"

rsync -a \
  --prune-empty-dirs \
  --exclude='.git/' \
  --exclude='.cabinet.db' \
  --exclude='.cabinet.db-*' \
  --exclude='**/.cabinet.db' \
  --exclude='**/.cabinet.db-*' \
  --exclude='.cabinet-state/' \
  --exclude='**/.cabinet-state/' \
  --exclude='.global-agents/' \
  --exclude='.agents/.runtime/' \
  --exclude='.agents/.conversations/' \
  --exclude='.agents/.config/' \
  --exclude='.agents/.config.json' \
  --exclude='**/.agents/.runtime/' \
  --exclude='**/.agents/.conversations/' \
  --exclude='**/.agents/.memory/' \
  --exclude='**/.agents/.messages/' \
  --exclude='**/.jobs/' \
  --exclude='.cabinet.env' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='*.pem' \
  --exclude='*.key' \
  --exclude='*.log' \
  --exclude='*.pid' \
  --exclude='.DS_Store' \
  "$SOURCE/" \
  "$DESTINATION/"

cat >"$DESTINATION/SAFE_EXPORT_MANIFEST.txt" <<EOF
Cabinet Safe Export

Created: $(date --iso-8601=seconds)
Source:  $SOURCE
Git HEAD: $(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || echo unavailable)

Excluded:
- .git
- SQLite runtime indexes
- .cabinet-state
- global agents and their runtime
- agent config, runtime and conversations
- jobs
- environment and key files
- logs and pid files
EOF

for forbidden in \
  "$DESTINATION/.git" \
  "$DESTINATION/.cabinet-state" \
  "$DESTINATION/.global-agents" \
  "$DESTINATION/.agents/.runtime" \
  "$DESTINATION/.agents/.config" \
  "$DESTINATION/.agents/.conversations"
do
  if [[ -e "$forbidden" ]]; then
    echo "STOP: Verbotener Exportpfad: $forbidden" >&2
    exit 5
  fi
done

if find "$DESTINATION" \
     -type f \
     \( \
       -name '.cabinet.db' \
       -o -name '.cabinet.db-*' \
       -o -name 'daemon-token' \
       -o -name '*.pem' \
       -o -name '*.key' \
     \) \
     -print |
   grep -q .
then
  echo "STOP: Verbotene Datei im Export:" >&2

  find "$DESTINATION" \
    -type f \
    \( \
      -name '.cabinet.db' \
      -o -name '.cabinet.db-*' \
      -o -name 'daemon-token' \
      -o -name '*.pem' \
      -o -name '*.key' \
    \) \
    -print >&2

  exit 6
fi

if grep -RIlE \
     'KB_PASSWORD|GEMINI_API_KEY|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY' \
     "$DESTINATION" \
     >/tmp/cabinet-safe-export-secret-hits.$$ \
     2>/dev/null
then
  cat /tmp/cabinet-safe-export-secret-hits.$$ >&2
  rm -f /tmp/cabinet-safe-export-secret-hits.$$

  echo "STOP: Mögliches Secret im Export." >&2
  exit 7
fi

rm -f /tmp/cabinet-safe-export-secret-hits.$$

chmod -R go-rwx "$DESTINATION"

echo "SAFE-EXPORT: PASS"
echo "$DESTINATION"
