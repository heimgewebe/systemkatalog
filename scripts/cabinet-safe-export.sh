#!/usr/bin/env bash
set -euo pipefail
umask 077

SOURCE="${1:-$HOME/repos/cabinet}"

if [[ $# -ge 2 ]]; then
  DESTINATION="$2"
else
  STAMP="$(date +%Y%m%d-%H%M%S)"
  DESTINATION="$HOME/exports/cabinet-safe/cabinet-$STAMP"
fi

RUNTIME_ENV="${CABINET_RUNTIME_ENV:-$HOME/.config/cabinet/runtime.env}"

command -v rsync >/dev/null 2>&1 || {
  echo "STOP: rsync fehlt." >&2
  exit 2
}

command -v python3 >/dev/null 2>&1 || {
  echo "STOP: python3 fehlt." >&2
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

Created:  $(date --iso-8601=seconds)
Source:   $SOURCE
Git HEAD: $(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || echo unavailable)

Excluded:
- .git
- SQLite runtime indexes
- .cabinet-state
- global agents and their runtime
- agent configuration, runtime and conversations
- jobs
- environment files and key files
- logs and PID files
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

python3 - "$DESTINATION" "$RUNTIME_ENV" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
runtime_env = Path(sys.argv[2])

secret_name = re.compile(
    r"(PASSWORD|TOKEN|SECRET|API_KEY|PRIVATE_KEY|CLIENT_SECRET)",
    re.IGNORECASE,
)

env_key = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

secret_values: list[bytes] = []

if runtime_env.is_file():
    for raw_line in runtime_env.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not env_key.fullmatch(key):
            continue

        if not secret_name.search(key):
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        encoded = value.encode("utf-8")

        if len(encoded) >= 8:
            secret_values.append(encoded)

private_key_prefix = b"-----BEGIN "
private_key_names = (
    b"PRIVATE KEY",
    b"RSA PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"EC PRIVATE KEY",
)

private_key_markers = [
    private_key_prefix + name + b"-----"
    for name in private_key_names
]

secret_hits: set[str] = set()
private_key_hits: set[str] = set()

for path in root.rglob("*"):
    if not path.is_file():
        continue

    try:
        content = path.read_bytes()
    except OSError:
        continue

    relative = str(path.relative_to(root))

    if any(value in content for value in secret_values):
        secret_hits.add(relative)

    if any(marker in content for marker in private_key_markers):
        private_key_hits.add(relative)

if secret_hits or private_key_hits:
    if secret_hits:
        print(
            "STOP: Konkreter Wert aus der Runtime-Konfiguration "
            "wurde im Export gefunden.",
            file=sys.stderr,
        )

        for hit in sorted(secret_hits):
            print(f"- {hit}", file=sys.stderr)

    if private_key_hits:
        print(
            "STOP: Private-Key-Marker wurde im Export gefunden.",
            file=sys.stderr,
        )

        for hit in sorted(private_key_hits):
            print(f"- {hit}", file=sys.stderr)

    raise SystemExit(7)

print("Secret-Inhaltsprüfung: PASS")
PY

chmod -R go-rwx "$DESTINATION"

echo "SAFE-EXPORT: PASS"
echo "$DESTINATION"
