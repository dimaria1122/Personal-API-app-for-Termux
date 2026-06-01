#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -f "$HOME/.tg-sign.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.tg-sign.env"
elif [ -f "config/public-api.env" ]; then
  # shellcheck disable=SC1091
  source "config/public-api.env"
fi

mkdir -p data/control-bot

python -m src.control_bot
