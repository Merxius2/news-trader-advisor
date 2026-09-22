# News Trader Advisor

Local news-driven **crypto advisor** for your mini-PC: Ollama analyzes headlines → structured suggestions with reasoning → Bitvavo **read-only** sync and trader sub-ledger P&amp;L. Auto-trading is opt-in (Phase 6+ only).

An IBKR / stocks variant is planned in parallel — see [`docs/PLAN.md`](docs/PLAN.md).

## Status

**Planning / mockup only** — no backend yet. Default dashboard mockup: [`mockup/dashboard.html`](mockup/dashboard.html) (Bitvavo fork).

## Agent workflow

Agents should load [`.instructions`](.instructions) and [`docs/repo-map.json`](docs/repo-map.json) at session start. Cursor auto-loads [`AGENTS.md`](AGENTS.md), which points to both.

After changes merge to `main`, **update the mini-PC** — see [`docs/mini-pc.md`](docs/mini-pc.md) or run `./scripts/sync-mini-pc.sh`.

- [`docs/PLAN.md`](docs/PLAN.md) — IBKR / stocks handoff: architecture, phases, schema, guardrails
- [`docs/PLAN-bitvavo.md`](docs/PLAN-bitvavo.md) — Bitvavo / crypto fork (reusable template for both variants)
- [`docs/mini-pc.md`](docs/mini-pc.md) — clone and sync repo on the mini-PC
- [`mockup/dashboard.html`](mockup/dashboard.html) — Bitvavo/crypto dashboard mockup (default on mini-PC)
- [`mockup/dashboard-ibkr.html`](mockup/dashboard-ibkr.html) — IBKR/stocks dashboard mockup
- [`mockup/README.md`](mockup/README.md) — how to open the mockup locally

## Planned features

- Hourly news digest + trigger on new crypto headlines
- Watchlist with per-market signals (`BTC-EUR`, etc.)
- Suggestions with full model reasoning (visible before any trade)
- **Trader allocation** sub-ledger (tagged `advisor-*` orders only — manual holdings excluded)
- Bitvavo read-only sync → trader portfolio, holdings, activity log
- Bot run/stop control and live status (idle · reading news · analyzing · trading)
- Web dashboard — see [Dashboard mockup → plan mapping](#dashboard-mockup--plan-mapping) below

## Dashboard mockup → plan mapping

Reference UI: [`mockup/dashboard.html`](mockup/dashboard.html) · Full spec: [`docs/PLAN-bitvavo.md` §8](docs/PLAN-bitvavo.md#8-dashboard)

| Mockup element | Phase | Plan / implementation |
|---|---|---|
| **Sidebar** — logo, trader badge, nav links | 2 | [PLAN-bitvavo §8](docs/PLAN-bitvavo.md#8-dashboard) — `templates/base.html`; nav routes in Phase 2 |
| **Status panel** — Bitvavo, allocation, Ollama, news poll, reconcile | 2–4 | Phase 2: Ollama + news poll; Phase 3: Bitvavo sync; Phase 4: allocation + reconcile |
| **Top bar** — date, sync time, **Run news now**, **Sync Bitvavo** | 2–3 | Phase 2: manual news trigger + HTMX refresh; Phase 3: sync endpoint |
| **Bot control bar** — current activity, state pills, **start/stop toggle** | 2, 6 | Phase 2: daemon heartbeat + idle/news/analysis states; Phase 6: trading state + kill switch |
| **Trader allocation bar** — deployed € / cap, reserve | 4 | [PLAN-bitvavo §6](docs/PLAN-bitvavo.md#6-trader-allocation--sub-ledger-core-product-requirement) — `TraderLedger`, `trader_config` |
| **Trader P&amp;L cards** — portfolio, unrealized, win rate | 4–5 | Phase 4: sub-ledger cards; Phase 5: win rate from `trader_fills` history |
| **P&amp;L chart** — € / % toggle, 1D–1Y periods, hover tooltip | 5 | `trader_snapshots` time series; chart API + front-end (mockup JS → FastAPI/HTMX) |
| **Activity log** — timeline, filters (Trade · News · Analysis · Sync · System · Idle) | 2–6 | `activity_log` table + `event_type` enum; filters in Phase 2 UI; trade/sync types from Phase 3+ |
| **Trader holdings table** — sub-ledger qty, tags, linked suggestions | 4 | `trader_positions`, `trader_fills`, `suggestion_trades`; footnote for manual account holdings |
| **Suggestions panel** — reasoning, would-do, risks, event_type | 1–2 | Phase 1: `CryptoAnalysisResult`; Phase 2: dashboard cards from `suggestions` + `analyses` |
| **Watchlist** — markets, signal dots, action tags | 2 | `config/watchlist.yaml` + latest suggestion per market |
| **Account overview** (nav page, not on home) | 3 | Full Bitvavo balances — [PLAN-bitvavo §7](docs/PLAN-bitvavo.md#7-bitvavo-integration); separate route |
| **Digests / Settings** (nav pages) | 1–2 | Phase 1: markdown reports; Phase 2: digest list + settings form |

Home dashboard focuses on **trader bot performance only** — full account totals live on **Account overview**, not the home page.

## Stack (planned)

- Python, FastAPI, SQLite, APScheduler, HTMX
- Ollama (e.g. Qwen2.5:7b or Finance-Llama-8B)
- Bitvavo REST API (read-only Phases 3–5; optional spot orders Phase 6+)

## Mockup

```bash
cd mockup
python3 -m http.server 8765
# http://localhost:8765/dashboard.html
```

## License

Private — personal project.
