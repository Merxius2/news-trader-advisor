#!/usr/bin/env bash
# Run on the mini-PC: pull latest main and restart dashboard (and later daemon).
# Also invoked remotely by scripts/sync-mini-pc.sh.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== git pull ==="
git fetch origin
git pull --ff-only origin main
echo "At commit: $(git log -1 --oneline)"

echo "=== restart services ==="
if systemctl list-unit-files news-trader-advisor.service &>/dev/null \
   && systemctl is-enabled news-trader-advisor.service &>/dev/null; then
  sudo systemctl restart news-trader-advisor
  echo "news-trader-advisor: $(systemctl is-active news-trader-advisor)"
else
  echo "news-trader-advisor.service not installed — skip (run install-dashboard-service.sh once)"
fi

# Phase 1+: restart news daemon when unit exists
# if systemctl is-enabled news-trader-advisor-daemon.service &>/dev/null; then
#   sudo systemctl restart news-trader-advisor-daemon
# fi

echo "Done."
