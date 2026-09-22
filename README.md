# News Trader Advisor

Local news-driven trading **advisor** for your mini-PC: Ollama analyzes headlines and suggests actions; IBKR **paper account** tracks P&amp;L. No live trading in v1.

## Status

**Planning / mockup only** — no backend yet.

- [`docs/PLAN.md`](docs/PLAN.md) — full project handoff: architecture, phases, schema, guardrails
- [`mockup/dashboard.html`](mockup/dashboard.html) — static dashboard preview (sample data)
- [`mockup/README.md`](mockup/README.md) — how to open the mockup locally

## Planned features

- Hourly news digest + trigger on new headlines
- Watchlist with per-ticker signals
- Suggestions with full model reasoning (not auto-executed)
- IBKR paper sync: positions, today P&amp;L, total P&amp;L per line item
- Web dashboard (activity feed, portfolio, digests)

## Stack (planned)

- Python, FastAPI, SQLite, APScheduler
- Ollama (e.g. Finance-Llama-8B)
- IBKR paper via IB Gateway + ib_async (read-only first)

## Mockup

```bash
cd mockup
python3 -m http.server 8765
# http://localhost:8765/dashboard.html
```

## License

Private — personal project.
