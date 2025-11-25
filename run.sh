#!/usr/bin/env bash
set -euo pipefail
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip wheel >/dev/null
pip install -r requirements.txt
python -m app.main
