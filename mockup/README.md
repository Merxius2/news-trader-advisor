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

See [`README.md`](../README.md#dashboard-mockup--plan-mapping) and [`docs/PLAN-bitvavo.md` §8](../docs/PLAN-bitvavo.md#8-dashboard) for full component → phase mapping.

| Component | Phase |
|---|---|
| Sidebar, status panel, top bar actions | 2–4 |
| Bot control bar + start/stop toggle | 2, 6 |
| Activity log + type filters | 2–6 |
| Suggestions + reasoning, watchlist | 2 |
| Trader allocation bar, P&L cards, holdings table | 4 |
| P&L chart (€ / %, 1D–1Y, hover) | 5 |
| Account overview (nav page, not on home) | 3 |

## IBKR mockup highlights

- **P&L summary** — today, unrealized, realized, net liquidation (paper)
- **Positions table** — per-ticker P&L with linked suggestion tags
- **Suggestions & reasoning** — equity news, would-do, risks
- **Live activity feed** — news polling, analysis, IBKR sync events

No backend, no API calls — design reference only.
