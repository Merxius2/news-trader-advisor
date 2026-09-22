# Crypto News Advisor (Bitvavo fork) — Project Handoff & Phase Plan

Handoff document for the **Bitvavo / crypto** variant of News Trader Advisor. This fork replaces stock news + IBKR with **crypto news + Bitvavo API**.

Use this document as a **reusable fork template**: the shared pipeline (ingest → dedupe → LLM → rules → dashboard → broker sync) stays the same; only the fork-specific blocks in [§ Fork profile](#0-fork-profile-reusable-template) change when you spin up the IBKR stock fork again.

**Parent reference:** [`docs/PLAN.md`](PLAN.md) (IBKR / stocks — original plan)

---

## 0. Fork profile (reusable template)

When creating another fork (e.g. IBKR stocks), copy this table and fill in fork-specific values. Everything else in this document follows the same phase structure.

| Dimension | **This fork (Bitvavo / crypto)** | IBKR fork (reference) |
|---|---|---|
| **Codename** | `crypto-advisor-bitvavo` | `news-trader-advisor` |
| **Asset class** | Crypto (spot on Bitvavo) | US/EU equities |
| **Watchlist unit** | Market pair (`BTC-EUR`, `ETH-EUR`) | Stock ticker (`NVDA`, `ASML`) |
| **News domain** | Crypto / DeFi / regulation / macro | Corporate / earnings / M&A / macro |
| **Broker API** | Bitvavo REST + WebSocket | IBKR via IB Gateway + ib_async |
| **Paper trading** | No REST sandbox — read-only key + virtual portfolio | IBKR paper account (port 4002) |
| **Quote currency** | EUR (Bitvavo default) | USD / multi-currency |
| **Market hours** | 24/7 | Exchange session hours |
| **LLM focus** | Crypto-native prompts & event taxonomy | Finance-equity prompts |
| **Connector package** | `src/bitvavo/` | `src/ibkr/` |
| **Sync tables** | `bitvavo_balances`, `bitvavo_trades`, `trader_*` sub-ledger | `ibkr_positions`, `ibkr_executions`, … |
| **Capital model** | Small **trader allocation** on shared account; sub-ledger P&L | Small allocation / sub-account on paper |
| **Dashboard badge** | "Trader allocation — read-only" | "Paper account — no real money" |

### Shared pipeline (identical across forks)

```
News sources → ingest + dedupe → SQLite articles
      ↓
Watchlist mapping (pairs or tickers)
      ↓
Ollama → structured JSON (fork-specific schema + prompts)
      ↓
Rules engine (confidence, conflicts, watchlist guard)
      ↓
FastAPI dashboard + activity feed
      ↕
Broker connector (read-only first) → positions/balances + P&L
```

### Fork-specific files (swap per variant)

| File / area | Bitvavo fork | IBKR fork |
|---|---|---|
| Plan doc | `docs/PLAN-bitvavo.md` | `docs/PLAN.md` |
| Watchlist config | `config/watchlist.yaml` (markets) | `config/watchlist.yaml` (tickers) |
| News sources | `config/sources.yaml` → crypto RSS/APIs | `config/sources.yaml` → equity RSS/Finnhub |
| System prompt | `src/analyze/prompts_crypto.py` | `src/analyze/prompts.py` |
| Broker connector | `src/bitvavo/connector.py`, `sync.py` | `src/ibkr/connector.py`, `sync.py` |
| Env vars | `BITVAVO_API_KEY`, `BITVAVO_API_SECRET` | IB Gateway host/port |

---

## 1. Project overview

Crypto News Advisor is a local tool for a mini-PC that:

- Ingests **crypto news** (hourly batch + poll on new headlines)
- Analyzes headlines with Ollama using **crypto-focused prompts**
- Produces spot-trading suggestions (`BTC-EUR`, `ETH-EUR`, …) with full reasoning — **not auto-executed in v1**
- Connects to **Bitvavo read-only API** for account balances and trade history
- Operates on a **small trader allocation** (EUR budget) while the rest of the Bitvavo account stays for manual holdings
- Maintains a **trader sub-ledger** — tracks only bot-attributed transactions and P&L, separate from manual wins/losses on the same account
- Shows everything on a web dashboard — activity, watchlist, suggestions, reasoning, **trader P&L vs account P&L**

**Explicit non-goals for early phases:**

- No automatic order placement until Phase 6 (and only with explicit opt-in)
- No withdrawal permission on API keys — ever
- Not financial advice — research/advisory tool only
- No on-chain wallet tracking in v1 (exchange balances only)

**Bitvavo-specific constraint:** Bitvavo REST/WebSocket has **no paper-trading sandbox**. Early phases use a **read-only API key** plus an optional **virtual portfolio** (track "what if I had followed suggestions" without placing orders).

---

## 2. Core user stories

| As a user, I want to… | So that… |
|---|---|
| See crypto news analyzed every hour and when new headlines arrive | I don't miss market-moving events (hacks, ETF flows, regulation) |
| See why the model suggests buy/sell/hold on a **market pair** | I can judge crypto-specific reasoning myself |
| Manage a watchlist of Bitvavo markets | Analysis focuses on coins I hold or watch |
| Cap the trader at a small EUR allocation (e.g. €500) | Most of my Bitvavo balance stays untouched for manual trades |
| See **trader P&L** (bot trades only) separately from **account P&L** (everything on Bitvavo) | I know if the advisor is winning without mixing in my manual buys |
| See each trader position linked to the suggestion that opened it | I connect news → decision → outcome |
| See when manual activity on the same asset affects account totals but not trader attribution | Deposits, manual buys, and airdrops don't corrupt bot performance stats |
| Watch a live activity feed | I trust the system is running 24/7 |
| Start with read-only Bitvavo access | Real balances visible but no accidental trades |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MINI-PC                               │
├─────────────────────────────────────────────────────────────┤
│  Crypto news (RSS, CryptoCompare, CoinGecko, …)             │
│       ↓ hourly + poll every 3–5 min                         │
│  Ingest + dedupe → SQLite                                   │
│       ↓                                                      │
│  Market mapping (watchlist: BTC-EUR, ETH-EUR, …)            │
│       ↓                                                      │
│  Ollama (crypto-tuned prompt) → structured JSON             │
│       ↓                                                      │
│  Rules engine (confidence, 24h conflict detection)          │
│       ↓                                                      │
│  FastAPI backend + Web dashboard                            │
│       ↕ sync every 30–60s (read-only)                       │
│  Trader sub-ledger (allocation, tagged fills, trader P&L)   │
│       ↕                                                      │
│  Bitvavo REST API ← python-bitvavo-api or httpx client      │
└─────────────────────────────────────────────────────────────┘
```

**Stack:**

- Python 3.11+, FastAPI, SQLite, APScheduler
- Ollama — `qwen2.5:7b` (strict JSON) primary; `martain7r/finance-llama-8b:q4_k_m` fallback
- Bitvavo — REST `https://api.bitvavo.com/v2` + optional WebSocket for ticker streams
- Official SDK: [python-bitvavo-api](https://github.com/bitvavo/python-bitvavo-api) (or thin httpx wrapper)
- Frontend — HTML + HTMX; dark theme (reuse mockup layout, relabel for crypto)

---

## 4. Crypto news ingestion

### Two modes (both required)

| Mode | Schedule | Behavior |
|---|---|---|
| Hourly batch | Every hour at :00 | Fetch all sources since last run, dedupe, analyze new items, write hourly digest |
| Event-driven | Poll every 3–5 min | Lightweight poll; new headline → immediate analysis → activity feed update |

### Sources (start small)

| Source | Type | Notes |
|---|---|---|
| CoinDesk RSS | RSS | Free; broad crypto news |
| Cointelegraph RSS | RSS | Free |
| The Block RSS | RSS | Free tier / RSS |
| Decrypt RSS | RSS | Free |
| Bitcoin Magazine RSS | RSS | Free |
| CryptoCompare News API | REST | Free tier; needs `CRYPTOCOMPARE_API_KEY` |
| CoinGecko status / blog RSS | RSS | Optional; listings & macro |

**Later (Phase 5+):** Twitter/X lists, Fear & Greed index, funding rates (if added), Dutch/EU regulation feeds (AFM, ESMA summaries).

### Deduplication

- Primary key: normalized URL
- Fallback: hash of (title + published_date + source)
- Cluster near-duplicates (same **base asset** + event type within 30–60 min) → analyze once
- Map headline → **base asset** (`BTC`, `ETH`, `SOL`) then → Bitvavo market (`BTC-EUR`) if listed

### Priority queue (event-driven)

| Priority | Event types |
|---|---|
| Breaking | `hack`, `exchange_outage`, `stablecoin_depeg`, `major_regulation` |
| High | `etf_flow`, `listing`, `protocol_upgrade`, `whale_move` |
| Normal | `macro`, `adoption`, `analysis`, `other` |

Crypto markets move 24/7 — no "market open" delay in rules engine.

---

## 5. Ollama analysis (crypto-focused)

### Model options

| Model | Use case |
|---|---|
| Qwen2.5:7b | Primary — reliable structured JSON |
| Finance-Llama-8B | Fallback — decent macro/regulation reasoning |

**Important:** LLMs have no live chain or order-book data. Supply: headline text, watchlist markets, and (Phase 5+) **24h price change** from Bitvavo public ticker or CoinGecko.

### Crypto system prompt (design principles)

The system prompt must instruct the model to:

1. Reason about **spot markets on Bitvavo** (EUR pairs), not perpetuals or leverage unless explicitly mentioned in the article.
2. Identify **base asset** and map only to watchlist markets that exist on Bitvavo.
3. Weigh crypto-specific risks: volatility, liquidity, regulatory jurisdiction (EU/NL), stablecoin exposure, exchange counterparty risk.
4. Avoid hype — distinguish news vs opinion vs rumor; tag `source_quality`.
5. Consider **24/7** time horizon (`minutes | hours | days | weeks`).
6. Never invent wallet addresses, TVL numbers, or prices not in the article unless marked as general context.

Store prompts in `src/analyze/prompts_crypto.py` (fork-specific; IBKR fork uses `prompts.py`).

### Required JSON output schema (per article)

```json
{
  "headline_id": "abc123",
  "base_assets": ["BTC"],
  "markets": ["BTC-EUR"],
  "event_type": "hack | regulation | etf_flow | listing | protocol_upgrade | macro | adoption | exchange | stablecoin | whale_move | legal | other",
  "sentiment": "bullish | bearish | neutral | mixed",
  "time_horizon": "minutes | hours | days | weeks",
  "suggested_action": "would_buy | would_sell | would_reduce | would_hold | no_action",
  "confidence": 0.72,
  "source_quality": "confirmed | reported | opinion | rumor",
  "rationale": "Plain-language explanation tied to the news and crypto market structure...",
  "risk_factors": ["Already priced in", "Thin liquidity on pair", "EU regulatory uncertainty"],
  "would_do": {
    "market": "BTC-EUR",
    "side": "buy | sell",
    "notional_hint": "small | medium | large",
    "entry_logic": "Limit near support / wait for volatility settle / no entry",
    "exit_logic": "Take profit at +X% / stop if regulatory headline confirmed"
  },
  "disclaimer": "Advisory only — not executed — not financial advice"
}
```

Validate with Pydantic (`CryptoAnalysisResult`); retry once on parse failure.

### Rules engine (code, not LLM)

- `confidence < 0.6` → log only, no alert
- `no_action` → store but hide from alerts
- `source_quality == rumor` → cap confidence at 0.5 unless corroborated within 1 hour
- Conflicting signals on same **market** within 1 hour → flag "mixed signals"
- Never suggest markets not in article mapping + watchlist (reduce hallucinations)
- Reject markets not available on Bitvavo (check against cached `/markets` list daily)

---

## 6. Trader allocation & sub-ledger (core product requirement)

The advisor **does not control the full Bitvavo account**. It receives a **fixed EUR allocation** (e.g. €500) to trade within. The user may hold much more on the same account for manual investing. The system must:

1. **Enforce** the allocation cap when placing orders (Phase 6).
2. **Attribute** every bot fill to the trader sub-ledger.
3. **Report** trader wins/losses separately from account-level P&L that includes manual activity.

### Two isolation strategies

| Strategy | When to use | How it works |
|---|---|---|
| **A — Bitvavo subaccount** (preferred) | Corporate / institutional account with subaccounts enabled | Transfer EUR allocation to a dedicated subaccount via `POST /subaccounts/transfers`; bot API key scoped to subaccount only. Exchange-level separation — cleanest P&L. |
| **B — Single account + tagged orders** (default for personal accounts) | Standard Bitvavo account, one balance pool | Bot sets `clientOrderId` prefix `advisor-{suggestion_id}` on every order; app maintains internal **TraderLedger** from tagged fills only. Manual trades have no prefix → excluded from trader P&L. |

Both strategies use the same **TraderLedger** module and dashboard views. Strategy A reduces attribution errors; Strategy B works without subaccounts.

### Trader allocation config

```yaml
trader:
  allocation_eur: 500              # max EUR the bot may deploy (cash + open positions)
  reserve_eur: 50                # keep uninvested as buffer for fees / slippage
  isolation: tagged_orders         # tagged_orders | subaccount
  client_order_id_prefix: advisor  # all bot orders: advisor-{suggestion_id}-{uuid}
  subaccount_id: null              # set when isolation: subaccount
  attribution_start: null          # ISO datetime — ignore pre-existing balances; ledger starts here
```

On first run (Phase 4+), record **opening snapshot**: EUR cash assigned to trader + zero positions. Pre-existing manual holdings on the same assets are **not** part of trader cost basis.

### Sub-ledger rules (TraderLedger)

The sub-ledger is the **source of truth for bot performance**. Implement in `src/bitvavo/trader_ledger.py`.

| Rule | Behavior |
|---|---|
| **Tagged fill → ledger entry** | Every fill whose `clientOrderId` matches prefix → `trader_fills` row linked to `suggestion_id` |
| **Untagged fill → account only** | Sync to `bitvavo_trades` but **never** to trader P&L |
| **Allocation cap** | Before order: `trader_deployed_eur + order_notional ≤ allocation_eur` |
| **Position cost basis** | FIFO (or avg cost) **per market, trader scope only** |
| **Realized P&L** | On sell fill: proceeds − cost basis − fees (trader fills only) |
| **Unrealized P&L** | Mark trader holdings to market; ignore manual holdings in same asset |
| **Manual deposit to same asset** | Account balance ↑, trader allocation unchanged — log as `external_event` |
| **Manual buy of BTC while trader holds BTC** | Account BTC ↑; trader BTC qty unchanged — no P&L impact on trader |
| **Reconciliation drift** | If account sync shows tagged order without ledger entry → backfill; if ledger exceeds allocation → halt trading + alert |

### P&L attribution (three layers)

Always show three layers on dashboard — never conflate them:

```
┌─────────────────────────────────────────────────────────────┐
│  ACCOUNT TOTAL (Bitvavo)                                     │
│  Full balance + all trades — manual + bot                    │
├─────────────────────────────────────────────────────────────┤
│  NON-TRADER (derived)                                        │
│  account_total − trader_portfolio_value − trader_cash        │
│  = manual holdings + untagged activity                       │
├─────────────────────────────────────────────────────────────┤
│  TRADER ALLOCATION (sub-ledger)                              │
│  Realized P&L + unrealized P&L + cash within allocation cap   │
│  Only tagged fills + suggestion links                        │
└─────────────────────────────────────────────────────────────┘
```

**Formulas:**

- `trader_portfolio_eur` = trader cash + Σ(trader_qty × mark_price)
- `trader_realized_pnl` = Σ(sell proceeds − buy cost − fees) for tagged round-trips
- `trader_unrealized_pnl` = trader_portfolio_eur − trader_net_deposits (within allocation)
- `non_trader_eur` = `account_total_eur − trader_portfolio_eur` (informational — not bot performance)

### Order tagging (Strategy B)

Every bot-placed order **must** include:

```json
{
  "clientOrderId": "advisor-sugg-42-a1b2c3d4",
  "operatorId": 1
}
```

Sync job filters: `clientOrderId.startsWith("advisor-")` → trader ledger. WebSocket `account` channel tracks fills with same filter.

### Phase 4 virtual portfolio alignment

The virtual portfolio (pre-execution backtest) uses the **same allocation rules** as live trading — same cap, same ledger schema with `source: virtual | bitvavo`. Lets you compare virtual vs live trader P&L before enabling Phase 6.

### Reusable in IBKR fork

Same pattern applies to stocks: **allocation cap** + **tagged orders** (IBKR `orderRef` field) or **linked IBKR sub-account** + sub-ledger. Swap `clientOrderId` → `orderRef`, `BTC-EUR` → `NVDA`.

---

## 7. Bitvavo integration

### Setup

1. Create Bitvavo account; enable 2FA.
2. Create API key with **Read-only** (+ **Trade** only when reaching Phase 6).
3. **IP whitelist** mini-PC public IP (or VPN exit).
4. Store `BITVAVO_API_KEY` and `BITVAVO_API_SECRET` in `.env` — never commit.
5. **Never** enable Withdraw permission on automated keys.

### API overview

| Need | Endpoint | Auth |
|---|---|---|
| Balances | `GET /balance` | Private |
| Open orders | `GET /orders` | Private |
| Trade history | `GET /trades`, `GET /account/history` | Private |
| Place order | `POST /order` | Private (Phase 6 only) |
| Markets list | `GET /markets` | Public |
| 24h ticker | `GET /ticker/24h` | Public |

Docs: [docs.bitvavo.com](https://docs.bitvavo.com/docs/get-started/)

Rate limit: **1000 weight points / minute** per IP or API key — budget sync jobs accordingly.

### Integration modes (phased)

| Mode | Phase | Description |
|---|---|---|
| Read-only | Phase 3 | Balances, trades, EUR value — no orders |
| Manual link | Phase 4 | User tags suggestion ↔ Bitvavo trade |
| Virtual portfolio | Phase 4 | Track hypothetical fills from suggestions (no API orders) |
| Auto spot orders | Phase 6+ | High-confidence → limit/market on Bitvavo (opt-in, hard limits) |
| Withdrawals | Never | Disabled on API key |

### P&L dashboard requirements

**Trader allocation cards (primary — bot performance):**

- Trader portfolio value (EUR) — within allocation cap
- Allocation used / remaining (e.g. €420 / €500)
- Trader realized P&L (tagged fills only)
- Trader unrealized P&L (trader positions only)
- Trader win rate / trade count (optional Phase 5+)

**Account overview cards (secondary — full Bitvavo account):**

- Account total (EUR) — all holdings including manual
- Non-trader value (derived) — manual portion not attributed to bot
- 24h account change — informational only

**Per trader holding (sub-ledger scope):**

- Market, trader qty, avg cost, EUR value
- Trader unrealized P&L per position
- Linked suggestion (action tag + headline snippet)
- Tag: `advisor-*` or subaccount

**Per account holding (read-only reference):**

- Full Bitvavo balance — may exceed trader qty on same asset
- Badge: "manual" when account qty > trader qty

**Status panel:**

- Bitvavo API connected (last sync time)
- Trader allocation: €X / €Y deployed
- Ollama model name
- Last news poll / next hourly run
- Reconciliation status (OK / drift detected)

---

## 8. Dashboard

Static mockup: [`mockup/dashboard-bitvavo.html`](../mockup/dashboard-bitvavo.html) — dark theme, sample data, trader allocation UI.

| Page | Content |
|---|---|
| Dashboard (home) | **Trader P&L cards**, trader holdings, account total (collapsed), suggestions, activity |
| Trader portfolio | Sub-ledger positions, tagged trade history, realized/unrealized P&L chart |
| Account overview | Full Bitvavo balances (manual + bot), non-trader breakdown |
| Suggestions | Filters by market, action, confidence, event_type, date |
| Article detail | Headline, source, base assets, model JSON, rationale |
| Watchlist | Bitvavo markets (`BTC-EUR`), notes, current signal |
| Activity log | Full event history |
| Digests | Hourly and daily rollups |
| Settings | Poll interval, model, confidence thresholds, news sources, Bitvavo sync interval |

**UI elements:**

- **"Trader allocation €X — not full account"** badge (always visible)
- Clear visual split: trader section vs account-total section
- Buttons: "Run news now", "Sync Bitvavo"
- Reasoning block per suggestion (primary requirement)

---

## 9. Database schema (SQLite)

Shared tables (same as IBKR fork):

```
articles       — id, url, title, summary, source, published_at, content_hash, fetched_at
analyses       — id, article_id, model, raw_response, parsed_json, created_at
suggestions    — id, analysis_id, market, action, confidence, rationale, visible, event_type
activity_log   — id, timestamp, level, message
runs           — id, type (hourly|trigger|daily), started_at, finished_at, articles_processed
```

Bitvavo account sync (Phase 3+):

```
bitvavo_snapshots       — time, account_total_eur, synced_at
bitvavo_balances        — symbol, available, in_order, eur_value, synced_at
bitvavo_trades          — trade_id, market, side, price, amount, fee, timestamp, client_order_id, is_trader_tagged
bitvavo_markets_cache   — market, base, quote, status, updated_at
```

Trader sub-ledger (Phase 4+ — core for allocation tracking):

```
trader_config           — allocation_eur, reserve_eur, isolation_mode, attribution_start, subaccount_id
trader_snapshots        — time, cash_eur, portfolio_eur, realized_pnl, unrealized_pnl, deployed_eur
trader_positions        — market, qty, avg_cost_eur, opened_at, last_sync
trader_fills            — fill_id, order_id, client_order_id, suggestion_id, market, side, qty, price, fee, source (virtual|bitvavo), timestamp
trader_ledger_events    — id, type (fill|deposit|withdraw|reconcile|external), amount_eur, note, timestamp
suggestion_trades       — links suggestion_id ↔ trader_fill_id or bitvavo trade_id
virtual_fills           — id, suggestion_id, market, side, price, amount, simulated_at (same rules as trader_fills)
```

**Key invariant:** `trader_fills` is the only table used for bot P&L. `bitvavo_trades` is the full account mirror for reconciliation.

---

## 10. Learning over time (future — not v1)

| Approach | Phase | Notes |
|---|---|---|
| Log everything | Phase 1+ | News, model output, suggestion, portfolio snapshot |
| RAG / trade journal | Phase 5+ | Similar past crypto events in prompt |
| Rule tuning | Phase 4+ | Adjust filters from backtest vs 24h/7d price |
| Separate ML model | Phase 5+ | Features: sentiment, event_type, vol regime |
| LLM fine-tuning | Optional | High overfitting; crypto narratives shift fast |

**Recommended:** LLM for language; rules + backtest for calibration.

---

## 11. Implementation phases

### Phase 0 — Setup

- Python venv, project structure, config (YAML + `.env`)
- Ollama installed + models pulled
- SQLite schema + migrations (Bitvavo + trader sub-ledger tables stubbed)
- Trader allocation config in `settings.yaml`
- Watchlist config (`config/watchlist.yaml`) with Bitvavo markets
- Crypto news sources config (`config/sources.yaml`)
- `prompts_crypto.py` skeleton

**Deliverable:** `python -m src.main --help` runs; DB initializes; `/markets` cache loads.

### Phase 1 — Crypto news + suggestions (no Bitvavo, no execution)

- Crypto RSS fetcher + optional CryptoCompare fetcher
- Dedup + store articles
- Hourly scheduler (APScheduler)
- Ollama client + **crypto prompts** + JSON parser (`CryptoAnalysisResult`)
- Rules engine + suggestion storage
- CLI: `run-once`, `run-daemon`
- Markdown hourly reports (`reports/YYYY-MM-DD_HH.md`)

**Deliverable:** Daemon ingests crypto news; produces structured suggestions with reasoning.

### Phase 2 — Event-driven + basic dashboard

- Poll loop every 3–5 min for new headlines
- Priority queue (breaking crypto events first)
- FastAPI app serving dashboard
- Pages: activity feed, watchlist (markets), suggestions with reasoning
- Auto-refresh activity feed (HTMX)

**Deliverable:** New headline → analysis within ~5 min; visible on dashboard.

### Phase 3 — Bitvavo read-only + account overview

- Bitvavo REST client (HMAC auth)
- Sync job every 30–60s: full account balances, recent trades (with `clientOrderId`), account total EUR
- Dashboard: account overview cards (informational — not yet trader-attributed)
- Read-only API key enforced in config (`bitvavo.readonly: true`)
- Detect and flag pre-existing tagged vs untagged trades in history

**Deliverable:** Dashboard shows full Bitvavo account; **no orders placed**; trade tagging visible.

### Phase 4 — Trader sub-ledger + suggestion linking

- **TraderLedger** module: allocation cap, opening snapshot, tagged-fill attribution
- Virtual fills use same ledger rules (`source: virtual`)
- Dashboard: **trader P&L cards** separate from account total; non-trader derived row
- Manual tagging fallback: link untagged historical trade → suggestion (one-time import)
- Per-trader-position "linked suggestion" column with reasoning drill-down
- Reconciliation job: ledger vs Bitvavo tagged fills; drift alerts
- Hourly rollup per market (conflict detection)
- Daily summary digest (trader P&L section + account summary section)

**Deliverable:** Trader wins/losses tracked independently of manual activity on same account.

### Phase 5 — Enrichment + quality

- Inject 24h price change from Bitvavo ticker into prompts ("BTC already +6% today")
- Backtest suggestions vs next-24h / 7d price on Bitvavo
- Accuracy scoring per event_type on **trader sub-ledger** (not account total)
- Trader performance report: win rate, avg gain/loss, allocation utilization
- Optional Telegram/email alerts for high-confidence watchlist hits
- RAG: similar past crypto cases in prompt

**Deliverable:** Measurable suggestion quality; smarter context.

### Phase 6 — Optional auto spot execution (explicit opt-in)

- Requires Trade permission on API key (separate key from read-only; subaccount key if Strategy A)
- High-confidence suggestions → limit/market orders on Bitvavo
- **Every order tagged** with `clientOrderId: advisor-{suggestion_id}-{uuid}`
- **Allocation enforced** before submit: refuse if order would exceed `trader.allocation_eur`
- Hard limits: max EUR per order, max orders/day, min confidence, allowed markets only, reserve cash floor
- Fill → immediate `trader_fills` ledger entry + suggestion link
- Full audit log: suggestion id + headline + reasoning + bitvavo order id + ledger entry id
- Kill switch in config and dashboard; halt on reconciliation drift

**Deliverable:** Bot trades only within allocation; P&L attributable; manual account activity excluded.

### Phase 7 — Future

- WebSocket live ticker on dashboard
- Fear & Greed / funding rate context (if expanding beyond spot)
- Multi-exchange read-only (optional)
- On-chain metrics for watchlist assets (Phase 7+)

---

## 12. Project structure (target)

```
crypto-advisor-bitvavo/          # or subfolder of monorepo: forks/bitvavo/
├── config/
│   ├── watchlist.yaml           # markets: BTC-EUR, ETH-EUR, …
│   ├── sources.yaml             # crypto RSS + API keys
│   └── settings.yaml
├── src/
│   ├── main.py
│   ├── scheduler.py
│   ├── ingest/                  # rss_fetcher, cryptocompare_fetcher, deduper
│   ├── enrich/                  # market_mapper (base asset → BTC-EUR)
│   ├── analyze/                 # ollama_client, prompts_crypto.py, parser
│   ├── suggest/                 # rules_engine, rollup
│   ├── bitvavo/                 # connector, sync, trader_ledger, auth (Phase 3+)
│   ├── output/                  # reporter, notifier
│   ├── storage/                 # db, models (CryptoAnalysisResult)
│   └── web/                     # FastAPI routes, templates
├── templates/
├── static/
├── mockup/                      # reuse dashboard layout; crypto labels
├── reports/
├── data/                        # advisor.db (gitignored)
├── tests/
├── requirements.txt
├── .env.example                 # BITVAVO_API_KEY, BITVAVO_API_SECRET, …
└── README.md
```

---

## 13. Config defaults (suggested)

```yaml
schedule:
  hourly_digest_minute: 0
  news_poll_interval_minutes: 3
  daily_summary_hour: 18

ollama:
  base_url: http://127.0.0.1:11434
  model: qwen2.5:7b
  fallback_model: martain7r/finance-llama-8b:q4_k_m
  temperature: 0.2
  timeout_seconds: 120
  prompts_module: crypto          # loads prompts_crypto.py

suggestions:
  min_confidence_for_digest: 0.5
  min_confidence_for_highlight: 0.75
  max_articles_per_run: 30
  rumor_confidence_cap: 0.5

bitvavo:
  rest_url: https://api.bitvavo.com/v2
  ws_url: wss://ws.bitvavo.com/v2/
  readonly: true                  # Phase 3–5; false only in Phase 6 with opt-in
  sync_interval_seconds: 45
  access_window_ms: 10000
  quote_currency: EUR
  # API key/secret from .env — never in YAML

trader:
  allocation_eur: 500             # max EUR bot may deploy
  reserve_eur: 50                 # cash buffer within allocation
  isolation: tagged_orders        # tagged_orders | subaccount
  client_order_id_prefix: advisor
  subaccount_id: null             # UUID when isolation: subaccount
  attribution_start: null         # set on first ledger init (ISO datetime)

virtual_portfolio:
  enabled: true                   # Phase 4+ — uses same TraderLedger rules
  # initial_eur derived from trader.allocation_eur — do not exceed allocation

server:
  host: 0.0.0.0
  port: 8080
```

---

## 14. Guardrails & compliance

- Every suggestion: "Advisory only — not financial advice — not executed"
- **Read-only API key** for Phases 3–5; separate trade key for Phase 6
- **Never** enable Withdraw on API keys used by this app
- IP whitelist on Bitvavo API keys
- Validate JSON; never trust raw LLM output for execution without rules pass
- Rate-limit news and Bitvavo calls; respect ToS
- Log raw headlines + model output for audit
- Max EUR per order / max orders per day even in Phase 6
- **Never exceed trader allocation** — hard block in rules engine + pre-order check
- **Never attribute untagged fills** to trader P&L
- Halt trading on reconciliation drift until user acknowledges
- Crypto volatility disclaimer on dashboard
- MiCA / local regulation: user responsible for tax and compliance — tool is informational only

---

## 15. Hardware notes (mini-PC)

- Qwen2.5:7b or Finance-Llama-8B Q4: ~6–8 GB RAM
- One headline per Ollama call; cap ~30 articles/hour
- Bitvavo sync is lightweight HTTP — no local gateway daemon (simpler than IBKR)

---

## 16. Existing assets to reuse

| Asset | Location | Adapt for Bitvavo fork |
|---|---|---|
| Dashboard mockup | `mockup/dashboard-bitvavo.html` | Trader allocation bar, dual P&L rows, crypto markets |
| Agent workflow | `.instructions`, `docs/repo-map.json` | Add fork entry in repo map |
| Deployment scripts | `scripts/` | Same mini-PC sync flow |
| IBKR plan (reference) | `docs/PLAN.md` | Parallel structure for stock fork |

---

## 17. Success criteria (v1 complete)

- [ ] Daemon runs 24/7 without crashing
- [ ] New crypto articles detected within 5 min or at next hourly run
- [ ] Each article produces valid `CryptoAnalysisResult` JSON
- [ ] Dashboard shows suggestions with full crypto-specific reasoning
- [ ] Bitvavo read-only sync shows full account + trader allocation separately
- [ ] Trader sub-ledger P&L excludes manual trades on same account
- [ ] Allocation cap enforced before any Phase 6 order
- [ ] Zero automatic orders in Phases 0–5
- [ ] User can review a week of trader logs and judge bot performance vs manual holdings

---

## 18. Open decisions for product owner

- **Initial watchlist** — suggested starter: `BTC-EUR`, `ETH-EUR`, `SOL-EUR`, `XRP-EUR`, `ADA-EUR`
- **Trader allocation** — starting EUR budget (suggested: €500); reserve buffer (€50)?
- **Isolation strategy** — subaccount (if corporate) vs tagged orders on personal account?
- **Attribution start** — fund allocation fresh vs import historical tagged trades?
- **News sources** — RSS-only first or CryptoCompare from day one?
- **Execution** — read-only only forever, or Phase 6 auto spot within allocation only?
- **Language** — English-only crypto news or include Dutch sources (Bitvavo is NL-based)?
- **Repo layout** — separate git repo vs `forks/bitvavo/` in monorepo?

---

## 19. Recommended build order for the agent

1. **Phase 0 + 1** — backend, crypto news ingest, Ollama + crypto prompts, SQLite, CLI reports
2. **Phase 2** — FastAPI dashboard (adapt mockup); activity + suggestions + watchlist
3. **Phase 3** — Bitvavo read-only sync; account overview
4. **Phase 4** — **TraderLedger** + trader P&L vs account P&L; virtual fills; digests
5. **Phase 5+** — price enrichment, trader backtest scoring, alerts, optional execution within allocation

**Do not skip:** trader sub-ledger, allocation cap, order tagging, structured JSON schema, crypto-specific prompts, rules engine, and reasoning visibility on every suggestion.

---

## 20. Spinning up the IBKR fork from this template

To reuse this plan for the stock/IBKR variant:

1. Copy `docs/PLAN-bitvavo.md` → keep `docs/PLAN.md` as the IBKR canonical plan (already exists).
2. Swap [§0 Fork profile](#0-fork-profile-reusable-template) column values to IBKR.
3. Replace §4 news sources with equity RSS / Finnhub.
4. Replace §5 schema with equity `AnalysisResult` (tickers, not markets).
5. Replace §7 broker section with IBKR paper / ib_async.
6. Rename `src/bitvavo/` → `src/ibkr/`; keep **TraderLedger** pattern (`orderRef` tagging).
7. Restore paper-trading guardrails (IBKR port 4002).

Both forks share: ingest, dedupe, scheduler, rules engine, **trader allocation + sub-ledger**, dashboard shell, activity feed, phase numbering, and agent workflow.

---

This document is the canonical plan for the **Bitvavo / crypto fork**. The IBKR stock plan remains in [`docs/PLAN.md`](PLAN.md).
