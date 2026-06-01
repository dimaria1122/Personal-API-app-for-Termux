#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

pkg update -y
pkg install -y python git termux-api
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
