# Mini-PC deployment

The mini-PC is the **runtime target** for News Trader Advisor: Ollama, IBKR Gateway, the news daemon, and the web dashboard all run there. This repo must stay cloned and up to date on that machine.

**Git remote:** `https://github.com/Merxius2/news-trader-advisor.git`

## One-time setup (on the mini-PC)

```bash
# Clone (adjust path if you prefer another location)
git clone https://github.com/Merxius2/news-trader-advisor.git ~/news-trader-advisor
cd ~/news-trader-advisor

# Later phases — not required yet:
# python3 -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt
# cp .env.example .env   # fill in FINNHUB_API_KEY etc.
```

Or run the helper script copied to the mini-PC:

```bash
bash scripts/clone-on-mini-pc.sh ~/news-trader-advisor
```

## Update the mini-PC (after changes land on main)

### Option A — on the mini-PC directly

```bash
cd ~/news-trader-advisor
bash scripts/pull-on-mini-pc.sh
```

Pulls latest `main` and restarts `news-trader-advisor` (dashboard) automatically.

### Option B — from your dev machine via SSH

1. Copy the example config and fill in your mini-PC details:

```bash
cp config/mini-pc.env.example config/mini-pc.env
# Edit: MINI_PC_HOST, MINI_PC_REPO_PATH
```

2. Run the sync script:

```bash
./scripts/sync-mini-pc.sh
```

This SSHs into the mini-PC and runs `scripts/pull-on-mini-pc.sh` (pull + dashboard restart).

## Agent / developer workflow

Whenever code is merged or pushed to **`main`**:

1. **Pull on the mini-PC** (Option A or B above) — includes **automatic dashboard restart**.
2. If the change adds dependencies or config, run setup steps on the mini-PC (venv, pip install, copy `.env`).
3. Restart other services if applicable (daemon Phase 1+, IB Gateway — Phase 3+).

Agents completing deployable work should **sync the mini-PC** or explicitly tell the user to run the update commands.

## Web dashboard (view from Mac)

The dashboard runs on the mini-PC and is reachable on your LAN.

| Phase | URL (from Mac) | What runs |
|-------|----------------|-----------|
| Now (mockup) | `http://192.168.1.30:8080/dashboard.html` | Static mockup via `scripts/serve-dashboard.sh` |
| Phase 2+ | same host/port | FastAPI app (auto-switches when `src/web/app.py` exists) |

### Install / enable (one-time on mini-PC)

```bash
cd ~/news-trader-advisor
bash scripts/install-dashboard-service.sh
```

This installs `news-trader-advisor.service` (systemd), binds **0.0.0.0:8080**, and opens UFW port 8080.

### Service commands

```bash
sudo systemctl status news-trader-advisor
sudo systemctl restart news-trader-advisor   # manual restart if needed
sudo systemctl stop news-trader-advisor
```

`scripts/pull-on-mini-pc.sh` restarts the dashboard after every pull — no separate restart step needed.

## Config reference

| Variable | Example | Description |
|----------|---------|-------------|
| `MINI_PC_HOST` | `user@192.168.1.50` | SSH target |
| `MINI_PC_REPO_PATH` | `~/news-trader-advisor` | Clone path on mini-PC |

`config/mini-pc.env` is gitignored — never commit hostnames or credentials.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `git pull` conflicts | On mini-PC: `git status`; stash local changes or reset to `origin/main` if no local work |
| SSH permission denied | Ensure SSH key is on mini-PC; test with `ssh $MINI_PC_HOST` |
| Repo not cloned yet | Run one-time setup above |
