#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

pkg update -y
pkg install -y python git termux-api python-yaml

if ! python -m pip install --user -r requirements.txt; then
  echo "pip dependency install failed."
  echo "PyYAML is installed via Termux package python-yaml."
  echo "If Pyrogram is missing, run: python -m pip install --user pyrogram tgcrypto"
  exit 1
fi
