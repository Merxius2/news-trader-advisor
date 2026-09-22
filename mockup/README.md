# Dashboard mockups

Static HTML previews of the advisor dashboard (sample data only).

## Files

| File | Variant | Plan |
|---|---|---|
| [`dashboard.html`](dashboard.html) | Bitvavo / crypto (default on mini-PC) | [`docs/PLAN-bitvavo.md`](../docs/PLAN-bitvavo.md) |
| [`dashboard-ibkr.html`](dashboard-ibkr.html) | IBKR / stocks | [`docs/PLAN.md`](../docs/PLAN.md) |

## Open locally

```bash
# From this directory
open dashboard.html   # macOS — Bitvavo fork (default)
xdg-open dashboard.html  # Linux
```

Or serve:

```bash
python3 -m http.server 8765
# Bitvavo: http://localhost:8765/dashboard.html
# IBKR:    http://localhost:8765/dashboard-ibkr.html
```

## Bitvavo mockup highlights

- **Bot control bar** — live status (idle, reading news, analyzing, trading) + start/stop toggle
- **Bot activity log** — visual timeline of trades, news, analysis, and system events
- **Trader allocation bar** — €420 / €500 deployed (bot budget cap)
- **Trader P&L cards** — portfolio, unrealized, win rate
- **P&L chart** — switch € / % and time ranges (1D, 1W, 1M, 3M, YTD, 1Y)
- **Trader holdings table** — crypto markets with `advisor-*` order tags
- **Crypto suggestions** — event types (etf_flow, regulation), source quality (confirmed / rumor)
- **Watchlist** — `BTC-EUR`, `ETH-EUR`, etc.

## IBKR mockup highlights

- **P&L summary** — today, unrealized, realized, net liquidation (paper)
- **Positions table** — per-ticker P&L with linked suggestion tags
- **Suggestions & reasoning** — equity news, would-do, risks
- **Live activity feed** — news polling, analysis, IBKR sync events

No backend, no API calls — design reference only.
