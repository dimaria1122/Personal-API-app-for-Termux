#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -f "$HOME/.tg-sign.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.tg-sign.env"
fi

python -m src login --accounts config/accounts.yaml --sessions-dir data/sessions
