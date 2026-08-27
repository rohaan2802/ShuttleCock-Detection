#!/usr/bin/env bash
# Run inside a Lightning AI Studio (or any Linux cloud box).
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -q -r webapp/requirements.txt
exec python webapp/app.py
