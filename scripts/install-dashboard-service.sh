#!/usr/bin/env bash
# Install and start the dashboard systemd service on the mini-PC.
# Run on the mini-PC (or via: ssh sylvester@192.168.1.30 'bash ~/news-trader-advisor/scripts/install-dashboard-service.sh')

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="news-trader-advisor.service"

chmod +x "$ROOT/scripts/serve-dashboard.sh"

sudo cp "$ROOT/scripts/news-trader-advisor.service" "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

if command -v ufw >/dev/null 2>&1 && sudo ufw status | grep -q "Status: active"; then
  sudo ufw allow 8080/tcp comment 'News Trader Advisor dashboard' || true
fi

echo "Dashboard service status:"
systemctl is-active "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager -l | head -15
echo
echo "Open from your Mac: http://$(hostname -I | awk '{print $1}'):8080/dashboard.html"
