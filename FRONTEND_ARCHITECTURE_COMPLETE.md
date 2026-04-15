# Frontend Architecture - Complete Structure

## Overview
The frontend is a Next.js 14+ application with React components, built with TypeScript. It uses Zustand for global state management, Axios for API calls, and WebSocket for real-time data sync across tabs.

---

## 📁 Directory Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Home page (redirects to /dashboard or /login)
│   ├── globals.css               # Global styles
│   │
│   ├── (auth)/                   # Auth routes (protected)
│   ├── dashboard/
│   │   └── page.tsx              # Dashboard page with portfolio & market overview
│   ├── portfolio/
│   │   └── page.tsx              # Portfolio holdings, allocation, growth
│   ├── stocks/
│   │   └── [symbol]/
│   │       └── page.tsx          # Individual stock detail page with charts
│   ├── alerts/
│   │   └── page.tsx              # Create & manage price alerts
│   ├── watchlist/
│   │   └── page.tsx              # User's watchlist
│   ├── news/
│   │   └── page.tsx              # News feed
│   ├── trade-history/
│   │   └── page.tsx              # Trade history records
│   ├── profile/
│   ├── settings/
│   └── support/
│
├── components/
│   ├── alert-bootstrap.tsx       # [Bootstrap] Alert system & notifications
│   ├── session-bootstrap.tsx     # [Bootstrap] Auth session init
│   ├── auth/
│   │   ├── auth-shell.tsx
│   │   ├── login-form.tsx
│   │   └── register-form.tsx
│   ├── providers/
│   │   ├── data-sync-provider.tsx       # Primary data sync orchestrator
│   │   ├── data-sync-provider-v2.tsx    # Production-grade data sync
│   │   └── error-boundary-provider.tsx  # Global error boundary
│   ├── sentinel/                        # Core UI components
│   │   ├── shell.tsx                    # Main shell/layout with nav & ribbon
│   │   ├── optimized-ribbon.tsx         # Ticker tape component
│   │   ├── charts.tsx                   # Chart components (line, candlestick)
│   │   ├── primitives.tsx               # Reusable UI primitives
│   │   ├── protected-screen.tsx         # Route protection wrapper
│   │   └── error-boundary.tsx           # Local error boundary
│   └── ui/
│       └── toast.tsx                    # Toast notification component
│
├── hooks/                              # Custom React hooks
│   ├── useDataFetch.ts                 # Data fetching hooks from store
│   │   ├── useRibbonData()             # Get ribbon data from store
│   │   ├── useMarketData()             # Get market data from store
│   │   ├── useNewsData()               # Get news data from store with refetch
│   │   └── other data hooks
│   ├── useSafePolling.ts               # Basic safe polling (setTimeout-based)
│   ├── useSafePollingV2.ts             # Production-grade polling with WebSocket fallback
│   ├── useInterval.ts                  # Simple interval hook
│   ├── useAlertNotifications.ts        # Alert notifications
│   ├── useAlertsWS.ts                  # WebSocket alerts
│   ├── useWebSocket.ts                 # WebSocket connection
│   └── useWebSocketPrices.ts           # WebSocket price updates
│
├── lib/                                # Utilities & API client
│   ├── api-client.ts                   # Axios instance with interceptors
│   ├── api-service.ts                  # API endpoints organized by resource
│   ├── store-v2.ts                     # Zustand store (multi-tab sync)
│   ├── store.ts                        # Original store
│   ├── websocket-manager.ts            # Global WebSocket singleton
│   ├── multi-tab-lock.ts               # Tab focus lock for polling
│   ├── config.ts                       # Configuration
│   ├── auth.ts                         # Auth utilities
│   ├── types.ts                        # TypeScript types
│   ├── format.ts                       # Format utilities
│   ├── hooks.ts                        # Additional hooks
│   ├── logo.ts                         # Logo utilities
│   ├── sentinel-utils.ts               # Sentinel utilities
│   └── useInterval.ts                  # Alternative interval hook
│
├── .env.local                          # Local environment
├── .env.production                     # Production environment
├── .env.staging                        # Staging environment
└── next.config.mjs                     # Next.js config
```

---

## 🔄 Data Flow Architecture

### Top-Level Data Sync Flow
```
Root Layout (app/layout.tsx)
    ↓
    providers (ToastProvider)
    ↓
    DataSyncProvider (or DataSyncProviderV2)
        ├── WebSocket Manager (singleton)
        ├── Tab Lock
        ├── Safe Polling
        └── Store Sync (BroadcastChannel)
    ↓
    Child Components
        ├── Session Bootstrap
        ├── Alert Bootstrap
        └── Page Content
```

### Data Update Flow
```
WebSocket Connected? (Primary Tab?)
    ├─ YES → Real-time updates from WebSocket
    └─ NO  → Fall back to Safe Polling (every 5-30 seconds)
              ↓
              Polling suspended when tab is not visible
              ↓
              Exponential backoff on errors
              ↓
              Max 5 retries before stopping
              ↓
          Update Zustand Store
              ↓
          BroadcastChannel notifies other tabs
```

---

## 📡 API Services (lib/api-service.ts)

### Market Service
```typescript
export const marketService = {
  async getLiveRibbon()           // Get top movers ticker tape
  async getMarketSummary()        // Get market overview
  async getStockDetails(symbol, timeRange)  // Get price history & indicators
  async getStockPrice(symbol)     // Get current price
  async search(query)             // Search for stocks
}
```

### Portfolio Service
```typescript
export const portfolioService = {
  async list()                    // Get all holdings
  async summary()                 // Get portfolio summary (total value, gain/loss)
  async add(ticker, quantity, price)       // Add holding (BUY)
  async allocation()              // Get allocation by sector
  async growth(range: '1d'|'1w'|'1m'|'1y') // Get growth points for chart
  async remove(ticker)            // Remove holding (SELL)
}
```

### News Service
```typescript
export const newsService = {
  async global(limit)             // Get global news
  async bySymbol(symbol, limit)   // Get news for stock
  async withSentiment(symbol, limit)  // Get news with sentiment analysis
}
```

### Alert Service
```typescript
export const alertService = {
  async list()                    // Get all user alerts
  async create(payload)           // Create new alert
  async update(id, isActive)      // Toggle alert on/off
  async remove(id)                // Delete alert
}
```

### Watchlist Service
```typescript
export const watchlistService = {
  async list()                    // Get watchlist symbols
  async add(ticker)               // Add to watchlist
  async remove(ticker)            // Remove from watchlist
}
```

### Indicator Service
```typescript
export const indicatorService = {
  async combined(symbol)          // Get SMA, EMA, RSI for stock
}
```

### Auth Service
```typescript
export const authService = {
  async login(emailOrPhone, password)
  async register(email, password, fullName?, whatsappPhone?)
  async me()                      // Get current user profile
  async updateMe(fullName?)       // Update profile
}
```

---

## 🪝 Custom Hooks

### Data Fetching Hooks (hooks/useDataFetch.ts)
These hooks read from the Zustand store - they don't fetch directly:

```typescript
useRibbonData()                 // Returns: { ribbon, ribbonLoading, ribbonError }
useMarketData()                 // Returns: { market, marketLoading, marketError }
useNewsData(limit)              // Returns: { news, newsLoading, newsError, refetch() }
```

### Polling Hooks

#### useSafePolling.ts (Basic)
```typescript
useSafePolling(pollFn, {
  interval,                       // Poll interval in ms
  enabled,                        // Whether to poll
  onError,                        // Error callback
  onSuccess,                      // Success callback
  maxRetries,                     // Default: 3
  retryDelay                      // Default: 1000ms
})
```
Features:
- Uses `setTimeout` instead of `setInterval`
- Prevents overlapping calls
- Respects `document.hidden` (pauses when tab not visible)
- AbortController for cancellation
- Prevents state updates after unmount

#### useSafePollingV2.ts (Production-Grade)
```typescript
useSafePollingV2({
  url: string,                    // API endpoint to poll
  onData?: (data: any) => void,   // Data handler
  onError?: (error: Error) => void,
  interval?: number,              // Default: config.POLLING_INTERVAL
  maxRetries?: number,            // Default: 5
  shouldPoll?: () => boolean      // Custom poll condition
})
```
Features:
- **Only polls when WebSocket is disconnected** ✅
- 5-second timeout per request ✅
- Exponential backoff on errors
- Max 5 retries (prevents infinite loops)
- Data change detection (skips redundant updates)
- Respects polling suspension
- Structured logging with [POLL] prefix
- Document visibility detection

### Interval Hook
```typescript
useInterval(callback, delay)    // Simple setInterval wrapper
```
- Params update trigger re-registration
- Auto cleanup on unmount

### WebSocket Hooks
```typescript
useWebSocket()                  // General WebSocket connection
useWebSocketPrices()            // Price updates via WebSocket
useAlertsWS()                   // Alert notifications via WebSocket
useAlertNotifications()         // Alert UI notifications
```

---

## 🗄️ State Management

### Zustand Store v2 (lib/store-v2.ts) - PRODUCTION
```typescript
interface MarketStoreState {
  // Data
  ribbon: LiveQuote[]
  market: MarketSummary | null
  news: NewsArticle[]
  ribbonTimestamp: number          // Stale data protection
  marketTimestamp: number
  newsTimestamp: number

  // Loading states (only on initial load)
  isRibbonLoading: boolean
  isMarketLoading: boolean
  isNewsLoading: boolean

  // Error states
  ribbonError: string | null
  marketError: string | null
  newsError: string | null

  // WebSocket & Polling status
  isWebSocketConnected: boolean
  isPollingActive: boolean
  isPollingSuspended: boolean
  lastUpdateSource: 'websocket' | 'polling' | 'manual'

  // Metadata
  syncAcrossTabs: boolean

  // Methods
  setRibbon(data, source?)        // Updates data + timestamp
  setMarket(data, source?)
  setNews(data, source?)
  setWebSocketConnected(connected)
  suspendPolling() / resumePolling()
  isStaleData(type, maxAge?)      // Check data freshness
}
```

Features:
- Persistent with `localStorage`
- Multi-tab sync via `BroadcastChannel`
- Stale data protection (timestamps)
- Error tracking
- WebSocket/polling status

### Auth Store
- Login/logout
- Token management
- Session hydration

---

## 🔗 WebSocket & Polling Orchestration

### WebSocket Manager (lib/websocket-manager.ts)
```typescript
class GlobalWebSocketManager {
  // Singleton pattern - only ONE connection globally
  static getInstance()
  
  connect()                       // Establish connection
  disconnect()                    // Cleanup
  isConnected(): boolean
  
  onMessage(type, handler)        // Register message handlers
  send(type, data)                // Send message
  
  // Auto-reconnect with exponential backoff
  // 3-second fallback delay before polling starts
  // Heartbeat/ping-pong mechanism
}
```

### Tab Lock (lib/multi-tab-lock.ts)
Ensures only the primary (foreground) tab polls:
```typescript
getTabLock()                    // Returns tab lock instance
useTabLock()                    // React hook to check if primary
```

Rules:
- Only foreground tab polls (primary)
- Other tabs read from store (synced via BroadcastChannel)
- If primary tab closes, next tab becomes primary
- Prevents duplicate API requests

### Data Sync Provider (components/providers/data-sync-provider-v2.tsx)
```
RibbonPolling Component
├─ Check if primary tab
├─ If yes: Poll /stocks/top-movers every ~5s
└─ Update store with response
  
MarketPolling Component
├─ Check if primary tab
├─ If yes: Poll /stocks/market-summary/overview
└─ Update store
  
[Similar for News, Portfolio, etc.]
```

---

## 📄 Page Components

### Dashboard (app/dashboard/page.tsx)
- **Displays**: Portfolio value, market summary, news
- **Data Sources**: 
  - Portfolio from `api.get('/dashboard/portfolio')`
  - News from `api.get('/dashboard/news')`
  - Market from store (real-time synced)
- **Charts**: Portfolio growth (line chart)
- **Features**: Range selector (1D, 1W, 1M, 1Y)

### Portfolio (app/portfolio/page.tsx)
- **Displays**: Holdings table, allocation pie chart, growth chart
- **Data Sources**:
  - `portfolioService.list()` - holdings
  - `portfolioService.allocation()` - sector allocation
  - `portfolioService.growth(range)` - historical growth
- **Features**:
  - Add/remove holdings
  - Symbol autocomplete search
  - Export to CSV
  - Range selector

### Stocks Detail (app/stocks/[symbol]/page.tsx)
- **Displays**: Price chart, indicators (SMA, EMA, RSI), news
- **Data Sources**:
  - `marketService.getStockDetails(symbol, range)` - price history
  - `indicatorService.combined(symbol)` - technical indicators
  - `newsService.bySymbol(symbol)` - related news
- **Features**:
  - Interactive price chart (line/candlestick)
  - Indicator overlays
  - Hover to see price at point in time

### Alerts (app/alerts/page.tsx)
- **Displays**: Alert list, create alert form
- **Data Sources**:
  - `alertService.list()` - user alerts
  - `marketService.getLiveRibbon()` - for symbol autocomplete
- **Features**:
  - Create alerts (price, % change, volume spike, crash)
  - Toggle alerts on/off
  - Delete alerts

### Watchlist (app/watchlist/page.tsx)
- **Displays**: Watch symbols with prices and changes
- **Data Sources**:
  - `watchlistService.list()` - symbol list
  - `marketService.getStockPrice(ticker)` - for each symbol
  - `marketService.getMarketSummary()` - context
- **Features**:
  - Add/remove symbols
  - Real-time price updates

### News (app/news/page.tsx)
- **Data Sources**: `newsService.global(limit)`
- **Features**: News feed with sentiment

### Trade History (app/trade-history/page.tsx)
- **Data Sources**: `api.get('/trades')` (confirmed from trade submissions)
- **Displays**: Trade record table

---

## 🎯 Key Components

### SentinelShell (components/sentinel/shell.tsx)
Main application shell containing:
- **Left Sidebar**: Navigation menu with icons
  - Dashboard, Stocks, Portfolio, Watchlist, Alerts, Trades, News, Support, Settings
- **Top Navigation**: Quick-trade modal, search
- **Ribbon**: Live ticker tape (top movers)
- **Content Area**: Page content
- **Quick Trade Modal**: Buy/sell with validation

### OptimizedRibbon (components/sentinel/optimized-ribbon.tsx)
- Seamless infinite scrolling ticker
- Real-time price updates
- Click to navigate to stock details
- Colors: Green for gains, Red for losses

### Charts (components/sentinel/charts.tsx)
- **SentinelLineChart**: SVG-based line chart with indicators
  - Hover shows price at point
  - Indicator overlays (SMA, EMA, RSI)
- **AllocationDonut**: Pie chart for portfolio allocation

### Protected Screen (components/sentinel/protected-screen.tsx)
- Route protection wrapper
- Checks authentication before rendering
- Redirects to login if not authenticated

### Error Boundary (components/sentinel/error-boundary.tsx)
- Catches React errors
- Displays fallback UI
- Prevents full page crash

---

## 🔐 Authentication Flow

```
User lands on /
  ↓
useAuthStore checks if token exists
  ├─ Token found → Redirect to /dashboard
  └─ No token → Redirect to /login
  
Login form:
  1. User enters email/password
  2. POST /auth/login-json
  3. Server returns token
  4. Store in localStorage as "stocksentinel_token"
  5. Redirect to /dashboard

API requests:
  All requests include: Authorization: Bearer {token}
  If 401 response → Clear token, redirect to /login
```

---

## ⚡ Real-Time Features

### WebSocket Connection
- Connects in `DataSyncProvider`
- Listens for:
  - `ribbon` updates
  - `market` updates
  - `news` updates
  - `alert` notifications

### Polling Fallback
When WebSocket disconnects:
1. **Primary Tab**: Switches to polling
   - `/stocks/top-movers` → ribbon
   - `/stocks/market-summary/overview` → market
   - Other endpoints as needed
2. **Secondary Tabs**: Continue reading from store
3. **Reconnection**: Auto-reconnect with exponential backoff

### Tab Coordination
- Primary tab has exclusive polling rights
- If closed, next tab becomes primary
- All tabs stay synced via `BroadcastChannel` + `localStorage`

---

## 🛠️ Configuration (lib/config.ts)

```typescript
{
  API_BASE_URL: string
  POLLING_INTERVAL: number        // 5000ms typical
  WS_RECONNECT_ATTEMPTS: number   // 5
  WS_RECONNECT_DELAY: number      // exponential backoff
  STALE_DATA_MAX_AGE: number      // 30000ms
  // ... more config
}
```

---

## 📦 Dependencies

**Key packages:**
- `next` - React framework
- `react` - UI library
- `zustand` - State management
- `axios` - HTTP client
- `react-tooltip` - Tooltips
- `tailwindcss` - Styling

---

## 🔍 Common Patterns

### Read Data from Store
```typescript
const ribbon = useMarketStore((state) => state.ribbon);
const ribbonLoading = useMarketStore((state) => state.isRibbonLoading);
```

### Fetch Data Once on Mount
```typescript
useEffect(() => {
  let isMounted = true;
  
  const loadData = async () => {
    try {
      const data = await apiService.fetch();
      if (isMounted) setState(data);
    } catch (error) {
      if (isMounted) setError(error);
    }
  };
  
  loadData();
  return () => { isMounted = false; };
}, []);
```

### Safe Polling
```typescript
useSafePollingV2({
  url: '/api/endpoint',
  onData: (data) => setData(data),
  onError: (error) => console.error(error),
  interval: 5000,
  shouldPoll: () => isPrimaryTab
});
```

---

## 📊 Summary Table

| Feature | File | Purpose |
|---------|------|---------|
| **State** | `store-v2.ts` | Global market data + sync |
| **API** | `api-client.ts` | Axios instance |
| **Endpoints** | `api-service.ts` | Organized API calls |
| **Polling** | `useSafePollingV2.ts` | Production polling |
| **WebSocket** | `websocket-manager.ts` | Real-time connection |
| **Tab Sync** | `multi-tab-lock.ts` | Primary tab selection |
| **Provider** | `data-sync-provider-v2.tsx` | Orchestration |
| **Dashboard** | `app/dashboard/page.tsx` | Portfolio overview |
| **Stocks** | `app/stocks/[symbol]/page.tsx` | Stock details + chart |
| **Portfolio** | `app/portfolio/page.tsx` | Holdings mgmt |
| **Alerts** | `app/alerts/page.tsx` | Alert management |

---

## 🚀 Performance Optimizations

1. **Request Deduplication**: API client caches GET requests for 2 seconds
2. **Tab Coordination**: Polling only happens in primary tab
3. **Suspension**: Polling pauses when tab is not visible
4. **Change Detection**: Only updates UI if data actually changed
5. **Component Memoization**: Charts and ribbons use refs to avoid re-renders
6. **Lazy Loading**: Pages/components code-split by route
7. **CSS**: Tailwind preprocessed for minimal bundle

---

## 📝 Notes

- All polling includes retry logic and backoff strategies
- WebSocket failures gracefully fall back to HTTP polling
- Stale data is tracked with timestamps to ensure freshness
- Error states are preserved to inform users of issues
- Multi-tab sync is critical for user experience across browser instances
