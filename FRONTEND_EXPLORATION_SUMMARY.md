# Frontend Exploration - Complete Summary

## 📚 Documentation Created

I've created 4 comprehensive documents to help you understand the frontend architecture:

### 1. **FRONTEND_ARCHITECTURE_COMPLETE.md** ⭐ START HERE
- **Purpose**: High-level architectural overview
- **Contents**:
  - Directory structure with descriptions
  - Data flow diagram (WebSocket + Polling)
  - All API services explained
  - Custom hooks reference
  - State management (Zustand)
  - WebSocket & Polling orchestration
  - Page components overview
  - Key UI components
  - Performance optimizations
- **Best For**: Understanding how everything fits together

### 2. **FRONTEND_DATA_FLOW_DIAGRAMS.md**
- **Purpose**: Visual diagrams and decision trees
- **Contents**:
  - Component hierarchy
  - Data sync architecture
  - Polling decision tree
  - API service call hierarchy
  - useRibbonData flow
  - Multi-tab synchronization
  - WebSocket fallback strategy
  - Error handling flow
  - Request deduplication
  - Data freshness strategy
  - Decision tree for data fetching
- **Best For**: Visualizing data flow and understanding decisions

### 3. **FRONTEND_QUICK_REFERENCE.md**
- **Purpose**: Find features and code quickly
- **Contents**:
  - "Find features quickly" index
  - API integration points
  - Where polling is configured
  - State management location
  - Custom hooks index
  - HTTP client config
  - UI components list
  - Performance optimizations index
  - Authentication flow
  - Type definitions location
  - Bootstrap components
  - Feature location cheat sheet
- **Best For**: Quickly finding where something is implemented

### 4. **FRONTEND_FILE_TREE_COMPLETE.md**
- **Purpose**: Visual file structure with annotations
- **Contents**:
  - Complete directory tree with file descriptions
  - Component dependency map
  - Data flow dependencies
  - API call locations
  - File statistics
  - File relationships
  - Dataflow notes
- **Best For**: Understanding file organization and navigating the codebase

---

## 🎯 What You Asked For

### ✅ All React components related to Dashboard, Portfolio, and market/stock data:
- **Dashboard**: `app/dashboard/page.tsx`
- **Portfolio**: `app/portfolio/page.tsx`
- **Stocks**: `app/stocks/[symbol]/page.tsx`
- **Watchlist**: `app/watchlist/page.tsx`
- **Alerts**: `app/alerts/page.tsx`
- **News**: `app/news/page.tsx`
- **UI Components**: `components/sentinel/` (shell, charts, ribbon, etc.)

### ✅ Files with useEffect hooks and polling logic:
- **useSafePollingV2.ts** - Production polling with 5s timeout, 5 retries
- **useSafePolling.ts** - Basic polling (legacy)
- **data-sync-provider-v2.tsx** - Orchestrates all polling
- **useInterval.ts** - Simple interval wrapper
- **WebSocket hooks**: useWebSocket, useWebSocketPrices, useAlertsWS

### ✅ Where API calls like fetchMarket, fetchRibbon are defined:
- **lib/api-service.ts** - All API calls organized by resource:
  - `marketService.getLiveRibbon()`
  - `marketService.getMarketSummary()`
  - `portfolioService.list()`, `.summary()`, `.allocation()`, `.growth()`
  - `newsService.global()`, `.bySymbol()`, `.withSentiment()`
  - `alertService.list()`, `.create()`, `.update()`, `.remove()`
  - And more...

### ✅ Context or state management files:
- **lib/store-v2.ts** - Zustand store (PRODUCTION) with:
  - Multi-tab sync via BroadcastChannel
  - localStorage persistence
  - Timestamp-based staleness detection
- **lib/auth.ts** - Auth state management
- **components/providers/** - Context providers

### ✅ Hook files for data fetching:
- **hooks/useDataFetch.ts** - useRibbonData, useMarketData, useNewsData
- **hooks/useSafePollingV2.ts** - Production polling
- **hooks/useSafePolling.ts** - Basic polling
- **hooks/useWebSocket*.ts** - WebSocket connections
- **lib/useInterval.ts** - Interval hook

### ✅ Files related to polling, intervals, or API calls:
- **components/providers/data-sync-provider-v2.tsx** - Main polling orchestrator
- **lib/websocket-manager.ts** - WebSocket singleton
- **lib/multi-tab-lock.ts** - Tab coordination (prevents duplicate polling)
- **lib/api-client.ts** - Axios instance with request deduplication
- **hooks/useSafePollingV2.ts** - Production polling implementation

---

## 🔑 Key Discoveries

### Architecture Highlights:
1. **Dual Real-Time Strategy**:
   - WebSocket for live updates (primary)
   - HTTP polling fallback (when WebSocket fails)

2. **Smart Tab Coordination**:
   - Only primary (foreground) tab polls
   - Other tabs read from Zustand store
   - Store syncs via BroadcastChannel
   - If primary closes, next tab becomes primary

3. **Production-Grade Polling**:
   - 5-second timeout per request
   - Max 5 retries with exponential backoff
   - Data change detection (skip redundant updates)
   - Respects tab visibility (pauses when hidden)

4. **Robust Error Handling**:
   - Retry logic with backoff
   - 401 → redirect to login
   - WebSocket fail → automatic HTTP fallback
   - Error states in store

5. **Performance Optimizations**:
   - Request deduplication (2-second cache)
   - Component memoization
   - Lazy loading by route
   - Change detection prevents UI flicker

### Data Flow:
```
Real-Time Data Updates:
    WebSocket (Connected) → Zustand Store → Components
    OR
    HTTP Polling → Zustand Store → Components
    (Only primary tab polls)

Tab Sync:
    Primary Tab Updates Store
    ↓
    BroadcastChannel broadcasts
    ↓
    Secondary Tabs receive update
    ↓
    localStorage persists

One-Time Data (Portfolio, News):
    Component → useEffect → API Call → setState
```

### Key Files for Poll/Real-Time:
1. **data-sync-provider-v2.tsx** - Orchestrator (starts polling/WebSocket)
2. **useSafePollingV2.ts** - Polling implementation (with validation)
3. **websocket-manager.ts** - WebSocket connection (singleton)
4. **multi-tab-lock.ts** - Tab coordination
5. **store-v2.ts** - Central state (synced across tabs)
6. **api-service.ts** - Actual API calls

---

## 📊 Component Organization

### Pages (Routes):
```
/dashboard           → Dashboard (portfolio, market, news)
/portfolio           → Portfolio (holdings, allocation, growth)
/stocks/[symbol]     → Stock detail (chart, indicators, news)
/alerts              → Alert management
/watchlist           → Watchlist management
/news                → News feed
/trade-history       → Trade records
/profile             → User profile
/settings            → Settings
/support             → Support
/(auth)/login        → Login
/(auth)/register     → Register
```

### Data Sources by Page:
```
Dashboard:
  ├─ Real-time: ribbon, market (from store)
  └─ One-time: portfolio, news, growth (useEffect)

Portfolio:
  ├─ holdings via portfolioService.list()
  ├─ allocation via portfolioService.allocation()
  └─ growth via portfolioService.growth(range)

Stocks:
  ├─ price history via marketService.getStockDetails()
  ├─ indicators via indicatorService.combined()
  └─ news via newsService.bySymbol()

Alerts:
  ├─ alerts via alertService.list()
  └─ symbol autocomplete via marketService.getLiveRibbon()

Watchlist:
  ├─ symbols via watchlistService.list()
  └─ prices via marketService.getStockPrice(ticker)
```

---

## 🚀 Common Workflows

### To Add Data Polling for a New Component:
1. Add polling to `data-sync-provider-v2.tsx`
2. Create handler component (similar to RibbonPolling, MarketPolling)
3. Call `useSafePollingV2` with URL and onData callback
4. Update callback stores data in Zustand
5. Component reads from store via `useMarketStore`

### To Create New API Service:
1. Add methods to `lib/api-service.ts`
2. Use `api.get()`, `api.post()`, etc. (from api-client.ts)
3. Export as `serviceNameService`
4. Call from components

### To Fetch Data in Component:
1. One-time fetch: Use `useEffect` + `api.get()` + `useState`
2. Real-time data: Use `useMarketStore` (ribbon, market, news)
3. Polling fallback: Handled by `data-sync-provider-v2.tsx`

---

## 📈 Polling Intervals

```
Ribbon (top movers):          5 seconds     (polling)
Market summary:               5 seconds     (polling)
News:                         30 seconds    (polling)
Stock price:                  On demand     (component)
Portfolio:                    On demand     (component)
Indicators:                   On demand     (component)
Alerts:                       Real-time     (WebSocket)
```

---

## 🔒 Security & Auth

- All requests include `Authorization: Bearer {token}`
- Token stored in localStorage
- 401 response → redirect to /login
- Session validated in SessionBootstrap
- Protected routes use `ProtectedScreen` wrapper

---

## 🎯 Next Steps (If Building Features)

### To inspect a component's data source:
1. Open the page file (e.g., portfolio/page.tsx)
2. Check for `useMarketStore` calls → reads from real-time store
3. Check `useEffect` → one-time fetches
4. Check `useDataFetch` hooks → store helpers

### To trace where data comes from:
1. Find component reading data
2. Find where store gets updated
3. Follow to polling or WebSocket

### To understand polling for a data type:
1. Open data-sync-provider-v2.tsx
2. Look for polling component (RibbonPolling, MarketPolling, etc.)
3. Check useSafePollingV2 call
4. See API service call (e.g., marketService.getLiveRibbon)

---

## 📖 Using These Documents

### For Architecture Understanding:
**Start with**: FRONTEND_ARCHITECTURE_COMPLETE.md
- Read Directory Structure section
- Review Data Flow Architecture diagram
- Study API Services section

### For Visual Learners:
**Use**: FRONTEND_DATA_FLOW_DIAGRAMS.md
- Component Hierarchy diagram
- Multi-Tab Synchronization section
- WebSocket Fallback Strategy
- Error Handling Flow

### For Quick Lookups:
**Reference**: FRONTEND_QUICK_REFERENCE.md
- Use "Find Features Quickly" section
- Look up API Integration Points
- Check Feature Location Cheat Sheet

### For File Navigation:
**Navigate with**: FRONTEND_FILE_TREE_COMPLETE.md
- Full directory tree with annotations
- File relationships section
- Component dependency map

---

## ✨ Extra Insights

### Production Readiness:
✅ Multi-tab coordination prevents duplicate requests
✅ WebSocket with HTTP fallback ensures reliability
✅ Exponential backoff prevents server overwhelming
✅ Error states allow graceful degradation
✅ Data staleness tracking maintains consistency

### Performance:
✅ Request deduplication (2s cache)
✅ Change detection (skip redundant updates)
✅ Component memoization (minimal re-renders)
✅ Code splitting by route (faster initial load)

### Developer Experience:
✅ Clear service organization (by resource)
✅ Type safety (full TypeScript)
✅ Custom hooks for common patterns
✅ Error messages in store
✅ Structured logging [POLL], [WS] prefixes

---

## 🎓 Learning Path

1. **Start**: FRONTEND_ARCHITECTURE_COMPLETE.md (5-10 min read)
2. **Understand Flow**: FRONTEND_DATA_FLOW_DIAGRAMS.md (10-15 min read)
3. **Explore**: FRONTEND_QUICK_REFERENCE.md (as needed)
4. **Navigate**: FRONTEND_FILE_TREE_COMPLETE.md (as needed)
5. **Deep Dive**: Read actual component files as needed

---

## 📝 Summary

The Stock Sentinel frontend is a sophisticated Next.js 14+ application with:

- **8+ main feature pages** (Dashboard, Portfolio, Stocks, Alerts, etc.)
- **Real-time data via WebSocket + HTTP polling fallback**
- **Smart multi-tab coordination** (prevents duplicate requests)
- **Production-grade error handling** (retries, backoff, graceful fallback)
- **Zustand state management** with localStorage + BroadcastChannel sync
- **50+ TypeScript files** organized in clear directory structure
- **10+ custom hooks** for common patterns
- **Comprehensive type system** (types.ts)

All real-time data (ribbon, market, news) flows through a central orchestrator (DataSyncProviderV2) that manages both WebSocket and polling, ensuring optimal performance and reliability.

---

**Generated**: April 13, 2026
**Frontend Version**: Next.js 14+ with React 18+
**State Management**: Zustand v4+
**HTTP Client**: Axios
**Styling**: Tailwind CSS

