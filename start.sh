#!/usr/bin/env bash
# Start the Airfinder server (backend + frontend are served by Flask on one port).
cd "$(dirname "$0")" || exit 1

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example to .env and set SUPER_ADMIN_EMAIL / SUPER_ADMIN_PASSWORD."
  exit 1
fi

PY=python
command -v python >/dev/null 2>&1 || PY=python3

# Install dependencies only when requirements.txt changed
STAMP=.deps_installed
if [ ! -f "$STAMP" ] || [ requirements.txt -nt "$STAMP" ]; then
  echo "Installing dependencies..."
  "$PY" -m pip install -q -r requirements.txt && touch "$STAMP" || exit 1
fi

PORT=$(grep -E '^PORT=' .env | cut -d= -f2 | tr -d '\r')
echo "Starting Airfinder at http://localhost:${PORT:-5000}  (Ctrl+C to stop)"
"$PY" run.py
