# Agent entry point

Cursor loads this file automatically. **Follow `.instructions` and load `docs/repo-map.json` at the start of every session.**

## Required bootstrap

1. Read [`.instructions`](.instructions) — workflow, token-saving rules, repo map maintenance.
2. Read [`docs/repo-map.json`](docs/repo-map.json) — symbol index, API routes, DB models, pydantic schemas, UI map, phases. Use `symbol_index` to find classes/functions without scanning the codebase.
3. When implementing, read the relevant sections of [`docs/PLAN.md`](docs/PLAN.md) (see `topic_index` in the repo map).

## Project summary

Local news-driven trading **advisor** (mini-PC): Ollama analyzes headlines → structured suggestions with reasoning → IBKR **paper** P&L on a web dashboard. No live trading in v1.

**Current status:** planning / mockup only. **Next build:** Phase 0 (project setup).

## Quick links

- Plan: [`docs/PLAN.md`](docs/PLAN.md)
- Repo map: [`docs/repo-map.json`](docs/repo-map.json)
- Mini-PC setup & sync: [`docs/mini-pc.md`](docs/mini-pc.md)
- Dashboard mockup: [`mockup/dashboard.html`](mockup/dashboard.html)

## Mini-PC (runtime target)

After changes land on **`main`**, pull on the mini-PC or run `./scripts/sync-mini-pc.sh`. See [`.instructions`](.instructions) § Mini-PC deployment.
