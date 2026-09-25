# Architecture

```
Next.js frontend (:3000) ──HTTP /api──▶ FastAPI backend (:8000) ──▶ PostgreSQL
            │                                   │
            └───────WebSocket /ws/alerts────────┤
                                                ├──▶ Finnhub / yfinance (market data)
                                                ├──▶ SMTP (alert emails), Twilio (WhatsApp)
                                                └──  APScheduler: alert checks every 30 s
```

## Backend (`backend/app`)

| Path | Purpose |
|---|---|
| `main.py` | Creates the app. Registers middleware, exception handlers, CORS and routers, and starts and stops the scheduler through the lifespan handler. |
| `config.py` | Settings from environment variables and `.env` (pydantic-settings) |
| `api/routes/` | HTTP and WebSocket endpoints |
| `services/` | Business logic: `trading_service` (paper trading), `alert_service` and `scheduler` (alerts), `email_smtp`, `whatsapp_service`, `indicator_service`, `news_service`, `sentiment_service` |
| `models/` | SQLAlchemy models; the schema itself comes from Alembic (`backend/alembic/versions`) |
| `schemas/` | Pydantic request and response models |
| `ws/` | WebSocket connection manager and live price streamer |
| `core/` | Security (bcrypt, JWT), logging, exception handlers |

### API

All routers are mounted under `/api`, except WebSocket routes, which are under `/ws`. The full list is at `/docs`.

| Prefix | What it does |
|---|---|
| `/api/auth` | Register, login (form or JSON; email or WhatsApp phone), `me`, change password. Password reset is disabled (returns 501). |
| `/api/trade` | Paper trading: execute trades, close trades, trade history and stats |
| `/api/portfolio` | Holdings, summary (including `buying_power` = cash), allocation, growth. `POST` buys and `DELETE` sells through the trading engine. |
| `/api/alerts` | Alert CRUD |
| `/api/stocks`, `/api/stock` | Quotes, market summary, history. `/stocks/{symbol}/price` is the quote source used for trading. |
| `/api/indicators`, `/api/news`, `/api/sentiment`, `/api/search`, `/api/watchlist` | Market data features |
| `/api/dashboard`, `/api/user`, `/api/support`, `/api/health` | Dashboard sections, profile and settings, support tickets, health checks |
| `/ws/stocks/{symbol}`, `/ws/alerts`, `/ws/status` | Live prices, alert notifications, connection stats |

Authentication uses a Bearer JWT (`sub` = user email, 30-minute expiry by default).

### Paper trading (`services/trading_service.py`)

This module is the only code that changes trades, positions or cash.

- **Execution price** always comes from the server's market quote: Finnhub first, then yfinance. A price sent by the client is ignored. If no real price is available the trade is refused with 503; the service never falls back to a made-up or zero price.
- **Lots are the source of truth.** An open `BUY` or `SHORT` trade is a lot. After every change, the `portfolios` row for the symbol is recalculated from the open lots: net quantity (negative means short) and the weighted average entry price.
- **Trade types:**
  - `BUY`: opens a long lot and pays quantity × price from cash.
  - `SELL`: closes long lots oldest-first (FIFO) and credits the proceeds.
  - `SHORT`: opens a short lot and reserves quantity × price of cash as collateral, so there is no leverage.
  - `CLOSE`: closes every open lot in the symbol.
  - `POST /trade/{id}/close`: closes one lot.
  - Buying while short, or shorting while long, is rejected.
- **History:** each closed lot, or part of a lot, writes one `trade_history` row with its realised profit/loss.
- **Cash:** `users.cash_balance` starts at `PAPER_TRADING_STARTING_CASH`. Trades that need more cash than is available are rejected.
- **Precision:** quantities are `NUMERIC(20,8)`, prices `NUMERIC(18,6)`, cash and P/L `NUMERIC(18,2)` (rounded half-up to cents). All calculations use `Decimal`.
- **Consistency:** each trade runs in a single transaction that first locks the user's row (`SELECT … FOR UPDATE`). Concurrent trades by one user therefore run one after another, and a failure rolls back everything.

### Alerts

- **Scheduling:** `services/scheduler.py` starts an APScheduler `BackgroundScheduler` in the app process. It runs `check_all_alerts` every 30 seconds, with at most one run at a time.
- **Checking:** `services/alert_service.py` groups active alerts by symbol, pulls recent yfinance data and evaluates each alert type (price, percent change, volume spike, crash, SMA/EMA/RSI variants and combined signals).
- **On trigger:** an `alert_history` row is written, the alert is marked triggered and inactive, an email is sent through `email_smtp` (synchronous SMTP with STARTTLS), and a WhatsApp message is sent through Twilio if enabled and the user has a phone number set.

### Logging

`core/logging_config.py` writes to the console and to `backend/logs/{app,errors,access}.log`. A request-logging middleware in `core/error_handlers.py` logs every request.

## Frontend (`frontend/`)

| Path | Purpose |
|---|---|
| `app/` | Next.js App Router pages: dashboard, portfolio, watchlist, alerts, news, stocks/[symbol], trade-history, settings, profile, support, login/register |
| `components/sentinel/` | App shell (navigation, Quick Trade, search, alert bell), charts, shared UI |
| `components/providers/data-sync-provider.tsx` | Polls `/dashboard/market` and `/dashboard/ribbon` every 5 s through `hooks/useSafePolling.ts` |
| `lib/api-client.ts`, `lib/api-service.ts` | Axios instance (Bearer token from `localStorage`, redirect to `/login` on 401) and typed API calls |
| `lib/ws-manager.ts`, `hooks/useAlertsWS.ts` | `/ws/alerts` connection with reconnect and backoff |
| `lib/store.ts`, `lib/store-v2.ts` | Zustand stores (see known issues) |

## Known issues

These are tracked for later work and are not solved yet:

- CORS allows only `http://localhost:3000` and `http://127.0.0.1:3000`; `BACKEND_CORS_ORIGINS` is ignored.
- `/ws/alerts` has no authentication and broadcasts to every client. Alert broadcasts from the scheduler thread also fail, because that thread has no event loop.
- A triggered alert is set inactive, so it fires once until it is re-enabled. The cooldown settings have no effect.
- The global poller writes to `lib/store.ts`, but several pages read `lib/store-v2.ts`.
- `frontend/.env.production` and `.env.staging` use variable names the code doesn't read.
- The scheduler and caches live in the process, so running more than one backend process duplicates alert checks.
- The models and migrations differ outside the trading tables; `alembic check` is not clean.
- `POST /api/portfolio` checks the symbol with Finnhub search. Without `FINNHUB_API_KEY` that search returns nothing, so every buy through that endpoint is rejected.
