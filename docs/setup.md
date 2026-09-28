# Development setup

## Requirements

- Python 3.11 or newer. The Docker image uses 3.11.
- Node.js 20
- PostgreSQL 15 or newer, or Docker

## Environment variables

### Backend (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`. Settings are read in `backend/app/config.py`. Values from the process environment override `.env`. The `.env` path is relative to the working directory, so run `uvicorn` and `alembic` from `backend/`.

Required: the app will not start without these.

| Variable | Notes |
|---|---|
| `JWT_SECRET_KEY` | At least 32 characters |
| `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM` | SMTP credentials. For Gmail, `MAIL_PASSWORD` must be an [App Password](https://myaccount.google.com/apppasswords), which requires 2FA. |

Optional:

| Variable | Default |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel` |
| `ENVIRONMENT` | `local` (`local`, `staging` or `production`) |
| `DEBUG` | `true` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `FINNHUB_API_KEY` | none. Used for quotes and symbol search. Without it, prices fall back to yfinance, symbol search returns no results, and so buys from the Portfolio page and Quick Trade are rejected as unknown symbols (`POST /api/trade/` still works). |
| `PAPER_TRADING_STARTING_CASH` | `100000.00`: the cash each new account starts with |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_STARTTLS` | `smtp.gmail.com`, `587`, `true` |
| `ENABLE_EMAIL_NOTIFICATIONS` | `true` |
| `ENABLE_WHATSAPP_NOTIFICATIONS` | `false`. If `true`, also set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_WHATSAPP_NUMBER`. |
| `ALERT_COOLDOWN_MINUTES`, `ALERT_DEV_MODE`, `ALERT_LOG_COOLDOWN_CHECKS` | Deprecated; ignored. Alerts are one-shot, see [architecture](architecture.md#alerts-servicesalerts). |

`BACKEND_CORS_ORIGINS` is parsed but not used yet. CORS origins are hardcoded in `app/main.py`; see [architecture](architecture.md#known-issues).

### Frontend

The frontend reads only two variables. `frontend/.env.local` sets both for local development.

| Variable | Default |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` (the client calls `${NEXT_PUBLIC_API_URL}/api`) |
| `NEXT_PUBLIC_WS_URL` | derived from the API URL (`ws://…/ws/alerts`) |

`NEXT_PUBLIC_*` values are baked in at build time, so rebuild after changing them.

## Option A: everything in Docker

```bash
cp backend/.env.example backend/.env   # edit it
docker compose up --build
```

- **Services:** `db`, `backend` and `frontend`. The containers are named `stocksentinel-db`, `stocksentinel-backend` and `stocksentinel-frontend`.
- **Data:** Postgres data lives in the named volume `postgres_data`.
- **Database URL:** compose overrides `DATABASE_URL` to use the `db` host.

## Option B: database in Docker, app running locally

```bash
docker compose up -d db

cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head               # required: the app never creates tables itself
uvicorn app.main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```

To use a native PostgreSQL install instead of Docker, create the role and database with `backend/setup_postgres.sql`. It creates user `stocksentinel` with password `password` and database `stocksentinel`, which matches the default `DATABASE_URL`.

## Database migrations

Alembic owns the schema. Never call `Base.metadata.create_all()` in the app.

```bash
cd backend
alembic upgrade head                            # apply all migrations
alembic current                                 # show the applied revision
alembic history                                 # list revisions
alembic revision --autogenerate -m "describe"   # create a migration, then review it by hand
alembic downgrade -1                            # roll back one revision
```

In Docker, run them in the backend container, for example `docker exec stocksentinel-backend alembic current`.

The chain is `0001` → … → `0006_trading_cash_numeric` → `0007_alert_type_parameters`.

`alembic check` currently reports differences between the models and the migrations, mainly in the unused `stocks` and `stock_predictions` tables and in enum/varchar types. A dedicated alignment migration is still to do.

## Tests

```bash
cd backend
python -m pytest -q
```

By default the tests use in-memory SQLite and set their own environment variables, so no database or `.env` is needed.

To run the same tests against real PostgreSQL, point `TEST_DATABASE_URL` at a throwaway database. The tests wipe it and rebuild it with `alembic upgrade head`. This also runs the concurrency tests that SQLite skips.

```bash
createdb stocksentinel_test
TEST_DATABASE_URL=postgresql+psycopg2://localhost/stocksentinel_test python -m pytest -q
```

Frontend checks:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Backend exits at startup with a validation error | A required variable is missing: `JWT_SECRET_KEY` (at least 32 characters), `MAIL_USERNAME`, `MAIL_PASSWORD` or `MAIL_FROM`. |
| `relation "..." does not exist` | Migrations have not run. Run `alembic upgrade head`. |
| `password authentication failed for user "stocksentinel"` | The role or password doesn't match `DATABASE_URL`. See `backend/setup_postgres.sql`. |
| Database not reachable in Docker | `docker exec stocksentinel-db pg_isready -U stocksentinel` |
| Backend logs | `docker logs stocksentinel-backend`, or `backend/logs/{app,errors,access}.log` when running locally |
| Changed `backend/.env` | `docker compose up -d` recreates the container; no rebuild is needed. |
| Changed a `NEXT_PUBLIC_*` value | Rebuild the frontend: `docker compose up -d --build frontend`. |
| Trades fail with 503 | No market price is available for that symbol. Check network access and `FINNHUB_API_KEY`. |
| Start over with an empty database | `docker compose down -v` (**deletes all data**) |

Windows PowerShell helpers such as `run_migrations.ps1` and `backend/reset-database.ps1` are in the repo. They wrap the same `docker exec` and `alembic` commands.
