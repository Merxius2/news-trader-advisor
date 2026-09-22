# News Trader Advisor — Project Handoff & Phase Plan

Handoff document for the agent building this application. Covers goals, architecture, phases, and constraints from planning discussions.

## 1. Project overview

News Trader Advisor is a local tool for a mini-PC that:

- Ingests financial news (hourly batch + on new headlines)
- Analyzes headlines with Ollama (local LLM)
- Produces trading suggestions with full reasoning — not auto-executed in v1
- Connects to an IBKR paper account for positions and P&L (no real money)
- Shows everything on a web dashboard — activity, watchlist, suggestions, reasoning, P&L

**Explicit non-goals for early phases:**

- No live trading
- No automatic order execution until explicitly added later
- Not financial advice — research/advisory tool only

## 2. Core user stories

| As a user, I want to… | So that… |
|---|---|
| See news analyzed every hour and when new headlines arrive | I don't miss market-moving events |
| See why the model suggests buy/sell/hold | I can judge the reasoning myself |
| Manage a watchlist of tickers | Analysis focuses on stocks I care about |
| See today's P&L and total P&L on paper | I know if suggestions would have worked |
| See P&L per position linked to the suggestion that opened it | I connect news → decision → outcome |
| Watch a live activity feed | I trust the system is running |
| Start on IBKR paper only | I can experiment without risk |

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MINI-PC                               │
├─────────────────────────────────────────────────────────────┤
│  News sources (RSS, Finnhub, etc.)                          │
│       ↓ hourly + poll every 3–5 min                         │
│  Ingest + dedupe → SQLite                                   │
│       ↓                                                      │
│  Ticker mapping (watchlist)                                 │
│       ↓                                                      │
│  Ollama (Finance-Llama-8B or Qwen2.5) → structured JSON     │
│       ↓                                                      │
│  Rules engine (confidence thresholds, conflict detection)   │
│       ↓                                                      │
│  FastAPI backend + Web dashboard                            │
│       ↕ sync every 30–60s (read-only first)                 │
│  IB Gateway (paper) ← ib_async                              │
└─────────────────────────────────────────────────────────────┘
```

**Stack (planned):**

- Python 3.11+, FastAPI, SQLite, APScheduler
- Ollama — e.g. `martain7r/finance-llama-8b:q4_k_m` or `qwen2.5:7b` for JSON
- IBKR paper — IB Gateway (port ~4002) + ib_async
- Frontend — simple web UI (HTML + HTMX or lightweight JS); dark theme

## 4. News ingestion

### Two modes (both required)

| Mode | Schedule | Behavior |
|---|---|---|
| Hourly batch | Every hour at :00 | Fetch all sources since last run, dedupe, analyze new items, write hourly digest |
| Event-driven | Poll every 3–5 min | Lightweight poll; new headline → immediate analysis → activity feed update |

### Sources (start small)

| Source | Type | Notes |
|---|---|---|
| Reuters Business RSS | RSS | Free |
| Yahoo Finance RSS | RSS | Free |
| SEC EDGAR press RSS | RSS | Free |
| Finnhub company news | REST API | Free tier; needs `FINNHUB_API_KEY` |

### Deduplication

- Primary key: normalized URL
- Fallback: hash of (title + published_date + source)
- Cluster near-duplicates (same ticker + event within 30–60 min) → analyze once

## 5. Ollama analysis

### Model options

| Model | Use case |
|---|---|
| Finance-Llama-8B (`martain7r/finance-llama-8b:q4_k_m`) | Finance reasoning, sentiment, QA |
| Qwen2.5:7b | Alternative; often better at strict JSON |

**Important:** Finance LLMs do not have live market data. The app must supply news text, watchlist, and (later) price context from IBKR or public APIs.

### Required JSON output schema (per article)

```json
{
  "headline_id": "abc123",
  "tickers": ["NVDA"],
  "event_type": "earnings_guidance | m_and_a | regulation | macro | product | other",
  "sentiment": "bullish | bearish | neutral | mixed",
  "time_horizon": "intraday | days | weeks",
  "suggested_action": "would_buy | would_sell | would_reduce | would_hold | no_action",
  "confidence": 0.72,
  "rationale": "Plain-language explanation tied to the news...",
  "risk_factors": ["Already priced in", "Low detail in article"],
  "would_do": {
    "instrument": "NVDA",
    "direction": "long",
    "notional_hint": "small | medium | large",
    "entry_logic": "Wait for dip / market open / no entry yet",
    "exit_logic": "Take profit if +X% or if sentiment reverses"
  },
  "disclaimer": "Advisory only — not executed"
}
```

Validate with Pydantic; retry once on parse failure.

### Rules engine (code, not LLM)

- `confidence < 0.6` → log only, no alert
- `no_action` → store but hide from alerts
- Conflicting signals on same ticker within 1 hour → flag "mixed signals"
- Never suggest tickers not in article + watchlist mapping (reduce hallucinations)

## 6. IBKR paper account

### Setup

- Enable IBKR Paper Trading
- Run IB Gateway (paper) on mini-PC — port typically 4002
- Enable API: socket clients, trusted IP 127.0.0.1
- Connect via ib_async (Python)

### Integration modes (phased)

| Mode | Phase | Description |
|---|---|---|
| Read-only | Phase 2 | Positions, today P&L, total P&L, executions — no orders |
| Manual link | Phase 3 | User tags suggestion ↔ position, or one-click "open on paper" |
| Auto paper orders | Phase 4+ | High-confidence suggestions → paper orders only |
| Live account | Future | Off by default; separate config; never in v1 |

### P&L dashboard requirements

**Summary cards:**

- Today P&L
- Total unrealized (open positions)
- Total realized (all time)
- Net liquidation (paper)

**Per position:**

- Symbol, qty, avg cost, market value
- Today P&L, unrealized P&L
- Linked suggestion (action tag + headline snippet)

## 7. Dashboard (mockup exists)

Static mockup: [`mockup/dashboard.html`](../mockup/dashboard.html) — dark theme, sample data.

### Pages

| Page | Content |
|---|---|
| Dashboard (home) | P&L cards, positions table, latest suggestions, activity feed, watchlist sidebar |
| Portfolio & P&L | Full positions, trade history, cumulative P&L |
| Suggestions | All recommendations with reasoning; filters by ticker, action, confidence, date |
| Article detail | Headline, source, raw text, extracted tickers, model JSON, rationale |
| Watchlist | View/edit tickers, notes, sectors, current signal per ticker |
| Activity log | Full event history |
| Digests | Hourly and daily rollups |
| Settings | Poll interval, model name, confidence thresholds, news sources, IBKR connection |

### UI elements

- Paper account badge (always visible)
- Status panel: IBKR connected, Ollama model, last news poll, next hourly run
- Live activity feed (auto-refresh every few seconds)
- Reasoning block per suggestion (primary user requirement)
- Buttons: "Run news now", "Sync IBKR"

## 8. Database schema (SQLite)

```
articles       — id, url, title, summary, source, published_at, content_hash, fetched_at
analyses       — id, article_id, model, raw_response, parsed_json, created_at
suggestions    — id, analysis_id, ticker, action, confidence, rationale, visible
activity_log   — id, timestamp, level, message (for live feed)
runs           — id, type (hourly|trigger|daily), started_at, finished_at, articles_processed

# Phase 2+
ibkr_snapshots   — time, daily_pnl, total_unrealized, net_liq
ibkr_positions   — symbol, qty, avg_cost, mkt_value, unrealized, daily_pnl, synced_at
ibkr_executions  — fill details for realized P&L
suggestion_trades — links suggestion_id ↔ IBKR order/execution id
```

## 9. Learning over time (future — not v1)

The Ollama model does not learn automatically. Improvement paths:

| Approach | Phase | Notes |
|---|---|---|
| Log everything | Phase 1+ | News, model output, decision, P&L |
| RAG / trade journal | Phase 5+ | Feed past cases into prompts |
| Rule tuning | Phase 4+ | Adjust filters from backtest results |
| Separate ML model | Phase 5+ | XGBoost etc. on features + sentiment score |
| LLM fine-tuning | Optional | High overfitting risk; needs lots of data |

**Recommended:** LLM for language; traditional ML + strict rules for pattern learning.

## 10. Implementation phases

### Phase 0 — Setup

- Python venv, project structure, config (YAML + `.env`)
- Ollama installed + model pulled
- SQLite schema + migrations
- Watchlist config (`config/watchlist.yaml`)

**Deliverable:** `python -m src.main --help` runs; DB initializes.

### Phase 1 — News + suggestions (no IBKR, no execution)

- RSS fetcher + optional Finnhub fetcher
- Dedup + store articles
- Hourly scheduler (APScheduler)
- Ollama client + prompt templates + JSON parser
- Rules engine + suggestion storage
- CLI: `run-once`, `run-daemon`
- Markdown hourly reports (`reports/YYYY-MM-DD_HH.md`)

**Deliverable:** Daemon ingests news hourly; produces structured suggestions with reasoning.

### Phase 2 — Event-driven + basic dashboard

- Poll loop every 3–5 min for new headlines
- Priority queue (breaking > sector > general)
- FastAPI app serving dashboard
- Pages: activity feed, watchlist, suggestions with reasoning
- Auto-refresh activity feed (HTMX or polling)

**Deliverable:** New headline → analysis within ~5 min; visible on dashboard.

### Phase 3 — IBKR paper read-only + P&L

- IB Gateway (paper) connection via ib_async
- Sync job every 30–60s: positions, account summary, today P&L
- Dashboard: P&L summary cards + positions table
- Paper account banner + connection status

**Deliverable:** Dashboard shows live paper P&L; no orders placed.

### Phase 4 — Link suggestions ↔ positions

- Manual tagging: suggestion → paper trade
- Optional one-click "Execute on paper" for a suggestion
- Per-position "linked suggestion" column with reasoning drill-down
- Hourly rollup per ticker (conflict detection)
- Daily summary digest

**Deliverable:** Each position can show why it's held and its P&L.

### Phase 5 — Enrichment + quality

- Public price context in prompts (e.g. yfinance) — "already up 4% today"
- Backtest suggestions vs next-day/week price
- Accuracy scoring ("suggestions that made money")
- Optional Telegram/email alerts for high-confidence watchlist hits
- RAG: similar past cases in prompt

**Deliverable:** Measurable suggestion quality; smarter context.

### Phase 6 — Optional auto paper execution

- High-confidence suggestions → paper orders (configurable thresholds)
- Hard limits: max position size, max orders/day, market hours only
- Full audit log: suggestion id + headline + reasoning + order id
- Virtual portfolio "what if I had followed everything today"

**Deliverable:** Fully automated paper trading pipeline with guardrails.

### Phase 7 — Future (explicit opt-in)

- Live IBKR account (separate config, off by default)
- Human approval step before live orders
- Retrain small classifier on logged outcomes

## 11. Project structure (target)

```
news-trader-advisor/
├── config/
│   ├── watchlist.yaml
│   ├── sources.yaml
│   └── settings.yaml
├── src/
│   ├── main.py
│   ├── scheduler.py
│   ├── ingest/          # rss_fetcher, finnhub_fetcher, deduper
│   ├── enrich/          # ticker_mapper
│   ├── analyze/         # ollama_client, prompts, parser
│   ├── suggest/         # rules_engine, rollup
│   ├── ibkr/            # connector, sync (Phase 3+)
│   ├── output/          # reporter, notifier
│   ├── storage/         # db, models
│   └── web/             # FastAPI routes, templates
├── templates/
├── static/
├── mockup/              # static dashboard mockup (exists)
├── reports/
├── data/                # advisor.db (gitignored)
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 12. Config defaults (suggested)

```yaml
schedule:
  hourly_digest_minute: 0
  news_poll_interval_minutes: 3
  daily_summary_hour: 18

ollama:
  base_url: http://127.0.0.1:11434
  model: martain7r/finance-llama-8b:q4_k_m
  fallback_model: qwen2.5:7b
  temperature: 0.2
  timeout_seconds: 120

suggestions:
  min_confidence_for_digest: 0.5
  min_confidence_for_highlight: 0.75
  max_articles_per_run: 30

ibkr:
  mode: paper          # paper | live (live disabled in v1)
  host: 127.0.0.1
  port: 4002           # paper gateway
  client_id: 1
  readonly: true       # Phase 3; false only when executing

server:
  host: 0.0.0.0
  port: 8080
```

## 13. Guardrails & compliance

- Every suggestion output: "Suggestion only — not financial advice — not executed"
- Paper banner always visible on dashboard
- Separate config for paper vs live; live credentials never in same config as paper
- Validate JSON; never trust raw LLM output for execution without rules pass
- Rate-limit news API calls; respect ToS
- Log raw headlines + model output for audit
- Max position / max orders per day even on paper
- Start with months of paper before any live consideration

## 14. Hardware notes (mini-PC)

- Finance-Llama-8B Q4: ~6–8 GB RAM for model + OS headroom
- Batch size: prefer one headline per Ollama call for JSON reliability; cap ~30 articles/hour
- IB Gateway: allocate 4096 MB+ Java heap if loading bulk data

## 15. Existing assets

| Asset | Location | Status |
|---|---|---|
| Dashboard mockup | `mockup/dashboard.html` | Done — static HTML, sample data |
| Mockup README | `mockup/README.md` | Done |
| Backend / API / scheduler | — | Not started |
| IBKR integration | — | Not started |

**Mockup preview:**

```bash
cd mockup && python3 -m http.server 8765
# http://localhost:8765/dashboard.html
```

## 16. Success criteria (v1 complete)

- [ ] Daemon runs 24/7 without crashing
- [ ] New articles detected within 5 min or at next hourly run
- [ ] Each article produces valid structured JSON
- [ ] Dashboard shows suggestions with full reasoning
- [ ] IBKR paper P&L syncs (today + total + per position)
- [ ] Zero live trading; paper only
- [ ] User can review a week of logs and judge usefulness

## 17. Open decisions for product owner

- **Initial watchlist** — which tickers (suggested starter: AAPL, MSFT, NVDA, ASML, AMZN)
- **News sources** — RSS-only first or Finnhub from day one?
- **Execution v1** — read-only P&L only, or one-click paper trade from suggestion?
- **Markets** — US only or also EU listings?
- **Alerts** — dashboard only, or Telegram/email?
- **Language** — English-only news or Dutch/EU sources too?

## 18. Recommended build order for the agent

1. **Phase 0 + 1** — backend, news ingest, Ollama, SQLite, CLI reports
2. **Phase 2** — FastAPI dashboard (match mockup layout); activity + suggestions + watchlist
3. **Phase 3** — IBKR paper read-only; P&L cards + positions table
4. **Phase 4** — link suggestions to positions; digests
5. **Phase 5+** — enrichment, alerts, optional auto paper execution

**Do not skip:** structured JSON schema, rules engine, paper-only guardrails, and reasoning visibility on every suggestion.

---

This document reflects the full planning conversation. The mockup is the visual target for Phase 2–3 dashboard work.
