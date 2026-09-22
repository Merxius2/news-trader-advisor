#!/usr/bin/env bash
# Install systemd timer: auto pull + restart dashboard when main changes.
# Run on the mini-PC.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

chmod +x "$ROOT/scripts/check-and-deploy.sh" "$ROOT/scripts/pull-on-mini-pc.sh"

sudo cp "$ROOT/scripts/news-trader-advisor-deploy.service" /etc/systemd/system/
sudo cp "$ROOT/scripts/news-trader-advisor-deploy.timer" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable news-trader-advisor-deploy.timer
sudo systemctl start news-trader-advisor-deploy.timer

echo "Deploy trigger timer:"
systemctl is-active news-trader-advisor-deploy.timer
systemctl list-timers news-trader-advisor-deploy.timer --no-pager
echo
echo "Logs: journalctl -u news-trader-advisor-deploy.service -f"
