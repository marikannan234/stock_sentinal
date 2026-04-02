# Stock Sentinel - Detailed Implementation Roadmap

## Quick Stats
- **Lines of Code**: ~2,500 (backend) + ~1,500 (frontend)
- **Features Implemented**: 13/45 (29%)
- **Time to MVP**: 8-12 weeks
- **Team Size**: Assumes 1 developer working 3-4 hrs/day

---

## Week-by-Week Breakdown

### WEEK 1: Security & Error Handling
**Goal**: Make codebase production-ready for errors and security

#### Day 1: Security Fixes
- [ ] Audit `.env` files - move all secrets out
  - API keys in `streamlit_app.py` (line 15)
  - Database password in config
  - JWT secret
- [ ] Create `.env.example` template
- [ ] Add environment validation on startup
- [ ] Implement secret rotation helper

**Task Details**:
```python
# Fix: backend/app/config.py
# Add validation that raises error if secrets not set

from pydantic import field_validator

class Settings(BaseSettings):
    JWT_SECRET_KEY: str  # Will raise ValidationError if not in .env
    FINNHUB_API_KEY: str | None = None  # OK to be none but should warn
    
    @field_validator('JWT_SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == "change-me":
            raise ValueError("JWT_SECRET_KEY must be set in .env")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 chars")
        return v

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warn if API key not set
    if not settings.FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set - news fetching will fail")
    yield
```

#### Day 2: Error Handling
- [ ] Add exception handlers for all routes
- [ ] Create custom exception classes
- [ ] Add input validation with pydantic
- [ ] Handle API timeout/rate limits gracefully

**Code Changes Required**:
```bash
# Add to requirements.txt
python-logging-json==2.0.7  # Structured logging

# Files to modify:
backend/app/main.py  # Add exception handlers
backend/app/core/exceptions.py  # New file with custom exceptions
backend/app/api/routes/*.py  # Add error handling to all endpoints
```

#### Day 3: Logging Setup
- [ ] Setup structured logging with JSON output
- [ ] Add request/response logging middleware
- [ ] Add performance tracking (slow queries)
- [ ] Create log rotation strategy

**Files to Create**:
```python
# backend/app/core/logging.py
import logging
import json
from pythonjsonlogger import jsonlogger

logging.basicConfig(
    level=logging.INFO,
    format='%(timestamp)s %(name)s %(levelname)s %(message)s'
)

# Add to main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"Request {request.url.path} completed in {duration:.2f}s")
    return response
```

#### Day 4: Rate Limiting
- [ ] Install slowapi
- [ ] Add rate limiting to all endpoints
- [ ] Configure per-user limits (after auth)
- [ ] Add documentation for API consumers

```python
# backend/app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# On protected routes
@router.get("/stock/{ticker}")
@limiter.limit("100/minute")
def get_stock(ticker: str):
    pass
```

#### Day 5: API Documentation
- [ ] Add docstrings to all endpoints
- [ ] Configure OpenAPI/Swagger properly
- [ ] Test Swagger UI at `/docs`
- [ ] Create API usage guide

```bash
# Add to requirements.txt
python-multipart>=0.0.6  # Already there - needed for Swagger

# Update backend/app/main.py
app = FastAPI(
    title="Stock Sentinel API",
    description="Real-time stock trading platform with AI predictions",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
```

**Deliverable**: Production-ready error handling + security  
**Estimated Hours**: 20-25 hrs

---

### WEEK 2: Testing & Database Cleanup
**Goal**: Establish quality gates with tests

#### Day 1: Setup Testing Infrastructure
- [ ] Install pytest + fixtures
- [ ] Create test database setup/teardown
- [ ] Write 10 unit tests (authentication, watchlist, portfolio)
- [ ] Setup GitHub Actions CI/CD

```bash
# requirements-dev.txt
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
httpx==0.24.0  # For testing async endpoints
```

#### Day 2-3: Write Core Tests
- [ ] Auth endpoints (login, register, token refresh)
- [ ] Watchlist CRUD operations
- [ ] Portfolio calculations
- [ ] Stock quote caching

**Coverage Target**: 50% (focus on critical paths)

#### Day 4: Fix Database Schema
- [ ] Review migration `0002_watchlist_simplify.py` 
- [ ] Create migration `0003_add_alerts_schema.py`
- [ ] Add missing indices for performance
- [ ] Add database constraints

```python
# Create new migration file: 0003_add_alerts_schema.py
def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("ticker", sa.String(16)),
        sa.Column("alert_type", sa.String(20)),
        sa.Column("trigger_value", sa.Float()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_alerts_user_ticker", "alerts", ["user_id", "ticker"])
```

#### Day 5: Documentation
- [ ] Create API documentation (endpoints, auth, examples)
- [ ] Create database schema diagram
- [ ] Create development setup guide
- [ ] Create deployment checklist

**Deliverable**: Tested, documented, clean codebase  
**Estimated Hours**: 25-30 hrs

---

### WEEK 3-4: Alerts System (Tier 1 Critical)
**Goal**: Implement complete alert system with notifications

#### Week 3 - Database & APIs

**Day 1: Database Schema**
- [ ] Create `alerts` table (schema shown above)
- [ ] Create `alert_triggers` table (trigger history)
- [ ] Create `notifications` table (delivery log)
- [ ] Add database indices

**Day 2-3: Alert APIs**
- [ ] POST `/api/alerts` - Create alert
- [ ] GET `/api/alerts` - List user's alerts
- [ ] PUT `/api/alerts/{id}` - Update alert
- [ ] DELETE `/api/alerts/{id}` - Delete alert
- [ ] POST `/api/alerts/{id}/test` - Test alert manually

```python
# backend/app/api/routes/alerts.py
from pydantic import BaseModel, Field

class AlertCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16)
    alert_type: Literal['price', 'percentage', 'volume', 'crash']
    trigger_value: float = Field(..., gt=0)

class AlertResponse(AlertCreate):
    id: int
    is_active: bool
    created_at: datetime

@router.post("", response_model=AlertResponse)
def create_alert(
    alert: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a new price alert"""
    db_alert = Alert(
        user_id=current_user.id,
        ticker=alert.ticker.upper(),
        alert_type=alert.alert_type,
        trigger_value=alert.trigger_value,
    )
    db.add(db_alert)
    db.commit()
    return db_alert
```

**Day 4: Alert Validation**
- [ ] Validate trigger values (reasonable thresholds)
- [ ] Prevent duplicate alerts
- [ ] Test all alert endpoints

**Day 5: Documentation**
- [ ] Document alert types and parameters
- [ ] Create alert examples in Swagger

#### Week 4 - Background Jobs & Notifications

**Day 1: Celery Setup**
- [ ] Add Redis to docker-compose.yml
- [ ] Install celery, redis packages
- [ ] Create celery app configuration
- [ ] Create background job for checking alerts

```python
# backend/app/workers/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "stock_sentinel",
    broker=f"redis://{settings.REDIS_URL}",
    backend=f"redis://{settings.REDIS_URL}",
)

celery_app.conf.beat_schedule = {
    'check-alerts-every-1-minute': {
        'task': 'app.workers.tasks.check_all_alerts',
        'schedule': 60.0,  # Every 60 seconds during market hours
    },
}
```

**Day 2-3: Alert Checking Logic**
```python
# backend/app/workers/tasks.py
from app.workers.celery_app import celery_app

@celery_app.task
def check_all_alerts():
    """Check all active alerts and trigger if conditions met"""
    alerts = db.query(Alert).filter(Alert.is_active == True).all()
    
    for alert in alerts:
        current_price = get_stock_quote(alert.ticker)
        
        if alert.alert_type == 'price':
            if current_price >= alert.trigger_value:
                trigger_alert(alert, current_price)
        
        elif alert.alert_type == 'percentage':
            change = calculate_percentage_change(alert.ticker)
            if abs(change) >= alert.trigger_value:
                trigger_alert(alert, current_price)
        
        elif alert.alert_type == 'volume':
            volume = get_current_volume(alert.ticker)
            if volume > alert.trigger_value:
                trigger_alert(alert, current_price)
        
        elif alert.alert_type == 'crash':
            change = calculate_percentage_change(alert.ticker, period='1h')
            if change <= -alert.trigger_value:  # Negative threshold
                trigger_alert(alert, current_price)

def trigger_alert(alert: Alert, current_price: float):
    """Send notification and log trigger"""
    # Create trigger record
    trigger = AlertTrigger(
        alert_id=alert.id,
        trigger_price=current_price,
        notification_status='pending'
    )
    db.add(trigger)
    db.commit()
    
    # Send notification
    send_email_notification(alert.user, alert, current_price)
```

**Day 4: Email Notifications**
- [ ] Setup SMTP configuration
- [ ] Create email templates
- [ ] Send test emails
- [ ] Log notification status

```python
# backend/app/core/email.py
from email.mime.text import MIMEText
import smtplib

def send_email_alert(user_email: str, alert: Alert, price: float):
    subject = f"🚨 Alert: {alert.ticker} reached {price}"
    
    html_body = f"""
    <h2>Stock Alert Triggered!</h2>
    <p>Your alert for {alert.ticker} has been triggered.</p>
    <p><strong>Alert Type</strong>: {alert.alert_type}</p>
    <p><strong>Current Price</strong>: ${price}</p>
    <p><a href="https://yourapp.com/stock/{alert.ticker}">View Stock</a></p>
    """
    
    # Send via SMTP
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = user_email
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

**Day 5: Test & Documentation**
- [ ] Write tests for alert checking
- [ ] Test email delivery
- [ ] Document how to run Celery
- [ ] Create monitoring dashboard for Celery tasks

**Deliverable**: Complete alert system (database → checking → notification)  
**Estimated Hours**: 50-60 hrs

---

### WEEK 5-6: Technical Indicators & Real-Time (Tier 2)
**Goal**: Enable sophisticated trading with live updates

#### Week 5 - Technical Indicators

**Day 1: Indicators Endpoint**
```python
# backend/app/api/routes/indicators.py
import pandas_ta as ta

class IndicatorsResponse(BaseModel):
    ticker: str
    date: date
    sma_20: float
    sma_50: float
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_lower: float

@router.get("/{ticker}", response_model=List[IndicatorsResponse])
def get_stock_indicators(
    ticker: str,
    period: Literal['1d', '1w', '1m', '1y'] = '1d',
    current_user: User = Depends(get_current_user),
):
    """Get technical indicators for a stock"""
    # Fetch historical data
    df = yf.download(ticker, period='3mo', interval='1d')
    
    # Calculate indicators
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    macd = ta.macd(df['Close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDh_12_26_9']
    
    bb = ta.bbands(df['Close'], length=20)
    df['BB_Upper'] = bb['BBU_20_2.0']
    df['BB_Lower'] = bb['BBL_20_2.0']
    
    # Return as JSON
    return format_response(df)
```

**Day 2: Database Storage for Indicators**
- [ ] Create `indicators` table to store pre-calculated values
- [ ] Create Celery job to update indicators hourly
- [ ] Add caching in Redis

**Day 3-4: Historical Data Pipeline**
- [ ] Create job to fetch 3 years of OHLC data
- [ ] Store in PostgreSQL `ohlc_data` table
- [ ] Index by (ticker, date) for fast retrieval
- [ ] Schedule daily update at 10 PM

```python
@celery_app.task
def fetch_and_store_historical_data():
    """Fetch 3 years of data for all watched stocks"""
    stocks = db.query(Stock).all()
    
    for stock in stocks:
        df = yf.download(stock.ticker, period='3y', interval='1d')
        
        for idx, row in df.iterrows():
            ohlc = OhlcData(
                ticker=stock.ticker,
                date=idx.date(),
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=int(row['Volume']),
            )
            db.add(ohlc)
        
        db.commit()
```

**Day 5: Frontend Integration**
- [ ] Pass indicators data to chart component
- [ ] Display on stock details page

#### Week 6 - Real-Time Updates

**Day 1: WebSocket Setup**
- [ ] Create WebSocket endpoint
- [ ] Implement Redis pub/sub
- [ ] Create message schema

```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/prices")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    redis_conn = redis.Redis.from_url(settings.REDIS_URL)
    pubsub = redis_conn.pubsub()
    
    ticker = None
    try:
        while True:
            # Receive ticker subscription request
            data = await websocket.receive_json()
            action = data.get('action')
            
            if action == 'subscribe':
                ticker = data['ticker'].upper()
                pubsub.subscribe(f"price:{ticker}")
            
            # Listen for price updates
            for message in pubsub.listen():
                if message['type'] == 'message':
                    price_data = json.loads(message['data'])
                    await websocket.send_json(price_data)
    
    except WebSocketDisconnect:
        if ticker:
            pubsub.unsubscribe(f"price:{ticker}")
        pubsub.close()
```

**Day 2-3: Background Price Publisher**
```python
# Create job that runs every minute
@celery_app.task
def publish_prices():
    """Fetch current prices and publish to Redis"""
    stocks = db.query(Stock).limit(500).all()
    redis_conn = redis.Redis.from_url(settings.REDIS_URL)
    
    for stock in stocks:
        price_data = get_stock_quote(stock.ticker)
        
        # Publish to Redis channel
        redis_conn.publish(
            f"price:{stock.ticker}",
            json.dumps(price_data)
        )
        
        # Also store in cache for HTTP requests
        cache.setex(f"quote:{stock.ticker}", 300, json.dumps(price_data))

# Schedule every 1 minute during market hours
celery_app.conf.beat_schedule = {
    'publish-prices-every-minute': {
        'task': 'app.workers.tasks.publish_prices',
        'schedule': 60.0,
        'kwargs': {}
    },
}
```

**Day 4: Frontend WebSocket Client**
```typescript
// frontend/lib/websocket.ts
export class PriceWebSocket {
  private ws: WebSocket | null = null;

  connect() {
    this.ws = new WebSocket(`ws://localhost:8000/ws/prices`);
    
    this.ws.onopen = () => {
      console.log("WebSocket connected");
    };
    
    this.ws.onmessage = (event) => {
      const priceData = JSON.parse(event.data);
      // Update store with new price
      usePriceStore.setState({
        [priceData.ticker]: priceData
      });
    };
  }

  subscribe(ticker: string) {
    this.ws?.send(JSON.stringify({
      action: 'subscribe',
      ticker: ticker
    }));
  }
}
```

**Day 5: Testing & Deployment**
- [ ] Test WebSocket connections
- [ ] Load test with multiple connections
- [ ] Deploy to staging
- [ ] Monitor Redis/Celery

**Deliverable**: Real-time price updates + technical indicators  
**Estimated Hours**: 45-55 hrs

---

### WEEK 7-8: Frontend Improvements
**Goal**: Beautiful, interactive dashboard

#### Week 7 - Chart Components

**Day 1: Stock Chart Component**
```typescript
// frontend/app/components/StockChart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function StockChart({ ticker, data, indicators }) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="close" stroke="#8884d8" />
        <Line type="monotone" dataKey="sma_20" stroke="#82ca9d" />
        <Line type="monotone" dataKey="sma_50" stroke="#ffc658" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

**Day 2: Portfolio Dashboard**
- [ ] Chart showing pie chart of holdings
- [ ] P&L summary
- [ ] Allocation by sector
- [ ] Performance metrics

**Day 3: Watchlist Enhancement**
- [ ] Real-time price updates via WebSocket
- [ ] Display percentage change
- [ ] Add/remove from watchlist inline
- [ ] Click to view stock details

**Day 4-5: Stock Details Page**
- [ ] Chart with multiple timeframes (1D, 1W, 1M, 1Y)
- [ ] Show technical indicators
- [ ] Display news feed with sentiment
- [ ] Add to watchlist / Buy buttons

**Deliverable**: Interactive frontend with real-time updates  
**Estimated Hours**: 40-50 hrs

#### Week 8 - Advanced UI

**Day 1-2: Alert Management UI**
- [ ] List of user's alerts
- [ ] Create alert form with validation
- [ ] Edit/delete alerts
- [ ] Test alert button

**Day 3: Search & Filters**
- [ ] Advanced stock search
- [ ] Filter by sector, market cap
- [ ] Sort by various metrics
- [ ] Save search filters

**Day 4-5: Polish**
- [ ] Responsive design for mobile
- [ ] Loading states
- [ ] Error handling UI
- [ ] Dark mode support

---

### WEEK 9-10: AI Features & Advanced
**Goal**: Intelligent features that set you apart

#### Week 9 - Predictions & Recommendations

**Day 1: Integrate Prediction API**
```python
# backend/app/api/routes/predictions.py
@router.get("/{ticker}/forecast", response_model=ForecastResponse)
def get_price_forecast(ticker: str, days: int = 7):
    """Get 7-day price forecast using Prophet"""
    
    service = PredictionService(horizon_days=days)
    prediction_points = service.predict(ticker)
    
    return ForecastResponse(
        ticker=ticker,
        forecast_date=date.today(),
        predictions=[
            {'date': p.date, 'price': p.predicted_price}
            for p in prediction_points
        ]
    )
```

**Day 2: Buy/Sell Recommendations**
```python
@router.get("/{ticker}/recommendation", response_model=RecommendationResponse)
def get_recommendation(ticker: str):
    """Get buy/sell recommendation based on technical + fundamental analysis"""
    
    # Get prediction
    future_price = predict_price(ticker, days=7)
    current_price = get_stock_quote(ticker)
    upside = (future_price - current_price) / current_price
    
    # Get technical signals
    indicators = get_technical_indicators(ticker)
    rsi = indicators['rsi'].iloc[-1]
    macd = indicators['macd'].iloc[-1]
    
    # Score: -1 (SELL), 0 (HOLD), 1 (BUY)
    score = 0
    if upside > 0.05 and rsi < 30:
        score = 1  # BUY - undervalued with upside
    elif upside < -0.05 and rsi > 70:
        score = -1  # SELL - overvalued
    
    return RecommendationResponse(
        ticker=ticker,
        recommendation='BUY' if score > 0 else 'SELL' if score < 0 else 'HOLD',
        confidence=min(abs(upside), 1.0),  # 0-100%
        reasons=[
            f"Price forecasted to reach ${future_price:.2f}",
            f"RSI at {rsi:.1f}" + (" (oversold)" if rsi < 30 else " (overbought)" if rsi > 70 else ""),
        ]
    )
```

**Day 3: Stock Screener**
```python
# backend/app/api/routes/screener.py
@router.post("/scan", response_model=List[StockScore])
def screen_stocks(filters: ScreenerFilters):
    """Find stocks matching given criteria"""
    
    query = db.query(Stock)
    
    if filters.sector:
        query = query.filter(Stock.sector == filters.sector)
    
    if filters.min_pe:
        query = query.filter(Stock.pe_ratio >= filters.min_pe)
    
    # Get indicators for filtering
    stocks = query.limit(500).all()
    
    results = []
    for stock in stocks:
        indicators = get_technical_indicators(stock.ticker)
        rsi = indicators['rsi'].iloc[-1]
        
        # Apply filters
        if filters.min_rsi and rsi < filters.min_rsi:
            continue
        if filters.max_rsi and rsi > filters.max_rsi:
            continue
        
        # Score the stock
        current_price = get_stock_quote(stock.ticker)
        forecast = predict_price(stock.ticker)
        upside = (forecast - current_price) / current_price
        
        results.append(StockScore(
            ticker=stock.ticker,
            name=stock.name,
            price=current_price,
            upside_pct=upside * 100,
            rsi=rsi,
            score=upside  # For sorting
        ))
    
    return sorted(results, key=lambda x: x.score, reverse=True)[:20]
```

**Day 4-5: Market Dashboard**
```python
# backend/app/api/routes/market.py
@router.get("/dashboard", response_model=MarketDashboard)
def get_market_dashboard():
    """Get NIFTY, SENSEX, global indices, market sentiment"""
    
    # Fetch major indices
    nifty_price = get_stock_quote("^NSEI")  # NIFTY 50
    sensex_price = get_stock_quote("^BSESN")  # BSE SENSEX
    
    # Calculate market sentiment
    top_gainers = get_gainers_losers('gainers', limit=5)
    top_losers = get_gainers_losers('losers', limit=5)
    
    # Market breadth
    up_count = count_stocks_up()
    down_count = count_stocks_down()
    
    return MarketDashboard(
        nifty_50={'price': nifty_price, 'change_pct': get_change_pct("^NSEI")},
        sensex={'price': sensex_price, 'change_pct': get_change_pct("^BSESN")},
        global_indices={
            'sp500': get_stock_quote("^GSPC"),
            'nasdaq': get_stock_quote("^IXIC"),
            'dax': get_stock_quote("^GDAXI"),
        },
        sentiment={
            'up_count': up_count,
            'down_count': down_count,
            'up_percentage': (up_count / (up_count + down_count)) * 100
        },
        top_gainers=top_gainers,
        top_losers=top_losers,
    )
```

#### Week 10 - AI Chat & Polish

**Day 1-2: AI Chat Assistant**
- [ ] Setup open-source LLM (Llama 2 or similar)
- [ ] Create chat endpoint with context
- [ ] Integrate market data into prompts
- [ ] Test with sample queries

**Day 3-4: Advanced Features**
- [ ] Earnings calendar
- [ ] IPO tracker
- [ ] Insider transactions
- [ ] Sector analysis

**Day 5: Performance Testing**
- [ ] Load test the API
- [ ] Optimize slow queries
- [ ] Profile endpoints
- [ ] Documentation

**Deliverable**: Advanced AI features + market dashboard  
**Estimated Hours**: 50-60 hrs

---

### WEEK 11-12: Deployment & Monitoring
**Goal**: Production-ready deployment

#### Week 11 - Infrastructure

**Day 1: Docker Optimization**
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Setup docker-compose for production
- [ ] Environment-specific configurations

**Day 2: Kubernetes (if scaling needed)**
- [ ] Create k8s manifests
- [ ] Setup persistent volumes for DB
- [ ] Configure autoscaling

**Day 3: Database Setup**
- [ ] Production database backup strategy
- [ ] Database replication (optional)
- [ ] Performance tuning (VACUUM, ANALYZE)

```sql
-- Production database setup
CREATE INDEX idx_ohlc_ticker_date ON ohlc_data(ticker, date DESC);
ANALYZE ohlc_data;
CREATE MATERIALIZED VIEW daily_gainers_losers AS
SELECT ticker, close * 100 / close AS change_pct
FROM ohlc_data
WHERE date = CURRENT_DATE - 1
ORDER BY change_pct DESC;
```

**Day 4: Monitoring Setup**
- [ ] Install Prometheus (metrics collection)
- [ ] Setup Grafana (dashboards)
- [ ] Configure alerting rules

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
```

**Day 5: CI/CD Pipeline**
- [ ] GitHub Actions workflow
- [ ] Automated testing on push
- [ ] Automated deployment to staging
- [ ] Manual approval for production

```yaml
# .github/workflows/main.yml
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest backend/ -v --cov
      - name: Build Docker image
        run: docker build -t stock-sentinel:${{ github.sha }} .
```

#### Week 12 - Final Polish & Launch

**Day 1-2: Security Audit**
- [ ] Review secrets management
- [ ] Test SQL injection prevention
- [ ] Test authentication/authorization
- [ ] SSL/TLS setup

**Day 3: Performance Optimization**
- [ ] Reduce N+1 queries
- [ ] Enable HTTP caching
- [ ] Optimize frontend bundle
- [ ] Test page load times

**Day 4: Documentation**
- [ ] API documentation complete
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Developer setup guide

**Day 5: Launch Prep**
- [ ] Get SSL certificate
- [ ] Configure domain
- [ ] Final testing in production
- [ ] Create launch checklist

---

## Technology Stack Summary

### Backend
```
Language: Python 3.11
Framework: FastAPI 0.115
Server: Uvicorn
Database: PostgreSQL 15 + TimescaleDB
Cache: Redis 7
Job Queue: Celery 5 + RabbitMQ 3
Data: Pandas, NumPy
ML: Prophet, scikit-learn, transformers (FinBERT)
Testing: Pytest, pytest-asyncio
```

### Frontend
```
Framework: Next.js 14
Language: TypeScript 5
Styling: Tailwind CSS
Charts: Recharts
State: Zustand
HTTP: Axios
Real-time: WebSocket + Socket.IO
Testing: Jest, React Testing Library
```

### Infrastructure
```
Containerization: Docker
Orchestration: Docker Compose (dev), Kubernetes (prod)
CI/CD: GitHub Actions
Monitoring: Prometheus + Grafana
Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
Error Tracking: Sentry
APM: New Relic or Datadog (optional)
```

---

## Success Criteria

### Functional Requirements (MVP)
- [ ] Users can register/login
- [ ] Real-time stock prices with 1-min updates
- [ ] Watchlist with > 100 stocks
- [ ] Portfolio tracking with P&L
- [ ] Price alerts (working 99% of the time)
- [ ] Technical indicators (SMA, RSI, MACD, Bollinger Bands)
- [ ] News sentiment analysis
- [ ] Buy/Sell recommendations

### Performance Targets
- [ ] API response time < 200ms (p95)
- [ ] WebSocket latency < 100ms
- [ ] Database queries < 100ms (p95)
- [ ] Frontend load time < 2s (Lighthouse > 85)
- [ ] Uptime > 99.5%

### Quality Metrics
- [ ] Test coverage > 75%
- [ ] Zero critical security vulnerabilities
- [ ] Zero production errors in first week
- [ ] API documentation complete
- [ ] All endpoints have rate limiting

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| External API rate limits | High | Implement caching, queue system |
| Database performance | High | Proper indexing, partitioning |
| WebSocket  scalability | Medium | Connection pooling, Redis pub/sub |
| Model prediction accuracy | Medium | Backtesting, user feedback |
| Data staleness | Medium | Scheduled refresh jobs |
| Security vulnerabilities | High | Regular audits, OWASP checklist |

---

## Questions Before Starting

1. **API Keys**: Do you have Finnhub API access? (free tier has limits)
2. **Hosting Budget**: Cloud (AWS/GCP) or self-hosted?
3. **Timeline**: Can you commit 3-4 hrs daily for 12 weeks?
4. **Team Growth**: Will you hire as the project grows?
5. **Monetization**: Free, freemium, or enterprise model?
6. **Data**: Just India (NSE/BSE) or global stocks?

---

**Document Version**: 1.0  
**Created**: April 1, 2026  
**Status**: Ready for Implementation  
**Next Review**: End of Week 2
