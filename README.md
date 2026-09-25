# Stock Sentinel

Stock Sentinel is a stock-market dashboard with price alerts and paper trading.

- **Backend:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, APScheduler. Market data comes from Finnhub and yfinance, and alerts go out by email (SMTP) and optionally WhatsApp (Twilio).
- **Frontend:** Next.js 15, React 18, Zustand, Axios, Tailwind CSS.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env   # then set JWT_SECRET_KEY and the MAIL_* values
docker compose up --build
```

| Service  | URL                                   |
|----------|---------------------------------------|
| Frontend | http://localhost:3000                 |
| API      | http://localhost:8000/api             |
| API docs | http://localhost:8000/docs (Swagger)  |
| Health   | http://localhost:8000/api/health/     |

The backend container runs `alembic upgrade head` before it starts.

## Documentation

- [docs/setup.md](docs/setup.md): local development, environment variables, migrations, tests, troubleshooting
- [docs/architecture.md](docs/architecture.md): how the backend and frontend fit together, including the trading model
- [docs/deployment.md](docs/deployment.md): building images and deploying

## Tests

```bash
cd backend
python -m pytest -q
```

CI (`.github/workflows/ci.yml`) runs the backend tests, the frontend lint and build, and the Docker image builds on every push and pull request to `main`.

## Current limitations

- Password reset is disabled. `POST /api/auth/forgot-password` returns 501 until a secure flow exists.
- Trading is simulated (paper trading) with a per-user cash balance. It uses no real brokerage.
