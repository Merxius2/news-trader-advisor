# Dashboard mockups

Static HTML previews of the advisor dashboard (sample data only).

## Files

| File | Variant | Plan |
|---|---|---|
| [`dashboard.html`](dashboard.html) | IBKR / stocks | [`docs/PLAN.md`](../docs/PLAN.md) |
| [`dashboard-bitvavo.html`](dashboard-bitvavo.html) | Bitvavo / crypto | [`docs/PLAN-bitvavo.md`](../docs/PLAN-bitvavo.md) |

## Open locally

```bash
# From this directory
open dashboard-bitvavo.html   # macOS — Bitvavo fork
xdg-open dashboard-bitvavo.html  # Linux
```

Or serve:

```bash
python3 -m http.server 8765
# IBKR:    http://localhost:8765/dashboard.html
# Bitvavo: http://localhost:8765/dashboard-bitvavo.html
```

## Bitvavo mockup highlights

- **Trader allocation bar** — €420 / €500 deployed (bot budget cap)
- **Trader P&L cards** — unrealized, realized, win rate (tagged fills only)
- **Account total row** — full Bitvavo balance vs non-trader (manual) portion
- **Trader holdings table** — crypto markets with `advisor-*` order tags
- **Crypto suggestions** — event types (etf_flow, regulation), source quality (confirmed / rumor)
- **Watchlist** — `BTC-EUR`, `ETH-EUR`, etc.

## IBKR mockup highlights

- **P&L summary** — today, unrealized, realized, net liquidation (paper)
- **Positions table** — per-ticker P&L with linked suggestion tags
- **Suggestions & reasoning** — equity news, would-do, risks
- **Live activity feed** — news polling, analysis, IBKR sync events

No backend, no API calls — design reference only.
