#!/usr/bin/env bash
# Serve News Trader Advisor dashboard on the mini-PC.
# Mockup (now): static files from mockup/ on 0.0.0.0:8080
# Default page: mockup/dashboard.html (Bitvavo fork). IBKR: dashboard-ibkr.html
# Production (Phase 2+): uvicorn FastAPI when src/web/app.py exists

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${DASHBOARD_PORT:-8080}"
HOST="${DASHBOARD_HOST:-0.0.0.0}"

if [[ -f "$ROOT/src/web/app.py" ]] && [[ -x "$ROOT/.venv/bin/uvicorn" ]]; then
  cd "$ROOT"
  exec "$ROOT/.venv/bin/uvicorn" src.web.app:app --host "$HOST" --port "$PORT"
fi

cd "$ROOT/mockup"
exec python3 -m http.server "$PORT" --bind "$HOST"
