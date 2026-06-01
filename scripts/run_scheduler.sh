#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -f "$HOME/.tg-sign.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.tg-sign.env"
fi

SLEEP_SECONDS="${SLEEP_SECONDS:-300}"

while true; do
  python -m src scheduler --accounts config/accounts.yaml --config config/tasks.yaml --state data/state.json
  sleep "$SLEEP_SECONDS"
done
