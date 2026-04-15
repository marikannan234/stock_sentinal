# Frontend - Complete File Tree Reference

## Full Frontend Directory Structure

```
frontend/
│
├── 📄 Configuration Files
│   ├── .env.local                     # Local environment (git ignored)
│   ├── .env.production                # Production environment
│   ├── .env.staging                   # Staging environment
│   ├── next.config.mjs                # Next.js configuration
│   ├── tailwind.config.ts             # Tailwind CSS config
│   ├── postcss.config.mjs             # PostCSS config
│   ├── tsconfig.json                  # TypeScript config
│   ├── tsconfig.tsbuildinfo           # TypeScript build info
│   ├── package.json                   # Dependencies
│   ├── package-lock.json
│   ├── global.d.ts                    # Global TypeScript defs
│   ├── next-env.d.ts                  # Next.js TypeScript defs
│   ├── .dockerignore                  # Docker ignore rules
│   └── Dockerfile                     # Docker image config
│
├── 📁 app/  (Next.js App Router - Routes)
│   ├── 📄 page.tsx                    # Home page (redirects to /dashboard or /login)
│   ├── 📄 layout.tsx                  # Root layout with providers
│   ├── 📄 globals.css                 # Global styles
│   │
│   ├── 📁 (auth)/                     # Auth group (parentheses = no route segment)
│   │   ├── 📁 login/
│   │   │   └── 📄 page.tsx            # Login page
│   │   ├── 📁 register/
│   │   │   └── 📄 page.tsx            # Register page
│   │   └── 📁 forgot-password/
│   │       └── 📄 page.tsx            # Forgot password
│   │
│   ├── 📁 dashboard/
│   │   └── 📄 page.tsx                # Dashboard (portfolio overview, market, news)
│   │
│   ├── 📁 portfolio/
│   │   └── 📄 page.tsx                # Portfolio (holdings, allocation, growth)
│   │
│   ├── 📁 stocks/
│   │   └── 📁 [symbol]/               # Dynamic route for individual stocks
│   │       └── 📄 page.tsx            # Stock detail (chart, indicators, news)
│   │
│   ├── 📁 alerts/
│   │   └── 📄 page.tsx                # Alerts management
│   │
│   ├── 📁 watchlist/
│   │   └── 📄 page.tsx                # Watchlist management
│   │
│   ├── 📁 news/
│   │   └── 📄 page.tsx                # News feed
│   │
│   ├── 📁 trade-history/
│   │   └── 📄 page.tsx                # Trade history table
│   │
│   ├── 📁 profile/
│   │   └── 📄 page.tsx                # User profile
│   │
│   ├── 📁 settings/
│   │   └── 📄 page.tsx                # Settings
│   │
│   └── 📁 support/
│       └── 📄 page.tsx                # Support / Help
│
├── 📁 components/  (React Components)
│   ├── 📄 alert-bootstrap.tsx         # Bootstrap: Alert system setup
│   ├── 📄 session-bootstrap.tsx       # Bootstrap: Session/auth init
│   │
│   ├── 📁 auth/                       # Authentication UI
│   │   ├── 📄 auth-shell.tsx          # Auth page layout
│   │   ├── 📄 login-form.tsx          # Login form component
│   │   └── 📄 register-form.tsx       # Register form component
│   │
│   ├── 📁 providers/                  # Context Providers
│   │   ├── 📄 data-sync-provider-v2.tsx        # Production data sync (WebSocket + polling)
│   │   ├── 📄 data-sync-provider.tsx           # Original data sync (legacy)
│   │   └── 📄 error-boundary-provider.tsx      # Global error boundary
│   │
│   ├── 📁 sentinel/                   # Core UI Components (Design System)
│   │   ├── 📄 shell.tsx               # Main application shell/layout
│   │   │                              # ├─ Sidebar navigation (9 menu items)
│   │   │                              # ├─ Quick-trade modal
│   │   │                              # └─ Content area
│   │   │
│   │   ├── 📄 optimized-ribbon.tsx    # Ticker tape component (top movers)
│   │   │                              # └─ Real-time streaming
│   │   │
│   │   ├── 📄 charts.tsx              # Chart components
│   │   │                              # ├─ SentinelLineChart (SVG)
│   │   │                              # ├─ Candlestick chart
│   │   │                              # ├─ AllocationDonut (pie)
│   │   │                              # └─ Interactive hover
│   │   │
│   │   ├── 📄 primitives.tsx          # Reusable UI primitives
│   │   │                              # ├─ Card components
│   │   │                              # ├─ Skeletons
│   │   │                              # ├─ Icons
│   │   │                              # ├─ StatChip
│   │   │                              # └─ Other elements
│   │   │
│   │   ├── 📄 protected-screen.tsx    # Route protection wrapper
│   │   │                              # └─ Auth requirement check
│   │   │
│   │   └── 📄 error-boundary.tsx      # Local error boundary
│   │                                  # └─ Component error handling
│   │
│   └── 📁 ui/                         # Basic UI Components
│       └── 📄 toast.tsx               # Toast notification component
│
├── 📁 hooks/  (Custom React Hooks)
│   ├── 📄 useDataFetch.ts             # Data fetching hooks from store
│   │                                  # ├─ useRibbonData()
│   │                                  # ├─ useMarketData()
│   │                                  # ├─ useNewsData()
│   │                                  # └─ other data hooks
│   │
│   ├── 📄 useSafePollingV2.ts         # Production-grade polling
│   │                                  # ├─ 5s timeout per request
│   │                                  # ├─ Max 5 retries
│   │                                  # ├─ WebSocket fallback aware
│   │                                  # └─ Data change detection
│   │
│   ├── 📄 useSafePolling.ts           # Basic safe polling (legacy)
│   │                                  # └─ setTimeout-based
│   │
│   ├── 📄 useInterval.ts              # Simple interval hook
│   │
│   ├── 📄 useWebSocket.ts             # WebSocket connection hook
│   │
│   ├── 📄 useWebSocketPrices.ts       # WebSocket price updates
│   │
│   ├── 📄 useAlertsWS.ts              # WebSocket alerts
│   │
│   └── 📄 useAlertNotifications.ts    # Alert UI notifications
│
├── 📁 lib/  (Utilities, API, State)
│   ├── 📄 api-client.ts               # Axios instance with interceptors
│   │                                  # ├─ Token injection
│   │                                  # ├─ Request deduplication (2s)
│   │                                  # └─ 401 redirect
│   │
│   ├── 📄 api-service.ts              # API endpoints (organized by resource)
│   │                                  # ├─ authService
│   │                                  # ├─ marketService
│   │                                  # ├─ portfolioService
│   │                                  # ├─ newsService
│   │                                  # ├─ alertService
│   │                                  # ├─ watchlistService
│   │                                  # ├─ indicatorService
│   │                                  # ├─ profileService
│   │                                  # └─ getErrorMessage()
│   │
│   ├── 📄 store-v2.ts                 # Zustand store (PRODUCTION)
│   │                                  # ├─ Multi-tab sync (BroadcastChannel)
│   │                                  # ├─ Persistent (localStorage)
│   │                                  # ├─ ribbon: LiveQuote[]
│   │                                  # ├─ market: MarketSummary
│   │                                  # ├─ news: NewsArticle[]
│   │                                  # ├─ Loading/error states
│   │                                  # └─ WebSocket status
│   │
│   ├── 📄 store.ts                    # Original Zustand store (legacy)
│   │
│   ├── 📄 websocket-manager.ts        # Global WebSocket singleton
│   │                                  # ├─ One connection per browser
│   │                                  # ├─ Auto-reconnect
│   │                                  # ├─ Message routing
│   │                                  # ├─ Heartbeat mechanism
│   │                                  # └─ 3s fallback delay
│   │
│   ├── 📄 multi-tab-lock.ts           # Tab focus coordination
│   │                                  # ├─ Primary tab detection
│   │                                  # └─ Polling eligibility
│   │
│   ├── 📄 auth.ts                     # Auth store & utilities
│   │                                  # ├─ Login/logout
│   │                                  # ├─ Token management
│   │                                  # └─ Session hydration
│   │
│   ├── 📄 config.ts                   # Configuration & logger
│   │                                  # ├─ API_BASE_URL
│   │                                  # ├─ POLLING_INTERVAL
│   │                                  # ├─ WS settings
│   │                                  # ├─ Logging utilities
│   │                                  # └─ Monitoring
│   │
│   ├── 📄 types.ts                    # TypeScript type definitions
│   │                                  # ├─ LiveQuote
│   │                                  # ├─ MarketSummary
│   │                                  # ├─ PortfolioHolding
│   │                                  # ├─ NewsArticle
│   │                                  # ├─ AlertItem
│   │                                  # ├─ CombinedIndicators
│   │                                  # ├─ UserProfile
│   │                                  # └─ Many more...
│   │
│   ├── 📄 format.ts                   # Format utilities (dates, numbers)
│   │
│   ├── 📄 hooks.ts                    # Additional hooks
│   │
│   ├── 📄 logo.ts                     # Logo utilities
│   │
│   ├── 📄 sentinel-utils.ts           # Sentinel-specific utilities
│   │                                  # ├─ formatCurrency()
│   │                                  # ├─ formatPercent()
│   │                                  # ├─ formatCompactNumber()
│   │                                  # └─ Other helpers
│   │
│   ├── 📄 useInterval.ts              # Alternative interval hook
│   │
│   └── 📄 ws-manager.ts               # Alternative WebSocket manager
│
├── 📁 .next/                          # Build output (git ignored)
│   └── ... (compiled code)
│
├── 📁 node_modules/                   # Dependencies (git ignored)
│   └── ... (installed packages)
│
└── 📁 .stitch-temp/                   # Temp directory (git ignored)
    └── ... (temporary files)
```

---

## Component Dependency Map

```
RootLayout
├── ToastProvider
└── DataSyncProviderV2 ⭐
    ├── Ribbon Polling
    ├── Market Polling
    ├── News Polling
    └── SessionBootstrap
        └── AlertBootstrap
            └── Outlet → Page Route
                └── ProtectedScreen
                    └── SentinelShell
                        ├── Navigation Sidebar
                        ├── OptimizedRibbon
                        ├── QuickTradeModal
                        └── Page Content
                            ├── Charts
                            ├── Tables
                            └── Forms
```

---

## Data Flow Dependencies

```
Application Root
    │
    ├─ DataSyncProviderV2
    │  ├─ WebSocketManager (singleton)
    │  ├─ getTabLock()
    │  ├─ useSafePollingV2 (for ribbon)
    │  ├─ useSafePollingV2 (for market)
    │  ├─ useSafePollingV2 (for news)
    │  └─ useMarketStore
    │
    ├─ SessionBootstrap
    │  └─ useAuthStore
    │
    ├─ AlertBootstrap
    │  ├─ useAlertsWS
    │  ├─ useAlertNotifications
    │  └─ useMarketStore
    │
    └─ Page Route
       ├─ Components consuming:
       │  ├─ useMarketStore (for ribbon, market, news)
       │  ├─ useDataFetch hooks (for data)
       │  ├─ api-service methods (for one-time fetches)
       │  └─ useRibbonData, useMarketData, etc.
       │
       └─ Polling Data flows to:
           └─ Zustand Store (store-v2.ts)
               └─ BroadcastChannel
                   └─ Other Tabs
```

---

## API Call Locations

```
api-service.ts exports:
├── authService
│   ├── login()
│   ├── register()
│   ├── me()
│   └── updateMe()
│
├── marketService
│   ├── getLiveRibbon()        ← Called by: Polling in DataSyncProviderV2
│   ├── getMarketSummary()     ← Called by: Polling in DataSyncProviderV2
│   ├── getStockDetails()      ← Called by: Stock detail page
│   ├── getStockPrice()        ← Called by: Watchlist page
│   └── search()               ← Called by: Symbol search
│
├── portfolioService
│   ├── list()                 ← Called by: Portfolio page
│   ├── summary()              ← Called by: Dashboard page
│   ├── add()                  ← Called by: Quick-trade modal
│   ├── allocation()           ← Called by: Portfolio page
│   ├── growth()               ← Called by: Dashboard, Portfolio pages
│   └── remove()               ← Called by: Quick-trade modal (sell)
│
├── newsService
│   ├── global()               ← Called by: News page
│   ├── bySymbol()             ← Called by: Stock detail page
│   └── withSentiment()        ← Called by: Stock detail page
│
├── alertService
│   ├── list()                 ← Called by: Alerts page
│   ├── create()               ← Called by: Alerts page
│   ├── update()               ← Called by: Alerts page
│   └── remove()               ← Called by: Alerts page
│
├── watchlistService
│   ├── list()                 ← Called by: Watchlist page
│   ├── add()                  ← Called by: Watchlist page
│   └── remove()               ← Called by: Watchlist page
│
├── indicatorService
│   └── combined()             ← Called by: Stock detail page
│
└── profileService
    ├── getProfile()           ← Called by: Profile page
    └── updateProfile()        ← Called by: Profile page

All routed through:
    api-client.ts (Axios instance)
```

---

## File Statistics

```
Pages:
  • 8 main pages (dashboard, portfolio, stocks, alerts, watchlist, news, trade-history, profile, settings, support)
  • 3 auth pages (login, register, forgot-password)
  • 1 home page (redirects)

Components:
  • 15+ UI components (shell, ribbon, charts, primitives, etc.)
  • 3 provider components (auth, data-sync, error-boundary)
  • 3 bootstrap components

Hooks:
  • 10 custom hooks (useDataFetch, useSafePollingV2, useWebSocket, etc.)

Library Files:
  • 13 utility/lib files (api, store, websocket, auth, config, types, etc.)

Total TypeScript/TSX files: 50+
Total CSS files: 1 (globals.css + Tailwind)
```

---

## Key File Relationships

### For Real-Time Market Data:
```
Page Component
    ↓
useMarketStore hook (from lib/store-v2.ts)
    ↓
Store data (ribbon, market, news)
    ↓
Updated by:
├─ WebSocket messages (via websocket-manager.ts)
├─ HTTP polling responses (via useSafePollingV2 in data-sync-provider-v2.tsx)
└─ Manual updates (rarely)
```

### For Portfolio Data:
```
Page Component (portfolio/page.tsx)
    ↓
useEffect hook
    ↓
portfolioService.list/summary/allocation/growth()
    ↓
api-client.ts (Axios with token)
    ↓
Backend API
```

### For Stock Details:
```
Stock Detail Page ([symbol]/page.tsx)
    ↓
marketService.getStockDetails()
indicatorService.combined()
newsService.bySymbol()
    ↓
api-client.ts
    ↓
Backend API
```

### For Alert Notifications:
```
AlertBootstrap component
    ↓
useAlertsWS hook
    ↓
websocket-manager.ts
    ↓
/ws endpoint (alert messages)
```

---

## Important Notes

### Bootstrap Priority:
1. ToastProvider (UI notifications)
2. DataSyncProviderV2 (real-time data)
3. SessionBootstrap (auth init)
4. AlertBootstrap (alert listener)

### Multi-Tab Safety:
- Only **primary tab** polls to backend
- Other tabs read from **Zustand store**
- Store syncs via **BroadcastChannel**
- localStorage provides **persistence**

### Error Handling:
- API errors → store in state → display toast
- 401 → redirect to /login
- WebSocket fail → fall back to polling
- Polling fail → retry with exponential backoff

### Performance:
- Request deduplication (2s cache)
- Data change detection (skip redundant updates)
- Tab coordination (no duplicate requests)
- Component memoization (minimal re-renders)
- Lazy loading (code split by route)

