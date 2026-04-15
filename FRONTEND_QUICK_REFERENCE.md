# Frontend - Quick Reference Guide

## 🎯 Find Features Quickly

### I need to find...

#### Dashboard Display
**File**: [app/dashboard/page.tsx](app/dashboard/page.tsx)
- Portfolio summary
- Market overview
- Portfolio growth chart (1D, 1W, 1M, 1Y)
- Recent news
- Uses: `useMarketStore()`, `portfolioService`

#### Portfolio Management
**File**: [app/portfolio/page.tsx](app/portfolio/page.tsx)
- Holdings table
- Sector allocation pie chart
- Growth line chart
- Add/remove holdings
- Export to CSV
- Symbol search with autocomplete
- Uses: `portfolioService`, `marketService`

#### Stock Detail Page with Charts
**File**: [app/stocks/[symbol]/page.tsx](app/stocks/[symbol]/page.tsx)
- Price chart (line/candlestick)
- Technical indicators (SMA, EMA, RSI)
- Related news
- Uses: `marketService.getStockDetails()`, `indicatorService`

#### Alert Management
**File**: [app/alerts/page.tsx](app/alerts/page.tsx)
- Create price alerts
- Alert types: price, %, volume spike, crash
- Toggle alerts on/off
- Delete alerts
- Uses: `alertService`

#### Watchlist
**File**: [app/watchlist/page.tsx](app/watchlist/page.tsx)
- Watch symbols with live prices
- Add/remove symbols
- Uses: `watchlistService`, `marketService`

#### Navigation & Shell
**File**: [components/sentinel/shell.tsx](components/sentinel/shell.tsx)
- Main app layout
- Sidebar navigation (9 items)
- Quick-trade modal (buy/sell)
- Ribbon ticker
- Uses: `OptimizedRibbon`, `QuickTradeModal`

#### Live Ticker Tape
**File**: [components/sentinel/optimized-ribbon.tsx](components/sentinel/optimized-ribbon.tsx)
- Seamless infinite scrolling
- Real-time top movers
- Click to navigate to stock detail
- Uses: `useMarketStore()` for ribbon data
- Data from: Polling or WebSocket

#### Chart Drawing
**File**: [components/sentinel/charts.tsx](components/sentinel/charts.tsx)
- SVG-based line chart
- Candlestick chart support
- Indicator overlays
- Hover interactions
- Portfolio allocation donut

---

## 🔌 API Integration Points

### Where APIs are called

#### Market Data Polling
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: [components/providers/data-sync-provider-v2.tsx](components/providers/data-sync-provider-v2.tsx)

```typescript
marketService.getLiveRibbon()        // Top movers (every 5s)
marketService.getMarketSummary()     // Market overview (every 5s)
```

#### Portfolio Data
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: Components in `useEffect`

```typescript
portfolioService.list()              // Holdings
portfolioService.summary()           // Summary stats
portfolioService.allocation()        // Sector allocation
portfolioService.growth(range)       // Historical growth
portfolioService.add(ticker, qty, price)    // BUY
portfolioService.remove(ticker)     // SELL
```

#### Stock Details & Indicators
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: [app/stocks/[symbol]/page.tsx](app/stocks/[symbol]/page.tsx)

```typescript
marketService.getStockDetails(symbol, range)  // Price + history
indicatorService.combined(symbol)             // SMA, EMA, RSI
```

#### News
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: Components

```typescript
newsService.global()                // Global news
newsService.bySymbol(symbol)        // Stock-specific news
newsService.withSentiment(symbol)   // News with sentiment
```

#### Alerts
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: [app/alerts/page.tsx](app/alerts/page.tsx)

```typescript
alertService.list()                 // Get alerts
alertService.create(payload)        // Create alert
alertService.update(id, isActive)   // Enable/disable
alertService.remove(id)             // Delete alert
```

#### Watchlist
**File**: [lib/api-service.ts](lib/api-service.ts)
**Called by**: [app/watchlist/page.tsx](app/watchlist/page.tsx)

```typescript
watchlistService.list()             // Get symbols
watchlistService.add(ticker)        // Add symbol
watchlistService.remove(ticker)     // Remove symbol
```

---

## 🔄 Polling & Real-Time Updates

### Where polling is configured

#### Safe Polling Hook (Production)
**File**: [hooks/useSafePollingV2.ts](hooks/useSafePollingV2.ts)

Features:
- 5-second timeout per request
- Max 5 retries with exponential backoff
- Respects tab visibility
- Data change detection
- Structured logging [POLL] prefix

Usage:
```typescript
useSafePollingV2({
  url: '/api/endpoint',
  onData: (data) => updateStore(data),
  interval: 5000,
  shouldPoll: () => isPrimaryTab
})
```

#### Data Sync Provider (Orchestrator)
**File**: [components/providers/data-sync-provider-v2.tsx](components/providers/data-sync-provider-v2.tsx)

Handles:
- Ribbon polling every 5s
- Market polling every 5s
- News polling every 30s
- WebSocket connection setup
- Tab lock coordination

#### WebSocket Manager (Global)
**File**: [lib/websocket-manager.ts](lib/websocket-manager.ts)

Features:
- Singleton pattern (one connection per browser)
- Auto-reconnect with exponential backoff
- Heartbeat/ping-pong mechanism
- 3-second fallback before polling starts
- Message type routing

#### Multi-Tab Lock
**File**: [lib/multi-tab-lock.ts](lib/multi-tab-lock.ts)

Purpose:
- Determines if current tab is primary
- Only primary tab polls
- Prevents duplicate API calls

Usage:
```typescript
const isPrimary = useTabLock()
const tabLock = getTabLock()
```

---

## 🗄️ State Management

### Zustand Store v2
**File**: [lib/store-v2.ts](lib/store-v2.ts)

Data:
- `ribbon` - Top movers
- `market` - Market summary
- `news` - News articles
- Timestamps for staleness check
- Loading/error states

Features:
- localStorage persistence
- BroadcastChannel multi-tab sync
- Selective subscriptions (useMarketStore)

Usage:
```typescript
const ribbon = useMarketStore((state) => state.ribbon)
const { setRibbon } = useMarketStore((state) => state)
const isStale = useMarketStore((state) => 
  state.isStaleData('ribbon', 30000)
)
```

### Auth Store
**File**: [lib/auth.ts](lib/auth.ts)

- Token management
- Login/logout
- Session hydration
- Redirect on 401

---

## 🪝 Custom Hooks

### Data Fetching Hooks
**File**: [hooks/useDataFetch.ts](hooks/useDataFetch.ts)

```typescript
useRibbonData()         // { ribbon, loading, error }
useMarketData()         // { market, loading, error }
useNewsData(limit)      // { news, loading, error, refetch() }
```

### Polling Hooks
**File**: [hooks/useSafePollingV2.ts](hooks/useSafePollingV2.ts)
**File**: [hooks/useSafePolling.ts](hooks/useSafePolling.ts)

### WebSocket Hooks
**File**: [hooks/useWebSocket.ts](hooks/useWebSocket.ts)
**File**: [hooks/useWebSocketPrices.ts](hooks/useWebSocketPrices.ts)
**File**: [hooks/useAlertsWS.ts](hooks/useAlertsWS.ts)

### Alert Notifications
**File**: [hooks/useAlertNotifications.ts](hooks/useAlertNotifications.ts)

### Interval Hook
**File**: [lib/useInterval.ts](lib/useInterval.ts)

Simple interval wrapper:
```typescript
useInterval(callback, delay)
// Auto-cleanup on unmount
```

---

## 🔗 HTTP Client Configuration

### Axios Instance
**File**: [lib/api-client.ts](lib/api-client.ts)

Features:
- Automatic token injection
- Request deduplication (2s cache)
- 401 redirect to login
- Base URL configuration

### API Service Export
**File**: [lib/api-service.ts](lib/api-service.ts)

Exports:
- `authService`
- `marketService`
- `portfolioService`
- `newsService`
- `alertService`
- `watchlistService`
- `indicatorService`
- `profileService`

---

## 🎨 UI Components

### Main Components
**File**: [components/sentinel/shell.tsx](components/sentinel/shell.tsx)
- Main layout wrapper
- Navigation sidebar
- Quick-trade modal
- Ribbon ticker

**File**: [components/sentinel/charts.tsx](components/sentinel/charts.tsx)
- Line chart (SVG)
- Candlestick chart
- Allocation donut chart

**File**: [components/sentinel/primitives.tsx](components/sentinel/primitives.tsx)
- Reusable UI components
- Skeleton loaders
- Stat chips
- Icons

**File**: [components/sentinel/protected-screen.tsx](components/sentinel/protected-screen.tsx)
- Route protection
- Auth requirement check

**File**: [components/sentinel/optimized-ribbon.tsx](components/sentinel/optimized-ribbon.tsx)
- Ticker tape
- Real-time updates

## 🚀 Performance Optimizations

### Where they're implemented

#### Request Deduplication
**File**: [lib/api-client.ts](lib/api-client.ts)
- 2-second cache for GET requests
- Prevents duplicate calls

#### Tab Coordination
**File**: [lib/multi-tab-lock.ts](lib/multi-tab-lock.ts)
- Only primary tab polls
- Saves bandwidth

#### Tab Synchronization
**File**: [lib/store-v2.ts](lib/store-v2.ts)
- BroadcastChannel for sync
- localStorage for persistence

#### Change Detection
**File**: [hooks/useSafePollingV2.ts](hooks/useSafePollingV2.ts)
- Deep equality check
- Only updates if data changed

#### Component Optimization
**File**: [components/sentinel/charts.tsx](components/sentinel/charts.tsx)
- useRef for hover state (no re-renders)

**File**: [components/sentinel/optimized-ribbon.tsx](components/sentinel/optimized-ribbon.tsx)
- Selector-based subscriptions
- Minimal re-renders

---

## 🔐 Authentication

### Auth Flow
**Files**:
- [app/(auth)/...](app/)
- [components/auth/login-form.tsx](components/auth/login-form.tsx)
- [lib/auth.ts](lib/auth.ts)
- [lib/api-client.ts](lib/api-client.ts)

Flow:
1. User lands on / → redirects to /dashboard or /login
2. Login form POSTs to `/auth/login-json`
3. Token stored in localStorage
4. All requests include: `Authorization: Bearer {token}`
5. 401 → Clear token, redirect to /login

---

## 🔍 Type Definitions

**File**: [lib/types.ts](lib/types.ts)

Key types:
- `LiveQuote` - Current stock price
- `MarketSummary` - Market overview
- `PortfolioHolding` - Stock in portfolio
- `PortfolioSummary` - Portfolio stats
- `NewsArticle` - News item
- `AlertItem` - Price alert
- `CombinedIndicators` - Technical indicators
- `StockDetails` - Full stock info
- Many more...

---

## 📊 Configuration

**File**: [lib/config.ts](lib/config.ts)

Key configs:
- `API_BASE_URL` - Backend URL
- `POLLING_INTERVAL` - 5000ms typical
- `WS_RECONNECT_ATTEMPTS` - 5
- `WS_RECONNECT_DELAY` - Exponential
- `STALE_DATA_MAX_AGE` - 30000ms

---

## 🐛 Error Handling

### Global Error Handling
**File**: [components/sentinel/error-boundary.tsx](components/sentinel/error-boundary.tsx)
- Catches React errors
- Displays fallback UI

**File**: [components/providers/error-boundary-provider.tsx](components/providers/error-boundary-provider.tsx)
- Provider-level error boundary

### API Error Handling
**File**: [lib/api-client.ts](lib/api-client.ts)
- 401 → Redirect to login
- Other errors → Propagate to component

### Polling Error Handling
**File**: [hooks/useSafePollingV2.ts](hooks/useSafePollingV2.ts)
- Store in component state
- Display error message
- Retry with backoff

---

## 📝 Bootstrap Components

### Session Bootstrap
**File**: [components/session-bootstrap.tsx](components/session-bootstrap.tsx)
- Initializes user session
- Validates token
- Sets up filters

### Alert Bootstrap
**File**: [components/alert-bootstrap.tsx](components/alert-bootstrap.tsx)
- WebSocket alert listener
- Toast notifications
- Sound alerts (optional)

---

## 🎯 Feature Location Cheat Sheet

| Feature | Main File | Related Files |
|---------|-----------|---------------|
| Dashboard display | app/dashboard/page.tsx | store-v2.ts, api-service.ts |
| Portfolio management | app/portfolio/page.tsx | portfolioService |
| Stock charts | app/stocks/[symbol]/page.tsx | charts.tsx, indicatorService |
| Alerts system | app/alerts/page.tsx | alertService, useAlertsWS |
| Watchlist | app/watchlist/page.tsx | watchlistService |
| Live ribbon | components/sentinel/optimized-ribbon.tsx | store-v2.ts |
| Navigation | components/sentinel/shell.tsx | Quick-trade modal |
| Real-time polling | hooks/useSafePollingV2.ts | data-sync-provider-v2.tsx |
| WebSocket | lib/websocket-manager.ts | useWebSocket hooks |
| Tab sync | lib/multi-tab-lock.ts | store-v2.ts |
| API calls | lib/api-service.ts | api-client.ts |
| State management | lib/store-v2.ts | Zustand + BroadcastChannel |
| Authentication | lib/auth.ts | app/(auth), api-client |

---

## 🚀 Deployment Files

**Docker**: [Dockerfile](Dockerfile)
**Environment**: [.env.production](.env.production), [.env.staging](.env.staging)
**Config**: [next.config.mjs](next.config.mjs)
**Build**: `npm run build` → outputs `.next/`

---

## 📚 Documentation Files

- [FRONTEND_DOCUMENTATION.md](FRONTEND_DOCUMENTATION.md) - Comprehensive docs
- [FRONTEND_OPTIMIZATION_COMPLETE.md](FRONTEND_OPTIMIZATION_COMPLETE.md) - Performance info
- [POLLING_SETUP_GUIDE.md](POLLING_SETUP_GUIDE.md) - How polling works

