/**
 * PRODUCTION INTEGRATION GUIDE
 * Step-by-step instructions to integrate the new production system
 * 
 * This guide walks through:
 * 1. Environment setup
 * 2. Provider integration
 * 3. Store migration
 * 4. Page updates
 * 5. Testing
 * 6. Deployment
 */

// ═══════════════════════════════════════════════════════════════════════════
// STEP 1: ENVIRONMENT FILE SETUP
// ═══════════════════════════════════════════════════════════════════════════

// File: frontend/.env.local (for development)
// ─────────────────────────────────────────────

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/ws

NEXT_PUBLIC_POLLING_INTERVAL=5000
NEXT_PUBLIC_CACHE_TTL=300000
NEXT_PUBLIC_WS_RECONNECT_ATTEMPTS=5
NEXT_PUBLIC_WS_RECONNECT_DELAY=1000

NEXT_PUBLIC_ENABLE_LOGGING=true
NEXT_PUBLIC_ENABLE_MONITORING=false
NEXT_PUBLIC_SYNC_ACROSS_TABS=true
NEXT_PUBLIC_PAUSE_POLLING_ON_HIDDEN=true


// File: frontend/.env.staging
// ────────────────────────────

NEXT_PUBLIC_API_BASE_URL=https://staging-api.stock-sentinel.com/api
NEXT_PUBLIC_WS_BASE_URL=wss://staging-api.stock-sentinel.com/ws

NEXT_PUBLIC_POLLING_INTERVAL=5000
NEXT_PUBLIC_CACHE_TTL=300000
NEXT_PUBLIC_WS_RECONNECT_ATTEMPTS=5
NEXT_PUBLIC_WS_RECONNECT_DELAY=1000

NEXT_PUBLIC_ENABLE_LOGGING=true
NEXT_PUBLIC_ENABLE_MONITORING=true
NEXT_PUBLIC_SYNC_ACROSS_TABS=true
NEXT_PUBLIC_PAUSE_POLLING_ON_HIDDEN=true


// File: frontend/.env.production
// ───────────────────────────────

NEXT_PUBLIC_API_BASE_URL=https://api.stock-sentinel.com/api
NEXT_PUBLIC_WS_BASE_URL=wss://api.stock-sentinel.com/ws

NEXT_PUBLIC_POLLING_INTERVAL=5000
NEXT_PUBLIC_CACHE_TTL=300000
NEXT_PUBLIC_WS_RECONNECT_ATTEMPTS=5
NEXT_PUBLIC_WS_RECONNECT_DELAY=1000

NEXT_PUBLIC_ENABLE_LOGGING=false
NEXT_PUBLIC_ENABLE_MONITORING=true
NEXT_PUBLIC_SYNC_ACROSS_TABS=true
NEXT_PUBLIC_PAUSE_POLLING_ON_HIDDEN=true


// ═══════════════════════════════════════════════════════════════════════════
// STEP 2: ROOT LAYOUT PROVIDER INTEGRATION
// ═══════════════════════════════════════════════════════════════════════════

// File: frontend/app/layout.tsx
// Update the root layout to include providers

import ErrorBoundaryProvider from '@/components/providers/error-boundary-provider';
import { DataSyncProvider } from '@/components/providers/data-sync-provider-v2';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundaryProvider>
          <DataSyncProvider>
            {/* Other providers (Zustand, etc.) */}
            {children}
          </DataSyncProvider>
        </ErrorBoundaryProvider>
      </body>
    </html>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// STEP 3: MIGRATE PAGES TO USE STORE-V2
// ═══════════════════════════════════════════════════════════════════════════

// File: frontend/app/dashboard/page.tsx
// Update imports and usage

'use client';

import { useMarketStore } from '@/lib/store-v2';  // ← Changed from store.ts

export default function DashboardPage() {
  // Read from store-v2
  const ribbon = useMarketStore((state) => state.ribbon);
  const market = useMarketStore((state) => state.market);
  const isRibbonLoading = useMarketStore((state) => state.isRibbonLoading);
  const isMarketLoading = useMarketStore((state) => state.isMarketLoading);
  const ribbonError = useMarketStore((state) => state.ribbonError);
  const marketError = useMarketStore((state) => state.marketError);

  // WebSocket/polling status for debugging
  const isWebSocketConnected = useMarketStore(
    (state) => state.isWebSocketConnected
  );
  const isPollingActive = useMarketStore((state) => state.isPollingActive);

  return (
    <div>
      {/* Display ribbon */}
      {ribbon && <RibbonComponent data={ribbon} />}

      {/* Display market data */}
      {market && <MarketComponent data={market} />}

      {/* Error handling */}
      {ribbonError && <ErrorAlert message={ribbonError} />}
      {marketError && <ErrorAlert message={marketError} />}

      {/* Loading states */}
      {isRibbonLoading && <Skeleton />}

      {/* Debug info (remove in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{ fontSize: '12px', opacity: 0.5 }}>
          WebSocket: {isWebSocketConnected ? '🟢' : '🔴'} Polling: {isPollingActive ? '🟢' : '🔴'}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// STEP 4: UPDATE NEWS PAGE
// ═══════════════════════════════════════════════════════════════════════════

// File: frontend/app/news/page.tsx

'use client';

import { useMarketStore } from '@/lib/store-v2';
import { useState, useEffect } from 'react';

export default function NewsPage() {
  const news = useMarketStore((state) => state.news);
  const isNewsLoading = useMarketStore((state) => state.isNewsLoading);
  const newsError = useMarketStore((state) => state.newsError);

  const [page, setPage] = useState(0);
  const itemsPerPage = 10;

  const paginatedNews = Array.isArray(news)
    ? news.slice(page * itemsPerPage, (page + 1) * itemsPerPage)
    : [];

  return (
    <div>
      <h1>Market News</h1>

      {newsError && <ErrorAlert message={newsError} />}

      {isNewsLoading ? (
        <Skeleton count={5} />
      ) : (
        <>
          {paginatedNews.map((item: any) => (
            <NewsCard key={item.id} item={item} />
          ))}

          {/* Pagination */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
            >
              Previous
            </button>
            <span>Page {page + 1}</span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * itemsPerPage >= (news?.length || 0)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// STEP 5: REPLACE RIBBON COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

// File: frontend/components/sentinel/optimized-ribbon.tsx
// Already updated in previous sessions - verify it uses store-v2

// Should import like this:
import { useMarketStore } from '@/lib/store-v2';

// And read data like:
const ribbon = useMarketStore((state) => state.ribbon);
const isRibbonLoading = useMarketStore((state) => state.isRibbonLoading);


// ═══════════════════════════════════════════════════════════════════════════
// STEP 6: TESTING MULTI-TAB SYNC
// ═══════════════════════════════════════════════════════════════════════════

// Test 1: Open two tabs and verify:
// - Only one tab is "primary" (check browser console for "[Lock] PRIMARY TAB")
// - Data updates appear in both tabs
// - If primary tab closes, secondary becomes primary
// - No duplicate API calls in network tab

// Test 2: Verify WebSocket priority:
// - Open app with network tab open
// - If WebSocket connects, polling should stop (no API calls)
// - If WebSocket disconnects, polling should resume (API calls resume)

// Test 3: Verify error handling:
// - Temporarily block WebSocket in DevTools
// - App should fallback to polling
// - Data should still update

// Test 4: Verify performance:
// - Network tab should show no duplicate calls
// - Memory should remain stable with multiple data updates
// - CPU usage should be minimal during idle


// ═══════════════════════════════════════════════════════════════════════════
// STEP 7: DEPLOYMENT CHECKLIST
// ═══════════════════════════════════════════════════════════════════════════

/*

Pre-deployment:
□ Set correct environment variables in .env.production
□ Verify API_BASE_URL and WS_BASE_URL are correct
□ Test WebSocket endpoint configuration
□ Verify CORS settings on backend
□ Test in staging environment for 24 hours

Build:
□ Run: npm run build
□ No TypeScript errors
□ No console warnings
□ Bundle size check (should not increase significantly)

Testing:
□ Manual test multi-tab scenarios
□ Test WebSocket reconnection
□ Test polling fallback
□ Test error boundaries
□ Load test with multiple concurrent users

Monitoring:
□ Set up error monitoring in production
□ Monitor WebSocket connection success rate
□ Monitor API call frequency (should be stable)
□ Monitor memory usage over time

Rollback Plan:
□ Keep previous version deployed
□ Monitor error rates for 1 hour post-deployment
□ Have rollback procedure ready

Performance Targets:
□ Page load time: < 2 seconds
□ Data sync latency: < 1 second (WebSocket) or < 5 seconds (polling)
□ Error rate: < 0.1%
□ Memory usage: < 100MB per tab
□ CPU usage: < 5% idle


// ═══════════════════════════════════════════════════════════════════════════
// STEP 8: MONITORING AND OBSERVABILITY
// ═══════════════════════════════════════════════════════════════════════════

// The config.ts file includes monitor utility
// Use it to track errors:

import { monitor } from '@/lib/config';

try {
  // Some operation
} catch (error) {
  monitor.trackError(error as Error, 'MyComponent.operation', {
    context: 'additional data',
  });
}

// Monitor automatically:
// - Sends error to monitoring service (if enabled in config)
// - Logs to console (if ENABLE_LOGGING enabled)
// - Includes timestamp and context


// ═══════════════════════════════════════════════════════════════════════════
// FILE SUMMARY - NEW PRODUCTION SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

New Files Created:
├── frontend/lib/config.ts                          (Configuration system)
├── frontend/lib/store-v2.ts                        (Enhanced Zustand store)
├── frontend/lib/websocket-manager.ts               (Global WS manager)
├── frontend/lib/multi-tab-lock.ts                  (Tab coordination)
├── frontend/hooks/useSafePollingV2.ts              (Safe polling hook)
├── frontend/components/providers/error-boundary-provider.tsx
└── frontend/components/providers/data-sync-provider-v2.tsx

Files to Update:
├── frontend/app/layout.tsx                         (Add providers)
├── frontend/app/dashboard/page.tsx                 (Use store-v2)
├── frontend/app/portfolio/page.tsx                 (Use store-v2)
├── frontend/app/news/page.tsx                      (Use store-v2)
└── frontend/components/sentinel/optimized-ribbon.tsx (Already done)

Environment Files to Create:
├── frontend/.env.local                             (Development)
├── frontend/.env.staging                           (Staging)
└── frontend/.env.production                        (Production)

Existing Files (No Changes Needed):
├── frontend/hooks/useSafePolling.ts                (Still available)
├── frontend/hooks/useWebSocket.ts                  (Still available)
└── backend/app/api/routes/stocks_extended.py      (Caching works)


// ═══════════════════════════════════════════════════════════════════════════
// ARCHITECTURE DIAGRAM
// ═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                      ERROR BOUNDARY PROVIDER                     │
├─────────────────────────────────────────────────────────────────┤
│                      DATA SYNC PROVIDER V2                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  WebSocket Manager (Singleton)                          │    │
│  │  - One connection globally                              │    │
│  │  - Auto-reconnect with backoff                          │    │
│  │  - Message routing                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Multi-Tab Lock (Singleton)                             │    │
│  │  - Determines primary tab                               │    │
│  │  - Uses localStorage + BroadcastChannel                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Safe Polling Hooks (per component)                     │    │
│  │  - Check WebSocket connected first                      │    │
│  │  - Only poll on primary tab                             │    │
│  │  - Exponential backoff on errors                        │    │
│  │  - Respect visibility API                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Store V2 (Global State)                                │    │
│  │  - BroadcastChannel sync across tabs                    │    │
│  │  - Stale data protection (timestamps)                   │    │
│  │  - Source tracking (WebSocket vs polling)               │    │
│  │  - Error tracking per source                            │    │
│  │  - localStorage persistence                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                        COMPONENTS                                 │
│              (Dashboard, Portfolio, News)                        │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
1. DataSyncProvider initializes WebSocket Manager + Tab Lock
2. Primary tab: WebSocket connects → poll suspended
3. Secondary tab: Sees primary → poll suspended automatically
4. WebSocket receives data → Store updated → Broadcast to other tabs
5. All tabs see new data via store-v2
6. If WebSocket disconnects → Primary tab resumes polling
7. Polling updates store → Broadcast to secondary tabs


// ═══════════════════════════════════════════════════════════════════════════
// TROUBLESHOOTING
// ═══════════════════════════════════════════════════════════════════════════

Issue: Polling still happening when WebSocket connected
→ Check: Store shows isWebSocketConnected = true
→ Check: useSafePollingV2 respects this flag
→ Solution: Verify WebSocket message handling is working

Issue: Duplicate polling in two tabs
→ Check: Only one tab shows "[Lock] PRIMARY TAB" in console
→ Check: localStorage has 'stock-sentinel:tab-lock' value
→ Solution: Verify Tab Lock system is running

Issue: Data not syncing across tabs
→ Check: BroadcastChannel is available (not in embedded iframes)
→ Check: Store-v2 has broadcast listeners set up
→ Solution: Test BroadcastChannel manually in console

Issue: High memory usage
→ Check: Polling intervals are not too short
→ Check: Store data structure reasonably sized
→ Check: Cleanup functions in useEffect are called
→ Solution: Profile with DevTools Memory tab

Issue: WebSocket not connecting
→ Check: WS_BASE_URL environment variable correct
→ Check: Server accepts WebSocket connections
→ Check: SSL/TLS certificates valid (for WSS)
→ Solution: Test with wscat or similar tool

*/
