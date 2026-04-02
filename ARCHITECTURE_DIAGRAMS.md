# Stock Sentinel - Visual Architecture & Diagrams

## 🏗️ Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Pages: Login, Dashboard, Portfolio, Stocks, Watchlist     │ │
│  │ Charts: Recharts (not yet connected)                      │ │
│  │ State: Zustand (basic setup)                              │ │
│  │ Analytics: Missing                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬──────────────────────────────────────┘
                          │ Axios calls
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Routes:                                                    │ │
│  │  ✅ /auth (register, login, token)                         │ │
│  │  ✅ /stock (quote, historical data - basic caching)       │ │
│  │  ✅ /news (fetch from Finnhub)                            │ │
│  │  ✅ /sentiment (rule-based + FinBERT available)           │ │
│  │  ✅ /watchlist (CRUD)                                     │ │
│  │  ✅ /portfolio (CRUD + P&L)                               │ │
│  │  ✅ /search (ticker search)                               │ │
│  │  ⚠️  /predictions (exists, not exposed)                   │ │
│  │  ❌ /alerts (missing - CRITICAL)                          │ │
│  │  ❌ /indicators (missing - SMA, RSI, MACD)                │ │
│  │  ❌ /ws (WebSocket - missing)                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Features:                                                  │ │
│  │  ✅ JWT Authentication (30-min tokens)                    │ │
│  │  ✅ CORS enabled                                          │ │
│  │  ✅ Request validation (partial)                          │ │
│  │  ❌ Error handling (needs improvement)                    │ │
│  │  ❌ Rate limiting (no protection)                         │ │
│  │  ❌ Logging (minimal)                                     │ │
│  │  ❌ Tests (zero coverage)                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────┬──────────┬──────────────┬─────────────┬──────────────┬───┘
       │          │              │             │              │
       ▼          ▼              ▼             ▼              ▼
    YFinance  Finnhub      PostgreSQL       In-Memory    FinBERT
   (quotes)   (news)      (user, stocks,    Cache        (ML model)
              (news)       holdings)        (5min TTL)    (unused)
```

---

## 🎯 Target Architecture (After Phase 6)

```
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js + TanStack)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Real-time: WebSocket + Live Price Updates                │ │
│  │ Charts: Interactive with Technical Overlays              │ │
│  │ State: Proper store patterns + data caching              │ │
│  │ Pages: Full dashboards, screener, recommendations        │ │
│  │ Mobile: Responsive design, PWA ready                     │ │
│  │ Alerts: User notifications, settings                     │ │
│  │ AI: Chat assistant, buy/sell signals                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬──────────────────────────────────────┘
                          │ API + WebSocket
        ┌─────────────────┴─────────────────┐
        ▼                                     ▼
    HTTP API                          WebSocket Handler
  (request/response)               (real-time updates)
        │                                     │
        │          ┌────────────────────────┘
        │          │
        ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI - Scaled)                    │
│  ┌─ Load Balancer (Nginx)                                      │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ API Instances (3x):                                  │ │ │
│  │  │  • Stock Service (quotes, OHLC, indicators)         │ │ │
│  │  │  • Sentiment Service (FinBERT model)                │ │ │
│  │  │  • User Service (auth, portfolio, alerts)           │ │ │
│  │  │  • Prediction Service (Prophet, recommendations)    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Background Workers (Celery - 2x instances):          │ │ │
│  │  │  • Fetch prices every 1 minute                      │ │ │
│  │  │  • Check alerts every 1 minute                      │ │ │
│  │  │  • Calculate indicators hourly                      │ │ │
│  │  │  • Refresh historical data daily                    │ │ │
│  │  │  • Train models weekly                              │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Scheduled Jobs (Celery Beat):                        │ │ │
│  │  │  • Price updates (every 1 min)                      │ │ │
│  │  │  • Alert checks (every 1 min)                       │ │ │
│  │  │  • Sentiment updates (every 2 hrs)                  │ │ │
│  │  │  • Predictions (daily 10 PM)                        │ │ │
│  │  │  • Data cleanup (weekly)                            │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───┬──────────────┬──────────────┬─────────────┬──────────────┬──┘
    │              │              │             │              │
    ▼              ▼              ▼             ▼              ▼
  PostgreSQL     Redis      RabbitMQ     External APIs   Monitoring
  (time-series  (hot cache) (message    (YFinance,    (Prometheus+
   data)        (pub/sub)    queue)      Finnhub)      Grafana)
```

---

## 📊 Data Flow Diagrams

### Current (Simple, Bottleneck-Prone)
```
┌───────────────────────────────────────────────────────────────┐
│                    USER ACTION                                 │
│             (Click "View Stock RELIANCE")                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Router Request       │
            │  /api/stock/RELIANCE  │
            └───────────┬───────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Check In-Memory Cache (5 min)   │
         │  _quote_cache[RELIANCE]          │
         └───────────┬──────────────────────┘
                     │
            Found? ──┴── Not Found
             (fast)       (slow)
              │              │
              ▼              ▼
            Return      Fetch YFinance
            (0-1ms)     (3-5 seconds!)
                            │
                            ▼
                      Parse Response
                            │
                            ▼
                      Store in Cache
                            │
                            ▼
                      Return to Frontend
                            │
                            ▼
                ┌─────────────────────────┐
                │  Update UI with Price   │
                │  (after 5 seconds wait) │
                └─────────────────────────┘

PROBLEM: User sees loading spinner for 5 seconds,
         cache gets invalidated when server restarts,
         no real-time updates
```

### Recommended (Scalable & Real-Time)
```
┌─────────────────────────────────────────────────────────────────┐
│                      USER ACTION                                 │
│              (Opens Stock RELIANCE page)                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         ▼               ▼
    HTTP GET         WebSocket
    /api/stock/      /ws/prices
    RELIANCE         (subscribe)
         │               │
         │               ▼
         │          ┌─────────────────┐
         │          │ Redis Pub/Sub    │
         │          │ Channel:         │
         │          │ price:RELIANCE   │
         │          └────────┬─────────┘
         │                   │
         │          ┌────────┴──────────┐
         │          ▼                   ▼
         │      Listen for         WebSocket
         │      Updates          Push to Client
         │          │               │
         ▼          ▼               ▼
    ┌──────────────────────────────────────┐
    │  Redis Cache (hot data)               │
    │  - Current prices ({{ ticker }})      │
    │  - Technical indicators              │
    │  - Last update timestamp             │
    └──────────┬───────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    Return to    Stream to
    HTTP Client  WebSocket
    (0-10ms)     (real-time)
        │           │
        ▼           ▼
    ┌───────────────────────────┐
    │ Frontend State Update      │
    │ (instant, smooth)         │
    │ - Price: Live updates     │
    │ - Charts: Real-time plot  │
    │ - P&L: Calculated live    │
    └───────────────────────────┘

SOLUTION: Instant initial load (Redis cache),
          real-time updates via WebSocket,
          no polling needed,
          scales to 10k+ concurrent users
```

---

## 🔄 Data Pipeline (Recommended)

```
External Data Sources
│
├── YFinance (stock data)
├── Finnhub (news, company info)
├── NewsAPI (alternative news)
└── External APIs (earnings calendar, IPO data)
│
│ (Every 1 minute during market hours)
▼
┌─────────────────────────────────────┐
│  Celery Background Worker           │
│  Job: fetch_prices()                │
│                                     │
│  1. Call YFinance API               │
│  2. Parse responses                 │
│  3. Calculate indicators            │
│  4. Check alert triggers            │
│  5. Update databases                │
│  6. Publish to Redis pub/sub         │
└────────────┬────────────────────────┘
             │
             ├─── To PostgreSQL ──→ Historical Data
             │                      (OHLC, Technical)
             │
             ├─── To Redis ──────→ Cache Layer
             │                     (sub-100ms lookups)
             │
             ├─── Pub/Sub ──────→ WebSocket Handler
             │                    (broadcasts to users)
             │
             └─── Trigger ──────→ if Alert Matched
                                  → Send Email/Push
                                  → Log in Database

Frontend receives
└─ HTTP requests: served from Redis (cached)
└─ WebSocket: real-time updates from pub/sub
```

---

## 📈 System Performance Timeline

### Current System
```
Time │ RELIANCE Quote │ News Feed │ Portfolio │ Alerts
─────┼────────────────┼───────────┼──────────┼───────
0s   │ Request sent   │ Request   │ Request  │ Manual
1s   │ Waiting...     │ Waiting.. │ Loading  │ Check
2s   │ Waiting...     │ Waiting.. │ Loading  │ Only
3s   │ Waiting...     │ Waiting.. │ Loading  │ on
4s   │ Waiting...     │ Got data  │ Loading  │ Page
5s   │ Got price      │ Done (5s) │ Done (5s)│ Refresh
6s   │ Done (5s)      │           │          │
     │                │           │          │
Latency: 5 seconds per data source
Throughput: 1 user can overwhelm API
Real-time: Not possible (stale data)
Alerts: Manual checking only
```

### Target System (After Phase 6)
```
Time │ RELIANCE Quote │ News Feed │ Portfolio │ Alerts
─────┼────────────────┼───────────┼──────────┼───────
0s   │ Request sent   │ Request   │ Request  │ Active
0.1s │ Got price      │ Got news  │ Loaded   │ (running)
     │ (redis: 0.1s)  │ (cache)   │ (db)     │
0.2s │ WS: +0.05%     │ Stock: –  │ Refresh  │
0.3s │ WS: +0.06%     │           │ +$50 P&L │ Alert
0.4s │ WS: +0.07%     │           │ +10% YTD │ Triggered!
     │ WS: Chart plot │           │          │
     │
Latency: 100ms for initial load
Throughput: 10k+ concurrent users
Real-time: Updates every 100-200ms  
Alerts: Automatic (Celery job checks every minute)
Push: Email/SMS sent to user
```

---

## 🗂️ Database Schema Evolution

### Current
```sql
users ──→ watchlists ──→ portfolios ──→ stocks
                            │
                            └─→ sentiments
                            
Missing:
  - alerts
  - alert_triggers
  - ohlc_data
  - indicators
  - predictions
  - notifications
  - user_preferences
```

### After Phase 2 (Alerts)
```sql
users ─────────┬──→ watchlists
               ├──→ portfolios ──→ holdings
               ├──→ alerts ────→ alert_triggers
               │
stocks ───────┬──→ sentiments
              ├──→ news_articles
              └──→ price_history

New Tables:
  ✅ alerts
  ✅ alert_triggers  
  ✅ notifications
```

### After Phase 3 (Indicators & Real-Time)
```sql
stocks ───────┬──→ ohlc_data (historical)
              ├──→ indicators (pre-calculated)
              ├──→ technical_levels (support/resistance)
              └──→ current_prices (latest quote)

New Tables:
  ✅ ohlc_data
  ✅ indicators
  ✅ technical_levels
```

### Final (After Phase 6)
```sql
Complete stock trading database:
  - users (authentication)
  - portfolios (holdings)
  - alerts (price watchers)
  - stocks (company info)
  - ohlc_data (historical prices)
  - indicators (technical analysis)
  - news_articles (news feed)
  - sentiments (ML analysis)
  - predictions (AI forecasts)
  - earnings_calendar (earnings dates)
  - ipo_calendar (IPO tracking)
  - user_preferences (settings)
  - audit_log (changes tracking)
```

---

## 📱 Feature Rollout Timeline

```
Week  Phase           Completion   User Value
────  ──────────────  ──────────   ─────────────────────────
1-2   Foundation      ▓▓░░░░░░░░   Stable API (fixes bugs)
      ✅ Fixes bugs
      ✅ Error handling
      ✅ Tests

3-4   Alerts          ▓▓▓▓░░░░░░   Price Alerts Work!
      ✅ Alert creation
      ✅ Email alerts
      ✅ Auto-checking

5-6   Indicators      ▓▓▓▓▓▓░░░░   Technical Analysis
      ✅ SMA, RSI, MACD
      ✅ Real-time prices
      ✅ Interactive charts

7-8   Frontend        ▓▓▓▓▓▓▓▓░░   Beautiful Dashboard
      ✅ Stock charts
      ✅ Portfolio view
      ✅ Responsive design

9-10  AI Features     ▓▓▓▓▓▓▓▓▓░   Smart Recommendations
      ✅ Buy/Sell signals
      ✅ Stock screener
      ✅ Market dashboard

11-12 Deployment      ▓▓▓▓▓▓▓▓▓▓   Production Ready! 🚀
      ✅ Live on cloud
      ✅ SSL certificate
      ✅ Monitoring active
```

---

## 🎛️ Scaling Plan

```
Phase 1: MVP (200 users, 1 server)
┌──────────────────┐
│   Frontend       │
│  (Next.js)       │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
  Backend   Database
  (single)  (single)
  8000 port 5432

Phase 2: Growth (1k users, load balanced)
    ┌─────────┐
    │   CDN   │ (static assets)
    └─────────┘
         │
    ┌────┴────┐
    │Load     │
    │Balancer │
    └────┬────┘
         │
    ┌────┴──────┬──────┐
    ▼           ▼      ▼
  Backend    Backend   Cache
   (API)      (API)   (Redis)
    │          │        │
    └────┬─────┴────────┘
         ▼
      Database
      (PostgreSQL)

Phase 3: Scale (10k+ users, microservices)
    ┌────────────────────────────┐
    │   Kubernetes Cluster       │
    ├────────────────────────────┤
    │ Stock Service (3 pods)     │
    │ Sentiment Service (2 pods) │
    │ Prediction Service (2 pods)│
    │ Alert Service (2 pods)     │
    ├────────────────────────────┤
    │ Celery Workers (5 pods)    │
    │ RabbitMQ (HA)              │
    │ Redis Cluster              │
    │ PostgreSQL (Master-Slave)  │
    └────────────────────────────┘
```

---

## 🔑 Key Metrics to Track

```
Development Metrics:
  • Test coverage: Target 75-90%
  • Code quality: Zero critical issues
  • Build time: < 5 minutes
  • Deployment time: < 15 minutes

Performance Metrics:
  • API response time: p95 < 200ms
  • Database query time: p95 < 100ms
  • WebSocket latency: < 100ms
  • Page load time: < 2 seconds
  • Error rate: < 0.1%

Business Metrics:
  • User signups per week
  • Monthly active users
  • Feature adoption rate
  • Support tickets
  • System uptime: > 99.5%
```

---

## 🚨 Failure Points (What Could Go Wrong)

```
Current Risks:
  🔴 No alert system → Users can't trade profitably
  🔴 No error handling → Silent failures confuse users
  🔴 API keys exposed → Gets rate-limited/revoked
  🔴 In-memory cache → Data lost on restart
  🔴 No rate limiting → Vulnerable to spam
  🔴 No monitoring → Can't debug production issues
  🔴 No tests → Regressions break features

Mitigation:
  ✅ Build alerts first (Weeks 3-4)
  ✅ Implement error handling (Week 1)
  ✅ Move secrets to .env (immediate)
  ✅ Setup Redis (Week 3)
  ✅ Add rate limiting (Week 1)
  ✅ Setup monitoring (Week 1-2)
  ✅ Write tests (Week 2+)
```

---

## 📐 Request Flow Examples

### Example 1: Get Stock Quote (Simple HTTP)
```
Client Request:
GET /api/stock/INFY/quote
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Server Flow:
1. JWT Middleware: Verify token
2. Rate Limiter: Check if user exceeded limit
3. Stock Route Handler:
   a. Validate ticker (INFY)
   b. Check Redis cache
      ✅ Found → Return (0.1ms)
      ❌ Not found → Fetch YFinance (fetch_data(INFY))
   c. Parse response
   d. Save to Redis (5 min TTL)
   e. Return to client

Response (200 OK):
{
  "ticker": "INFY",
  "price": 1850.50,
  "change": 25.50,
  "change_percent": 1.40,
  "timestamp": "2026-04-01T10:30:00Z"
}

Timeline: 0.1ms (cached) or 3-5s (fresh)
```

### Example 2: Create Alert (With Background Job)
```
Client Request:
POST /api/alerts
{
  "ticker": "RELIANCE",
  "alert_type": "price",
  "trigger_value": 2850.00
}

Server Flow:
1. JWT: Verify user
2. Rate Limit: 10/min for POST
3. Validate: ticker format, price > 0
4. Database: INSERT INTO alerts
5. Return: 201 Created + alert_id
6. (Async) Celery picks up alert from RabbitMQ
7. Celery Job: Check every 1 minute if triggered
   - If triggered: Send email + log in alert_triggers
   - Mark: notification_status = 'sent'

Timeline:
  - HTTP Response: 100-200ms
  - First check: 60 seconds
  - Email delivery: 1-2 minutes
```

### Example 3: Real-Time Price Update (WebSocket)
```
Client WebSocket:
1. Opens WS connection: ws://localhost:8000/ws/prices
2. Sends subscription: {"action": "subscribe", "ticker": "RELIANCE"}
3. Listens for updates

Server Flow:
1. WebSocket Accept: handshake complete
2. Redis Subscribe: SUBSCRIBE price:RELIANCE
3. Waits for messages on Redis channel
4. When price updates arrive (from Celery job):
   a. Celery job publishes: PUBLISH price:RELIANCE {"price": 2850.05}
   b. WebSocket receives from Redis pub/sub
   c. Forwards to all connected clients for RELIANCE

Client Receives:
{
  "ticker": "RELIANCE",
  "price": 2850.05,
  "change": +0.05,
  "timestamp": "2026-04-01T10:30:00.123Z"
}

Frequency: Every 1 minute (or as often as data updates)
Latency: 100-200ms from price update to client
Clients: 10,000+ can subscribe (Redis pub/sub scales)
```

---

This visual guide helps understand:
- 🏗️ Current architecture (what exists)
- 🎯 Target architecture (where we're going)
- 📊 Data flows (how information moves)
- 📈 Performance improvements (what changes)
- 🔄 Feature rollout (when things launch)
- 📐 Technical examples (how it works)

**Use these diagrams when discussing architecture with your team or investors.**

---

Version 1.0 | Created April 1, 2026 | Stock Sentinel Architecture Team
