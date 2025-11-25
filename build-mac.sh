#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate || { echo "Activate venv first: source .venv/bin/activate"; exit 1; }
pyinstaller --noconfirm --onefile --add-data "app/static:app/static" --name ost-finder app/main.py
echo "Built dist/ost-finder"
