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
| `services/` | Business logic: `trading_service` (paper trading), `alerts/` (alert evaluation), `alert_service` (alert CRUD) and `scheduler`, `email_smtp`, `whatsapp_service`, `indicator_service`, `news_service`, `sentiment_service` |
| `models/` | SQLAlchemy models; the schema itself comes from Alembic (`backend/alembic/versions`) |
| `schemas/` | Pydantic request and response models |
| `ws/` | WebSocket connection manager and live price streamer |
| `core/` | Security (bcrypt, JWT), logging, exception handlers, `event_loop` (thread-to-event-loop bridge) |

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

### Alerts (`services/alerts/`)

- **Scheduling:** `services/scheduler.py` runs `check_all_alerts` in an APScheduler background thread every 30 seconds, at most one run at a time. `check_all_alerts` calls `alerts.alert_runner.run_alert_checks`, the single entry point. On shutdown the lifespan waits for a run in progress to finish.
- **Types and parameters:** each type has exactly the parameters it needs. The API schema (`schemas/alert.py`) and the database CHECK constraint `ck_alerts_type_parameters` enforce the same rules.

  | Type | Parameters | Fires when |
  |---|---|---|
  | `price`, `custom` | `condition` (`>`, `<`, `>=`, `<=`), `target_value` | the price compared with the target meets the condition |
  | `percentage_change` | `target_value` (%) | the price has moved ≥ N% either way from the reference price |
  | `crash` | `target_value` (%) | the price has dropped ≥ N% from the reference price |
  | `volume_spike` | `target_value` (multiple) | the latest volume is above N × the 20-day average |
  | `sma_above` / `sma_below` / `sma_crossover` | `sma_period` | the price is above / below the SMA, or crossed it since the last check |
  | `ema_above` / `ema_below` / `ema_crossover` | `ema_period` | the same, for the EMA |
  | `rsi_overbought` / `rsi_oversold` / `rsi_crossover` | `rsi_period` | RSI > 70 / < 30, or it crossed 30 or 70 since the last check |
  | `strong_buy_signal` / `strong_sell_signal` | all three periods | price > (<) SMA and EMA, and RSI < 30 (> 70) |

  The reference price for percent and crash alerts is the price recorded on the alert's first check after it is created or re-enabled.
- **Market data (`market_data.py`):** each symbol gets **one** yfinance daily-history request per run, however many alerts it has. The lookback is sized to the most demanding alert on that symbol: at least 21 bars, the SMA period + 1, and 3× the EMA or RSI period so they converge. For example, SMA-200 fetches about 300 calendar days. A missing, zero or NaN price skips that symbol for the run; no substitute price is ever used. If there isn't enough history for a period, the alert is skipped with a logged reason, never a signal.
- **Checkers:** `price_checker`, `custom_checker`, `percentage_checker`, `crash_checker`, `volume_checker` and `indicator_checker` are pure functions of `(alert, snapshot)`. `indicators.py` holds the SMA, EMA and RSI math, with the same formulas as `indicator_service`.
- **Lifecycle (one-shot):** when an alert fires it is deactivated (`is_active=false`, `is_triggered=true`), an `alert_history` row is written, and notifications are sent once. Re-enabling it (`PATCH /api/alerts/{id}` with `{"is_active": true}`) re-arms it and clears the recorded reference values. The trigger is claimed with a conditional UPDATE, so overlapping runs cannot fire it twice.
- **Notifications (`notifier.py`):** email goes through `email_smtp`, and WhatsApp through Twilio if enabled and the user has a phone number. A failed notification is logged and never undoes the trigger or stops the run; `alert_history.email_sent` records whether the email was delivered. Logs mask email addresses and phone numbers. WebSocket push is implemented through `core/event_loop.py`, but it is switched **off** (`BROADCAST_ALERTS_OVER_WEBSOCKET`) until `/ws/alerts` is authenticated.
- **Error isolation:** each alert runs in its own transaction. An exception is logged with the alert ID, symbol, type and error category, and the run continues with the next alert. A failed symbol fetch skips only that symbol.

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
- `/ws/alerts` has no authentication and would broadcast to every client, so alert push over WebSocket is switched off for now (email and WhatsApp work).
- The global poller writes to `lib/store.ts`, but several pages read `lib/store-v2.ts`.
- The scheduler and caches live in the process, so running more than one backend process duplicates alert checks.
- The models and migrations differ outside the trading and alert tables; `alembic check` is not clean.
- `/api/indicators` (the indicator endpoints, separate from alerts) still fetches only 1–3 months of history, so SMA-50 and longer fail there.
- `POST /api/portfolio` checks the symbol with Finnhub search. Without `FINNHUB_API_KEY` that search returns nothing, so every buy through that endpoint is rejected.
