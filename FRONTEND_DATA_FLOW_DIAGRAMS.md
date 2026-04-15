# Frontend Polling & Data Flow - Visual Diagrams

## 1. Component Hierarchy & Data Flow

```
RootLayout (app/layout.tsx)
│
├─ ToastProvider
│  └─ DataSyncProviderV2
│     ├─ RibbonPolling (Component)
│     ├─ MarketPolling (Component)
│     ├─ NewsPolling (Component)
│     ├─ SessionBootstrap
│     ├─ AlertBootstrap
│     │
│     └─ {children}
│        ├─ AuthLayout / (auth)/page.tsx
│        │  ├─ LoginForm
│        │  └─ RegisterForm
│        │
│        ├─ DashboardPage (/dashboard)
│        │  ├─ SentinelShell
│        │  │  ├─ OptimizedRibbon (ribbon from store)
│        │  │  └─ Sidebar Navigation
│        │  └─ Dashboard content
│        │
│        ├─ PortfolioPage (/portfolio)
│        │  ├─ SentinelShell
│        │  ├─ Holdings Table
│        │  ├─ AllocationDonut Chart
│        │  ├─ Growth LineChart
│        │  └─ Add Holding Form
│        │
│        ├─ StockDetailPage (/stocks/[symbol])
│        │  ├─ SentinelShell
│        │  ├─ SentinelLineChart (price + indicators)
│        │  ├─ Technical Indicators Panel
│        │  └─ News Section
│        │
│        ├─ AlertsPage (/alerts)
│        │  ├─ SentinelShell
│        │  ├─ Alerts Table
│        │  └─ Create Alert Form
│        │
│        ├─ WatchlistPage (/watchlist)
│        │  ├─ SentinelShell
│        │  ├─ Watchlist Table
│        │  └─ Add Symbol Form
│        │
│        └─ [Other pages: news, trade-history, etc.]
```

---

## 2. Data Sync Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser Window / Tab                          │
└─────────────────────────────────────────────────────────────────┘
                            ↑
                            │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
    ┌────────────────────────────────────┐   ┌─────────────────┐
    │   Zustand Store (store-v2.ts)      │   │  localStorage   │
    │                                    │   │  (persistence)  │
    │  • ribbon: LiveQuote[]             │   │                 │
    │  • market: MarketSummary           │   │  "ribbon"       │
    │  • news: NewsArticle[]             │   │  "market"       │
    │  • timestamps                      │   │  "news"         │
    │  • loading/error states            │   │  "ws_status"    │
    │  • ws_connected: boolean           │   │  "poll_active"  │
    │  • poll_suspended: boolean         │   │                 │
    └────────────────────────────────────┘   └─────────────────┘
        ↑                                ↑
        │                                │
        │         Updates from:          │
        │                                │
    ┌───┴────────────────────────────────┴───┐
    │                                        │
    ├─ WebSocket (Real-time, if connected)  │
    │  └─ /ws endpoint                       │
    │     ├─ ribbon messages                 │
    │     ├─ market messages                 │
    │     ├─ news messages                   │
    │     └─ alert notifications             │
    │                                        │
    ├─ HTTP Polling (Fallback)               │
    │  └─ Primary tab only                   │
    │     ├─ GET /stocks/top-movers (ribbon) │
    │     ├─ GET /stocks/market-summary      │
    │     ├─ GET /news                       │
    │     └─ etc.                            │
    │                                        │
    └─ BroadcastChannel (Tab Sync)           │
       └─ Broadcasts store updates           │
          to other browser tabs              │
```

---

## 3. Polling Decision Tree

```
┌──────────────────────────────────┐
│  Application Starts              │
└──────────────┬───────────────────┘
               │
               ↓
    ┌──────────────────────┐
    │ WebSocket Manager    │
    │ Connects to /ws      │
    └──────────┬───────────┘
               │
        ┌──────┴─────┐
        │            │
    ✓ SUCCESS   ✗ FAILED
        │            │
        ↓            │
    ┌───────┐    ┌───────────────────────────┐
    │ OPEN  │    │ Wait 3 seconds (fallback) │
    └───┬───┘    └───────────┬───────────────┘
        │                    │
        │                    ↓
        │         ┌──────────────────────┐
        │         │ Is this Primary Tab? │
        │         └──────┬────────────────┘
        │                │
    NO POLLING   YES     │
    (all data via        ↓
     WebSocket)   ┌────────────────────────────────────┐
                  │ Start Polling                      │
                  │ • /stocks/top-movers (5s)         │
                  │ • /stocks/market-summary (5s)     │
                  │ • /news (30s)                     │
                  │ • /portfolio/* (on demand)        │
                  └────────┬───────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ✓ SUCCESS      ✗ ERROR
                    │             │
                    ↓             ↓
            ┌──────────────┐  ┌──────────────┐
            │ Store data   │  │ Exponential  │
            │ BroadCast    │  │ Backoff +    │
            │ to other tabs│  │ Retry        │
            └──────────────┘  │ (max 5x)     │
                               └──────┬───────┘
                                      │
                              ┌───────┴────────┐
                              │                │
                       Exceeded Retries        │
                              │                │
                              ↓                │
                        ┌────────────┐         │
                        │ Stop       │         │
                        │ Polling    │         │
                        │ (error     │         │
                        │ state)     │         │
                        └────────────┘         │
                                              │
                                      Resume Next Poll
                                      
Tab Visibility Check:
┌──────────────────────────────┐
│ Is tab visible?              │
└──────┬───────────────────────┘
       │
    ├─ YES → Continue polling
    └─ NO  → Suspend polling (pause)
             Resume when visible again
```

---

## 4. API Service Call Hierarchy

```
Components (Pages/UI)
    │
    ├─ useSafePollingV2
    │  └─ marketService.getLiveRibbon()        → GET /api/stocks/top-movers
    │
    ├─ useSafePollingV2
    │  └─ marketService.getMarketSummary()     → GET /api/stocks/market-summary/overview
    │
    ├─ useSafePollingV2
    │  └─ newsService.global()                 → GET /api/news
    │
    └─ Component Mounts (useEffect)
       ├─ portfolioService.list()              → GET /api/portfolio
       ├─ portfolioService.summary()           → GET /api/portfolio/summary
       ├─ portfolioService.allocation()        → GET /api/portfolio/allocation
       ├─ portfolioService.growth('1d'|'1w'|'1m'|'1y') → GET /api/portfolio/growth
       │
       ├─ marketService.getStockDetails(symbol, range)  → GET /api/stocks/{symbol}
       ├─ marketService.getStockPrice(symbol) → GET /api/stocks/{symbol}/price
       │
       ├─ newsService.bySymbol(symbol)        → GET /api/news/{symbol}
       ├─ newsService.withSentiment(symbol)   → GET /api/news/{symbol}/sentiment
       │
       ├─ indicatorService.combined(symbol)   → GET /api/indicators/combined
       │
       ├─ watchlistService.list()             → GET /api/watchlist
       │
       ├─ alertService.list()                 → GET /api/alerts
       │
       └─ Search / Autocomplete
          └─ marketService.search(query)      → GET /api/search

    ↓
    api-service.ts (exports services)
    │
    ↓
    api-client.ts
    │
    ├─ Token Injection (Authorization header)
    ├─ Request Deduplication (2s cache)
    └─ 401 Response Handling (redirect to login)
    
    ↓
    Axios Instance
    │
    ↓
    HTTP GET/POST/PATCH/DELETE to Backend
```

---

## 5. useRibbonData Hook Flow

```
Component Code:
┌─────────────────────────────────────────────────────┐
│ const { ribbon, ribbonLoading, ribbonError } =      │
│   useRibbonData();                                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│ hooks/useDataFetch.ts                               │
│                                                     │
│ export function useRibbonData() {                   │
│   const ribbon = useMarketStore(state =>            │
│     state.ribbon                                    │
│   );                                                │
│   return { ribbon, ... };                           │
│ }                                                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓ (Reading from store)
┌─────────────────────────────────────────────────────┐
│ lib/store-v2.ts                                     │
│                                                     │
│ ribbon: LiveQuote[] = [                             │
│   { symbol: "AAPL", price: 192.50, ... },           │
│   { symbol: "MSFT", price: 420.25, ... },           │
│   ...                                               │
│ ]                                                   │
└─────────────────────────────────────────────────────┘

Data Updated When:
1. WebSocket message received
   ├─ Type: "ribbon"
   └─ Handler updates store

2. OR Polling response received
   ├─ useSafePollingV2 calls getLiveRibbon()
   └─ Updates store via setRibbon()

3. OR Manual update from component
   └─ Rarely used, usually for refetch
```

---

## 6. Multi-Tab Synchronization

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser                                  │
├─────────────────────────┬──────────────────────────┬────────────┤
│      TAB 1              │      TAB 2               │   TAB 3    │
│   (Primary Tab)         │   (Secondary)            │ (Minimized)│
│                         │                          │            │
│ Polling Active:         │ Polling Suspended        │ Polling    │
│ ✓ GET /stocks/ribbon    │ (Tab not primary)        │ Suspended  │
│ ✓ GET /stocks/market    │                          │ (Not visible)
│ ✓ GET /news             │ Reads from store:        │            │
│                         │ • ribbon                 │ Reads from │
│ Store Updates:          │ • market                 │ store      │
│ • ribbon ← response     │ • news                   │            │
│ • market ← response     │                          │            │
│ • news ← response       │ BroadcastChannel         │            │
│                         │ listener updates         │            │
│ BroadcastChannel:       │ local store when         │            │
│ └─ Broadcast all        │ TAB1 updates             │ Re-enables │
│    updates to TAB2, 3   │                          │ polling on │
│                         │                          │ focus      │
└─────────────────────────┴──────────────────────────┴────────────┘

Key Features:
1. Tab Lock: Only primary tab polls
   - Prevents duplicate API calls
   - Saves bandwidth & backend load

2. BroadcastChannel: Syncs across tabs
   - TAB1 retrieves data
   - All tabs receive update
   - Sub-second latency

3. localStorage: Persistent state
   - Survives page reload
   - Survives tab close/reopen

4. Focus Detection:
   - document.hidden listener
   - Pauses polling when tab inactive
   - Resumes when tab active

5. Tab Failover:
   - If TAB1 closes, TAB2 becomes primary
   - Polling transfers automatically
   - No user experience change
```

---

## 7. WebSocket Fallback Strategy

```
┌─────────────────────────────────┐
│ Application Initial State       │
└──────────────┬──────────────────┘
               │
               ↓
    ┌──────────────────────────┐
    │ Attempt WebSocket        │
    │ Connect to wss://...     │
    └──────────┬───────────────┘
               │
        ┌──────┴──────┐
        │             │
    SUCCESS        TIMEOUT (3s)
        │             │
        ↓             ↓
    ┌─────┐   ┌────────────────────┐
    │ LIVE│   │ WebSocket Failed    │
    │ SYNC│   │ Use HTTP Polling    │
    └─────┘   └──────────┬─────────┘
        │                 │
        │         ┌───────┴────────┐
        │         │                │
        │    PRIMARY TAB      SECONDARY TAB
        │         │                │
        │    Poll HTTP        Read from Store
        │    GET /api/*       (BroadcastChannel)
        │         │                │
        │    Update Store    Local Updates
        │    Broadcast          Work Till
        │    to other tabs  Primary Reconnects
        │                        │
        │         ┌──────────────┘
        │         │
        │    WebSocket
        │    Reconnects?
        │         │
        │    ┌────┴────┐
        │    │         │
        │   YES       NO
        │    │         │
        │    ↓         ↓
        │ Stop HTTP  Continue
        │ Return to  Polling
        │ Live Sync  (Indefinite with
        │            retries)
        │
        └──────────┬─────────────────┘
                   │
                   ↓
            User sees data
            Updated in real-time
            via either channel
```

---

## 8. Error Handling Flow

```
API Request
    │
    ├─ Network Error
    │  └─ useSafePollingV2
    │     └─ Exponential Backoff
    │        └─ Retry (max 5x)
    │           └─ Store error in state
    │              └─ Display error to user
    │
    ├─ 401 Unauthorized
    │  └─ api-client.ts interceptor
    │     ├─ Clear token from localStorage
    │     └─ Redirect to /login
    │
    ├─ 404 Not Found
    │  └─ Component error boundary
    │     └─ Display 404 message
    │
    ├─ 500 Server Error
    │  └─ Caught by error handler
    │     └─ Retry with backoff
    │
    ├─ WebSocket Connect Error
    │  └─ websocket-manager.ts
    │     ├─ Emit error event
    │     ├─ Update store: isWebSocketConnected = false
    │     └─ Trigger polling fallback (3s delay)
    │
    └─ Timeout (5s)
       └─ useSafePollingV2
          └─ Abort request
             └─ Trigger retry

Error Display:
┌────────────────────────┐
│ Global Toast/Alert     │
│ "Failed to fetch data" │
│ [Retry] button         │
└────────────────────────┘

Also stored in:
store.ribbonError
store.marketError
store.newsError
```

---

## 9. Request Deduplication Cache

```
api-client.ts GET interceptor:
┌──────────────────────────────┐
│ GET /api/stocks/ribbon       │
└──────────┬───────────────────┘
           │
           ↓
    ┌─────────────────┐
    │ Cache Check     │
    │ (2 second TTL)  │
    └────┬────────────┘
         │
      ┌──┴──┐
      │     │
   MISS  HIT
      │     │
      ↓     ↓
    MAKE   RETURN
    REQ    CACHED
    │      │
    │      ↓
    │   Components
    │   get same data
    │   (prevents dupes)
    │
    └─→ STORE
        │
        ↓
    BroadcastChannel
    to other tabs

Timeline:
Request 1 (10:00:00.000) → Made → Cached
Request 2 (10:00:00.100) → Served from cache ✓
Request 3 (10:00:00.500) → Served from cache ✓
Request 4 (10:00:00.999) → Served from cache ✓
Request 5 (10:00:02.001) → Cache expired, made anew

Benefits:
✓ Prevents rapid duplicate calls
✓ Handles multi-component renders
✓ Tab focus optimization
✓ Minimal backend load
```

---

## 10. Data Freshness Strategy

```
Zustand Store Tracks:
┌────────────────────────┐
│ • ribbon              │
│ • ribbonTimestamp     │  ← "When was this updated?"
│                        │
│ • market              │
│ • marketTimestamp     │
│                        │
│ • news                │
│ • newsTimestamp       │
└────────────────────────┘

Hook to Check Staleness:
isStaleData('ribbon', maxAge: 30000)

Usage:
const isStale = useMarketStore(state =>
  state.isStaleData('ribbon', 30_000)
)

if (isStale) {
  // Show "refreshing..." indicator
  // Data is >30s old
}

Polling Prevents Staleness:
• Primary tab: Polls every 5-30s
• WebSocket: Real-time updates
• Result: Data never >5-30s old

User sees:
✓ Fresh data
✓ Timestamps updated
✓ "Last updated X seconds ago"
```

---

## Summary Decision Tree: Should I Fetch?

```
Component Mounts
    │
    ├─ "Do I need reactive market data?"
    │  │
    │  ├─ YES
    │  │  └─ Use useRibbonData() / useMarketData()
    │  │     └─ Data from store (always synced)
    │  │
    │  └─ NO
    │     └─ Use one-time fetch in useEffect
    │        └─ api.get() or service.method()
    │           └─ Store data in local useState
    │
    ├─ "Is this data portfolio-specific?"
    │  │
    │  ├─ YES
    │  │  └─ Fetch in useEffect
    │  │     └─ portfolioService.list()
    │  │
    │  └─ NO
    │     └─ Use store hook
    │
    └─ "Does this need polling?"
       │
       ├─ YES, every few seconds
       │  └─ useSafePollingV2 in DataSync
       │
       └─ NO, one-time fetch
          └─ Use useEffect + api

Result: Optimized, efficient data flow!
```

