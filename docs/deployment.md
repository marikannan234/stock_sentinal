# Deployment

## Images

| Image | Base | Notes |
|---|---|---|
| `backend/Dockerfile` | `python:3.11-slim` | Starts with `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| `frontend/Dockerfile` | `node:20-alpine`, multi-stage | `NEXT_PUBLIC_API_URL` (required) and `NEXT_PUBLIC_WS_URL` are **build arguments** compiled into the bundle: pass the public API and WebSocket origins (no `/api` or `/ws` path) with `--build-arg`. The build fails if `NEXT_PUBLIC_API_URL` is missing. |

`docker-compose.yml` runs the stack locally: Postgres 15, backend and frontend. Its database password (`password`) is for development only.

## Required production configuration

Set these in the backend environment:

- `ENVIRONMENT=production`. This turns off debug mode and makes a scheduler start-up failure fatal.
- A random `JWT_SECRET_KEY` of at least 32 characters.
- `DATABASE_URL` pointing at the production database.
- Real SMTP credentials (`MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`), managed as secrets. Never commit them.
- `FINNHUB_API_KEY`. Without it, quotes depend on yfinance alone and symbol search returns nothing.
- `PAPER_TRADING_STARTING_CASH`, if the default of `100000.00` is not wanted.

CORS origins are currently hardcoded in `backend/app/main.py`. Change that code, or make it use `BACKEND_CORS_ORIGINS`, before serving the frontend from a different origin.

## Database migrations

1. Back up first, for example `pg_dump -U stocksentinel stocksentinel > backup.sql`.
2. Apply migrations with `alembic upgrade head`. The backend container does this on start.
3. Verify with `alembic current`.
4. Roll back one step with `alembic downgrade -1` if needed.

Migration `0006_trading_cash_numeric` does four things:

1. Adds `users.cash_balance` and sets every existing user to `PAPER_TRADING_STARTING_CASH`.
2. Converts trading and portfolio money columns to `NUMERIC`.
3. Reconciles old data:
   - Trades that were still OPEN are marked CANCELLED; before this release they never affected holdings.
   - Each existing holding becomes one open lot at its average price.
4. Leaves this reconciliation in place on downgrade; it is not reversed.

Set `PAPER_TRADING_STARTING_CASH` in the environment **before** running `0006` if you want a different backfill amount.

Migration `0007_alert_type_parameters` makes `alerts.target_value` nullable (indicator alerts have no target) and adds the CHECK constraint `ck_alerts_type_parameters`. Before adding it, the migration deletes any existing alert that lacks the parameters its type requires, such as a `custom` alert without a condition, and prints how many it removed. Those alerts could never be evaluated. Downgrading sets missing targets to 0 and deletes nothing.

## Reverse proxy

Proxy `/api` as normal HTTP. `/ws` needs WebSocket upgrade headers, for example with nginx:

```nginx
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Scaling

Run **one** backend process for now. The alert scheduler, quote caches and WebSocket connections live inside the process, so more replicas or `--workers` would run duplicate alert checks and send duplicate emails.
