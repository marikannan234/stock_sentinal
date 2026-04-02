# Stock Sentinel - Quick Wins (Implement This Week!)

This document contains **ready-to-use code snippets** to immediately improve your application.  
**Estimated Time**: 4-6 hours to implement all quick wins  
**Impact**: Better error handling, security, and user experience

---

## Quick Win #1: Move Secrets to Environment Variables (30 min)

### Problem
- Streamlit app exposes NewsAPI key (security risk)
- Database password in docker-compose (should be env var)
- JWT secret is "change-me" (no good)

### Solution

**Step 1: Create `.env` file**
```bash
# backend/.env
ENVIRONMENT=local
DEBUG=true

# Database
DATABASE_URL=postgresql+psycopg2://stocksentinel:your_password@localhost:5432/stocksentinel

# Security
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30

# APIs
FINNHUB_API_KEY=your_finnhub_key_here
NEWSAPI_KEY=your_newsapi_key_here

# Redis (optional, for future)
REDIS_URL=redis://localhost:6379/0

# SMTP (optional, for email alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@stocksentinel.com
```

**Step 2: Create `.env.example` (commit this to git)**
```bash
# backend/.env.example
ENVIRONMENT=local
DEBUG=false
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
JWT_SECRET_KEY=change-me
FINNHUB_API_KEY=change-me
NEWSAPI_KEY=change-me
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=change-me
SMTP_PASSWORD=change-me
SMTP_FROM_EMAIL=noreply@stocksentinel.com
```

**Step 3: Add `.env` to `.gitignore`**
```bash
echo ".env" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

**Step 4: Fix `backend/app/config.py`**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    DEBUG: bool = False
    
    # Add validation
    APP_NAME: str = "StockSentinel API"
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]
    
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    FINNHUB_API_KEY: str | None = None
    NEWSAPI_KEY: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@stocksentinel.com"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Step 5: Update docker-compose.yml**
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: stocksentinel-db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${DB_NAME:-stocksentinel}
      POSTGRES_USER: ${DB_USER:-stocksentinel}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change-me}  # Override in .env
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
    container_name: stocksentinel-backend
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
```

---

## Quick Win #2: Add Error Handling to All Routes (1.5 hours)

### Problem
- Routes fail silently on errors
- No validation on user input
- External API failures crash endpoints

### Solution

**Step 1: Create exception handlers**

Create `backend/app/core/exceptions.py`:
```python
from fastapi import HTTPException, status

class StockNotFoundError(HTTPException):
    def __init__(self, ticker: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker} not found"
        )

class InvalidTickerError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ticker format"
        )

class ExternalAPIError(HTTPException):
    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch data from {service}. Please try again later."
        )

class RateLimitError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again in a few minutes."
        )
```

**Step 2: Update route handlers**

Example fix for `backend/app/api/routes/stock.py`:
```python
from app.core.exceptions import StockNotFoundError, ExternalAPIError, InvalidTickerError
import logging

logger = logging.getLogger(__name__)

def validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker"""
    ticker = ticker.strip().upper()
    if not ticker or len(ticker) > 10:
        raise InvalidTickerError()
    return ticker

@router.get("/{ticker}/quote", response_model=StockQuoteResponse)
async def get_stock_quote(ticker: str):
    """Get stock quote with proper error handling"""
    try:
        ticker = validate_ticker(ticker)
        
        # Check cache first
        cached = _quote_cache_get(ticker)
        if cached:
            logger.info(f"Cache hit for {ticker}")
            return cached
        
        # Fetch fresh data
        logger.info(f"Fetching fresh quote for {ticker}")
        quote_data = yf.Ticker(ticker).info
        
        if not quote_data or 'currentPrice' not in quote_data:
            raise StockNotFoundError(ticker)
        
        response = StockQuoteResponse(
            ticker=ticker,
            price=float(quote_data.get('currentPrice', 0)),
            change=float(quote_data.get('regularMarketChange', 0)),
            change_percent=float(quote_data.get('regularMarketChangePercent', 0)),
        )
        
        _quote_cache_set(ticker, response)
        return response
    
    except StockNotFoundError:
        raise
    except InvalidTickerError:
        raise
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {str(e)}")
        raise ExternalAPIError("YFinance")
```

---

## Quick Win #3: Add Input Validation with Pydantic (1 hour)

### Problem
- No validation on request bodies
- Missing required fields accepted silently
- Inconsistent response formats

### Solution

**Step 1: Create schema validation**

Create/update `backend/app/schemas/stock.py`:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class StockQuoteRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v):
        if not v.isalnum():
            raise ValueError('Ticker must be alphanumeric')
        return v.upper()

class StockQuoteResponse(BaseModel):
    ticker: str
    price: float = Field(..., gt=0)
    change: float
    change_percent: float
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "RELIANCE",
                "price": 2850.50,
                "change": 25.50,
                "change_percent": 0.90,
                "updated_at": "2026-04-01T10:30:00Z"
            }
        }
```

**Step 2: Apply to routes**

```python
from app.schemas.stock import StockQuoteResponse, StockQuoteRequest

@router.get("/{ticker}/quote", response_model=StockQuoteResponse)
async def get_stock_quote_new(ticker: str = Field(..., min_length=1, max_length=10)):
    """Get stock quote (with validation)"""
    ticker = ticker.upper()
    
    try:
        quote_data = yf.Ticker(ticker).info
        if not quote_data.get('currentPrice'):
            raise StockNotFoundError(ticker)
        
        return StockQuoteResponse(
            ticker=ticker,
            price=float(quote_data['currentPrice']),
            change=float(quote_data.get('regularMarketChange', 0)),
            change_percent=float(quote_data.get('regularMarketChangePercent', 0)),
            updated_at=datetime.utcnow()
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
```

---

## Quick Win #4: Add Comprehensive Logging (1 hour)

### Problem
- Can't debug issues in production
- No performance metrics
- No request tracking

### Solution

**Step 1: Setup structured logging**

Create `backend/app/core/logging.py`:
```python
import logging
import time
from fastapi import Request, Response
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create file handler
file_handler = logging.FileHandler('stock_sentinel.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

**Step 2: Add middleware for request logging**

Update `backend/app/main.py`:
```python
import time
from fastapi import Request
from app.core.logging import logger

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        status_code = response.status_code
        logger.info(
            f"← {request.method} {request.url.path} - "
            f"{status_code} ({process_time:.3f}s)"
        )
        
        # Warn if slow
        if process_time > 1.0:
            logger.warning(f"Slow request: {request.url.path} took {process_time:.3f}s")
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"✗ {request.method} {request.url.path} failed after {process_time:.3f}s: {str(e)}"
        )
        raise
```

**Step 3: Add logging to services**

```python
# In any service/route
from app.core.logging import logger

def get_stock_quote(ticker: str):
    logger.info(f"Fetching quote for {ticker}")
    start = time.time()
    
    try:
        data = yf.Ticker(ticker).info
        duration = time.time() - start
        logger.debug(f"Got quote for {ticker} in {duration:.2f}s")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch {ticker}: {str(e)}", exc_info=True)
        raise
```

---

## Quick Win #5: Add Rate Limiting (45 min)

### Problem
- API vulnerable to abuse
- Finnhub rate limit not handled
- No protection for heavy users

### Solution

**Step 1: Install slowapi**
```bash
pip install slowapi
```

**Step 2: Setup rate limiting**

Update `backend/app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Max 100 requests per minute.",
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )
```

**Step 3: Apply to routes**

```python
from app.main import limiter

@router.get("/{ticker}/quote")
@limiter.limit("30/minute")  # 30 requests per minute per IP
async def get_stock_quote(ticker: str, request: Request):
    """Get stock quote (rate limited)"""
    return get_stock_quote(ticker)


@router.post("/alerts")
@limiter.limit("10/minute")  # Stricter for POST operations
async def create_alert(alert: AlertCreate, request: Request):
    """Create alert (stricter rate limit)"""
    return create_alert(alert)
```

---

## Quick Win #6: Improve Frontend Error Handling (1 hour)

### Problem
- Frontend silently fails on API errors
- No user feedback for failures
- Network errors crash app

### Solution

**Step 1: Create API error handler**

Create `frontend/lib/api-client.ts`:
```typescript
import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
});

api.interceptors.response.use(
  response => response,
  error => {
    const err = error as AxiosError;
    
    if (err.response?.status === 401) {
      // Token expired, redirect to login
      window.location.href = '/login';
      return Promise.reject('Session expired');
    }
    
    if (err.response?.status === 429) {
      return Promise.reject('Too many requests. Please wait a moment.');
    }
    
    if (err.response?.status === 404) {
      return Promise.reject(`Resource not found: ${err.config?.url}`);
    }
    
    if (!err.response) {
      return Promise.reject('Network error. Check your connection.');
    }
    
    return Promise.reject(err.response.data?.detail || 'Something went wrong');
  }
);

export default api;
```

**Step 2: Create error boundary component**

Create `frontend/app/components/ErrorBoundary.tsx`:
```typescript
'use client';

import React, { ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

export class ErrorBoundary extends React.Component<Props> {
  state = { hasError: false, error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('Error caught:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-100 border border-red-400 rounded">
          <h2 className="text-red-800 font-bold">Something went wrong</h2>
          <p className="text-red-700">{this.state.error?.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Step 3: Use in layout**

```typescript
// frontend/app/layout.tsx
import { ErrorBoundary } from './components/ErrorBoundary';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}
```

---

## Quick Win #7: Add Database Indexes for Performance (15 min)

### Problem
- Slow queries when database grows
- No indexes on common filter columns

### Solution

Create `backend/alembic/versions/0003_add_indexes.py`:
```python
"""Add performance indexes.

Revision ID: 0003
Revises: 0002_watchlist_simplify
"""

from alembic import op

def upgrade() -> None:
    # Index for watchlist queries
    op.create_index('idx_watchlist_user_id', 'watchlists', ['user_id'])
    
    # Index for portfolio queries
    op.create_index('idx_portfolio_user_id', 'portfolios', ['user_id'])
    op.create_index('idx_portfolio_user_ticker', 'portfolios', ['user_id', 'ticker'], unique=True)
    
    # Index for sentiment queries
    op.create_index('idx_sentiment_ticker_date', 'sentiment_records', ['ticker', 'window_start'])

def downgrade() -> None:
    op.drop_index('idx_sentiment_ticker_date')
    op.drop_index('idx_portfolio_user_ticker')
    op.drop_index('idx_portfolio_user_id')
    op.drop_index('idx_watchlist_user_id')
```

Then run:
```bash
cd backend
alembic upgrade head
```

---

## Quick Win #8: Add API Documentation (30 min)

### Problem
- No clear documentation of endpoints
- Missing API authentication examples
- No example requests/responses

### Solution

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Stock Sentinel API",
        version="0.1.0",
        description="""
        Real-time stock market platform with AI-powered insights.
        
        ## Authentication
        Use JWT tokens obtained from `/api/auth/login` or `/api/auth/register`.
        Include the token in the Authorization header: `Bearer <token>`
        
        ## Rate Limiting
        API endpoints are rate limited to prevent abuse.
        - Standard endpoints: 100 requests/minute
        - Write operations: 30 requests/minute
        
        ## Usage Example
        ```bash
        # 1. Register or login
        curl -X POST http://localhost:8000/api/auth/register \\
          -H "Content-Type: application/json" \\
          -d '{"email":"user@example.com","password":"secure_password","full_name":"User"}'
        
        # 2. Use token from response
        curl http://localhost:8000/api/stock/RELIANCE/quote \\
          -H "Authorization: Bearer <your_token>"
        ```
        """,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

Access at: `http://localhost:8000/api/docs`

---

## Quick Win #9: Setup Basic Monitoring (1 hour)

### Problem
- Can't see what's happening in production
- No uptime monitoring
- Can't track performance trends

### Solution

**Step 1: Add Prometheus metrics**

```bash
pip install prometheus-client
```

**Step 2: Add metrics middleware**

Create `backend/app/core/metrics.py`:
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
request_count = Counter(
    'request_count',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'active_requests',
    'Active requests'
)
```

**Step 3: Add to main.py**

```python
from app.core.metrics import request_count, request_duration, active_requests
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    active_requests.inc()
    start = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    active_requests.dec()
    return response

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, REGISTRY
    return generate_latest(REGISTRY)
```

**Step 4: Add to docker-compose.yml**

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
```

**Step 5: Create prometheus.yml**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stock-sentinel'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

View at: `http://localhost:9090`

---

## Quick Win #10: Improve Frontend State Management (1 hour)

### Problem
- Props drilling for auth state
- No persistent user session
- No cached API responses

### Solution

**Step 1: Create better store**

Create `frontend/lib/stores.ts`:
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  email: string;
  full_name?: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-store', // Will persist to localStorage
    }
  )
);

interface PriceStore {
  prices: Record<string, number>;
  setPrice: (ticker: string, price: number) => void;
}

export const usePriceStore = create<PriceStore>((set) => ({
  prices: {},
  setPrice: (ticker: string, price: number) =>
    set((state) => ({
      prices: { ...state.prices, [ticker]: price },
    })),
}));
```

**Step 2: Use in components**

```typescript
// frontend/app/components/Header.tsx
import { useAuthStore } from '@/lib/stores';

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="bg-blue-600 text-white p-4">
      <div className="flex justify-between items-center">
        <h1>Stock Sentinel</h1>
        {user ? (
          <div>
            <span className="mr-4">{user.email}</span>
            <button onClick={logout} className="bg-blue-800 px-4 py-2 rounded">
              Logout
            </button>
          </div>
        ) : (
          <a href="/login" className="underline">
            Login
          </a>
        )}
      </div>
    </header>
  );
}
```

---

## Implementation Checklist

Complete these in order (estimated: 4-6 hours):

Week 1, Day 1 (30 min):
- [ ] Quick Win #1: Move secrets to .env
- [ ] Commit to git

Week 1, Day 2 (1.5 hours):
- [ ] Quick Win #2: Add error handling
- [ ] Quick Win #3: Add input validation
- [ ] Test all endpoints

Week 1, Day 3 (2 hours):
- [ ] Quick Win #4: Add logging
- [ ] Quick Win #5: Add rate limiting
- [ ] Quick Win #7: Add database indexes

Week 1, Day 4 (1.5 hours):
- [ ] Quick Win #6: Improve frontend error handling
- [ ] Quick Win #8: Add API documentation
- [ ] Quick Win #10: Improve state management

Week 1, Day 5 (1 hour):
- [ ] Quick Win #9: Setup monitoring
- [ ] Deploy to staging
- [ ] Final testing

---

## Verification Commands

```bash
# Test API error handling
curl -X GET http://localhost:8000/api/stock/INVALID/quote

# Test rate limiting
for i in {1..101}; do curl http://localhost:8000/api/stock/RELIANCE/quote; done

# View logs
tail -f stock_sentinel.log

# Check Swagger documentation
open http://localhost:8000/api/docs

# Check metrics
curl http://localhost:8000/metrics
```

---

**After completing these quick wins, you're ready for Phase 1: Foundation & Infrastructure.**

Next steps:
1. Setup tests (pytest)
2. Setup CI/CD (GitHub Actions)
3. Deploy to staging environment
4. Begin Phase 2: Alerts System

Good luck! 🚀
