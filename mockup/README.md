# Dashboard mockup

Static HTML preview of the News Advisor dashboard (sample data only).

## Open locally

```bash
# From this directory
open dashboard.html          # macOS
xdg-open dashboard.html      # Linux
```

Or serve it:

```bash
python3 -m http.server 8765
# Visit http://localhost:8765/dashboard.html
```

## What it shows

- **P&L summary** — today, unrealized, realized, net liquidation (IBKR paper)
- **Positions table** — per-ticker P&L with linked suggestion tags
- **Suggestions & reasoning** — headline, confidence, model rationale, would-do, risks
- **Live activity feed** — news polling, analysis, IBKR sync events
- **Watchlist** — tickers with current signal (buy / hold / reduce)

No backend, no API calls — design reference only.
