#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3.11 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
if [ ! -f frontend/dist/index.html ]; then
  echo 'Build the frontend using README.md before starting.' >&2
  exit 1
fi
if [ ! -f data/sessions.sqlite3 ]; then
  .venv/bin/python restore_sessions.py
fi
exec .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8790
