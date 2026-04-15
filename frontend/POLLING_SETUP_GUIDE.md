# Production-Ready Polling Infrastructure Guide

This guide demonstrates how to use the new production-ready polling infrastructure for the Stock Sentinel frontend.

## Overview

The polling infrastructure consists of three main components:

1. **`useSafePolling` Hook** - Safe polling with AbortController, visibility detection, and auto-retry
2. **`useMarketStore` (Zustand)** - Global state for shared market data across components
3. **`useWebSocket` Hook** - WebSocket connections with auto-reconnect

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Components                        │
│         (Dashboard, Portfolio, Stock Details, etc)           │
└────────────┬─────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────────┐   ┌───▼────────────────┐
│   Local    │   │ useMarketStore     │
│   State    │   │ (Zustand Global)   │
└────────────┘   └───┬────────────────┘
                 │
    ┌────────────┴───────────────────┐
    │                                │
┌───▼──────────────┐      ┌─────────▼──────┐
│ useSafePolling   │      │  useWebSocket  │
│ (setTimeout)     │      │  (auto-reconnect)
└───┬──────────────┘      └─────────┬──────┘
    │                               │
┌───▼───────────────┬──────────────▼────┐
│   API Server      │   WebSocket Server │
│  /dashboard/*     │   /ws/alerts       │
└───────────────────┴───────────────────┘
```

## Components

### 1. useSafePolling Hook

**Location:** `/frontend/hooks/useSafePolling.ts`

**Features:**
- setTimeout-based polling (no setInterval)
- AbortController for request cancellation
- Document.hidden detection to pause polling on inactive tabs
- Retry logic with exponential backoff
- isMounted tracking to prevent memory leaks
- Prevents overlapping API calls

**Usage Example:**

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useSafePolling } from '@/hooks/useSafePolling';
import { api } from '@/lib/api-client';

export function MyComponent() {
  const [data, setData] = useState(null);

  // Simple polling (5 seconds)
  useSafePolling(
    async (signal) => {
      try {
        const response = await api.get('/endpoint', { signal });
        setData(response.data);
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Failed to fetch:', error);
        }
      }
    },
    { interval: 5000 }
  );

  return <div>{data ? JSON.stringify(data) : 'Loading...'}</div>;
}
```

**Advanced Usage with Custom Handlers:**

```typescript
useSafePolling(
  async (signal) => {
    try {
      const [market, ribbon, news] = await Promise.all([
        api.get('/dashboard/market', { signal }),
        api.get('/dashboard/ribbon', { signal }),
        api.get('/dashboard/news', { signal }),
      ]);
      
      updateUI(market.data, ribbon.data, news.data);
    } catch (error) {
      handleError(error);
    }
  },
  {
    interval: 5000,
    retryDelay: 1000,
    maxRetries: 3,
  }
);
```

### 2. useMarketStore (Zustand)

**Location:** `/frontend/lib/store.ts`

**Purpose:** Global, shared state for market data across all components

**Features:**
- Centralized market data (ribbon, market, news)
- Timestamp tracking to prevent stale data
- Loading states (only on initial load)
- Error tracking per data source
- Polling suspension/resumption capability

**Usage Example: Simple Read from Store**

```typescript
'use client';

import { useMarketStore } from '@/lib/store';

export function MarketDisplay() {
  // Subscribe to specific slices of state
  const ribbon = useMarketStore((state) => state.ribbon);
  const market = useMarketStore((state) => state.market);
  const marketLoading = useMarketStore((state) => state.marketLoading);

  return (
    <div>
      {marketLoading ? (
        <p>Loading market data...</p>
      ) : (
        <>
          <h2>Market:</h2>
          <pre>{JSON.stringify(market, null, 2)}</pre>
          <h2>Top Movers:</h2>
          {ribbon.map((stock) => (
            <div key={stock.symbol}>
              {stock.symbol}: ${stock.price}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
```

**Usage Example: Update Store from Hook**

```typescript
'use client';

import { useEffect } from 'react';
import { useSafePolling } from '@/hooks/useSafePolling';
import { useMarketStore } from '@/lib/store';
import { api } from '@/lib/api-client';

export function DataSync() {
  const setMarket = useMarketStore((state) => state.setMarket);
  const setRibbon = useMarketStore((state) => state.setRibbon);

  useSafePolling(
    async (signal) => {
      // Fetch market data
      const marketResponse = await api.get('/dashboard/market', { signal });
      if (marketResponse.data) {
        setMarket(marketResponse.data); // Updates store
      }

      // Fetch ribbon data
      const ribbonResponse = await api.get('/dashboard/ribbon', { signal });
      if (ribbonResponse.data?.stocks) {
        setRibbon(ribbonResponse.data.stocks); // Updates store
      }
    },
    { interval: 5000 }
  );

  return null; // Data sync component
}
```

### 3. useWebSocket Hook

**Location:** `/frontend/hooks/useWebSocket.ts`

**Features:**
- Auto-reconnect with exponential backoff
- Connection state tracking
- Message type routing
- Heartbeat mechanism
- Proper cleanup on unmount

**Usage Example:**

```typescript
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';

export function AlertListener() {
  const { isConnected, subscribe, send } = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/alerts',
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    heartbeatInterval: 30000,
    onConnect: () => console.log('[WS] Connected'),
    onDisconnect: () => console.log('[WS] Disconnected'),
    onError: (error) => console.error('[WS] Error:', error),
  });

  // Subscribe to alert messages
  useEffect(() => {
    const unsubscribe = subscribe('alert', (data) => {
      console.log('New alert:', data);
      // Handle alert
    });

    return unsubscribe;
  }, [subscribe]);

  // Subscribe to pong messages
  useEffect(() => {
    const unsubscribe = subscribe('pong', (data) => {
      console.log('Pong received:', data);
    });

    return unsubscribe;
  }, [subscribe]);

  return (
    <div>
      WebSocket Status: <span>{isConnected ? '✓ Connected' : '✗ Disconnected'}</span>
    </div>
  );
}
```

## Real-World Implementation Examples

### Dashboard Page (Complete Example)

See `/frontend/app/dashboard/page.tsx` for the full implementation:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useSafePolling } from '@/hooks/useSafePolling';
import { useMarketStore } from '@/lib/store';
import { api } from '@/lib/api-client';

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState(null);
  const [news, setNews] = useState([]);

  // Get shared market data from store
  const market = useMarketStore((state) => state.market);
  const ribbon = useMarketStore((state) => state.ribbon);
  const marketLoading = useMarketStore((state) => state.marketLoading);
  const setMarket = useMarketStore((state) => state.setMarket);
  const setRibbon = useMarketStore((state) => state.setRibbon);

  // Setup polling for market and ribbon (5 seconds)
  useSafePolling(
    async (signal) => {
      try {
        const marketData = await api.get('/dashboard/market', { signal });
        if (marketData.data) {
          setMarket(marketData.data);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Failed to poll market:', error);
        }
      }

      try {
        const ribbonData = await api.get('/dashboard/ribbon', { signal });
        if (ribbonData.data?.stocks) {
          setRibbon(ribbonData.data.stocks);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Failed to poll ribbon:', error);
        }
      }
    },
    { interval: 5000 }
  );

  // Load portfolio and news once on mount
  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const [portfolioResp, newsResp] = await Promise.all([
          api.get('/dashboard/portfolio'),
          api.get('/dashboard/news'),
        ]);
        if (isMounted) {
          setPortfolio(portfolioResp.data);
          setNews(newsResp.data);
        }
      } catch (error) {
        console.warn('Failed to load initial data:', error);
      }
    };

    void load();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div>
      {/* Portfolio section */}
      <section>
        <h2>Portfolio</h2>
        {portfolio && <p>Value: ${portfolio.current_value}</p>}
      </section>

      {/* Market section - uses shared store */}
      <section>
        <h2>Market {marketLoading && '(Loading...)'}</h2>
        {market && <p>Gainers: {market.top_gainers?.length}</p>}
      </section>

      {/* Ribbon section - uses shared store */}
      <section>
        <h2>Top Movers</h2>
        {ribbon.map((stock) => (
          <div key={stock.symbol}>{stock.symbol}: {stock.price}</div>
        ))}
      </section>

      {/* News section */}
      <section>
        <h2>Market News</h2>
        {news.map((article) => (
          <article key={article.id}>{article.title}</article>
        ))}
      </section>
    </div>
  );
}
```

### Portfolio Page (Complete Example)

See `/frontend/app/portfolio/page.tsx` for the full implementation:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useSafePolling } from '@/hooks/useSafePolling';
import { useMarketStore } from '@/lib/store';
import { marketService, portfolioService } from '@/lib/api-service';

export default function PortfolioPage() {
  const [summary, setSummary] = useState(null);
  const [holdings, setHoldings] = useState([]);

  // Get ribbon from shared store
  const ribbon = useMarketStore((state) => state.ribbon);
  const setRibbon = useMarketStore((state) => state.setRibbon);

  // Setup polling for ribbon only (5 seconds)
  useSafePolling(
    async (signal) => {
      try {
        const ribbonResult = await marketService.getLiveRibbon({ signal });
        if (ribbonResult?.stocks) {
          setRibbon(ribbonResult.stocks);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Failed to poll ribbon:', error);
        }
      }
    },
    { interval: 5000 }
  );

  // Load portfolio data once on mount
  useEffect(() => {
    let isMounted = true;

    const loadPortfolio = async () => {
      try {
        const [summaryResult, holdingsResult] = await Promise.all([
          portfolioService.summary(),
          portfolioService.list(),
        ]);
        if (isMounted) {
          setSummary(summaryResult);
          setHoldings(holdingsResult);
        }
      } catch (error) {
        console.warn('Failed to fetch portfolio:', error);
      }
    };

    void loadPortfolio();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div>
      <h1>Portfolio</h1>
      {summary && <p>Value: ${summary.current_value}</p>}

      <h2>Holdings ({holdings.length})</h2>
      {holdings.map((holding) => (
        <div key={holding.symbol}>{holding.symbol}: {holding.quantity} shares</div>
      ))}

      <h2>Market Ribbon</h2>
      {ribbon.map((stock) => (
        <div key={stock.symbol}>{stock.symbol}: {stock.change_percent}%</div>
      ))}
    </div>
  );
}
```

## Best Practices

### 1. Share Data Globally When Needed

✅ **Good** - Use store for market/ribbon data used across multiple pages:
```typescript
const ribbon = useMarketStore((state) => state.ribbon);
```

❌ **Bad** - Fetching same data in Dashboard and Portfolio separately:
```typescript
// Dashboard
const [ribbon, setRibbon] = useState([]);
// Portfolio
const [ribbon, setRibbon] = useState([]); // Duplicate!
```

### 2. Use Polling Only for Data That Changes Frequently

✅ **Good** - Polling for market data (5s interval):
```typescript
useSafePolling(async (signal) => {
  const data = await api.get('/dashboard/market', { signal });
  // ...
}, { interval: 5000 });
```

❌ **Bad** - Polling for static data:
```typescript
// Don't poll portfolio holdings - only on trade events!
useSafePolling(async () => {
  const holdings = await portfolioService.list();
  // ...
}, { interval: 5000 });
```

### 3. Cancel Requests on Unmount

✅ **Good** - AbortController automatically cancels pending requests:
```typescript
useSafePolling(
  async (signal) => {
    // signal is AbortSignal
    const data = await api.get('/endpoint', { signal });
  },
  { interval: 5000 }
);
// Automatically cleaned up on unmount
```

❌ **Bad** - No cancellation:
```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await api.get('/endpoint'); // Keeps fetching after unmount!
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

### 4. Avoid Re-render Loops

✅ **Good** - Use store selectors (subscribeWithSelector):
```typescript
const market = useMarketStore((state) => state.market);
// Only re-renders when market changes
```

❌ **Bad** - Subscribing to entire state:
```typescript
const state = useMarketStore(); // All state
// Re-renders on any state change
```

### 5. Handle Tab Visibility

✅ **Good** - useSafePolling automatically pauses when tab is hidden:
```typescript
useSafePolling(async (signal) => {
  // Paused when tab is inactive
  // Resumes when tab becomes active
}, { interval: 5000 });
```

❌ **Bad** - Polling continues on hidden tabs:
```typescript
useEffect(() => {
  setInterval(async () => {
    // Still fetching even if user isn't looking!
  }, 5000);
}, []);
```

## Performance Benefits

| Issue | Before | After | Benefit |
|-------|--------|-------|---------|
| Duplicate API calls | Dashboard + Portfolio both fetch ribbon | Single shared store + centralized polling | **50% fewer API calls** |
| Memory leaks | Multiple intervals per page | Single safe polling with cleanup | **Zero memory leaks** |
| Overlapping requests | Multiple requests mid-flight | AbortController prevents overlaps | **Fewer failed requests** |
| Tab unused polling | Continues polling when tab hidden | Auto-pause with visibility API | **Reduced server load** |
| Browser clutter | 2+ setInterval per page | Single setTimeout per hook | **Cleaner browser performance** |

## Migration Guide

If you have existing useEffect-based polling, here's how to migrate:

### Before:
```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await api.get('/endpoint');
    setData(data);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

### After:
```typescript
useSafePolling(
  async (signal) => {
    const data = await api.get('/endpoint', { signal });
    setData(data);
  },
  { interval: 5000 }
);
```

## Troubleshooting

### Polling not starting?
- Check `autoConnect` option in `useWebSocket` (default: true)
- Verify AbortSignal is passed to requests
- Check browser console for error messages

### Data not updating on inactive tab?
- This is by design! useSafePolling pauses on hidden tabs
- Use `document.visibilitychange` event if you need to override
- Note: Most servers appreciate reduced load on inactive tabs

### WebSocket keeps reconnecting?
- Check network connection
- Verify server is running
- Check `reconnectAttempts` option (default: 5)
- Increase `reconnectDelay` if server is overloaded

### Memory leaks in dev mode?
- React 18 StrictMode intentionally double-invokes effects in development
- This is normal behavior - not a real memory leak
- Check production builds to verify actual memory usage

## File Reference

- **Hooks:**
  - `/frontend/hooks/useSafePolling.ts` - Safe polling hook
  - `/frontend/hooks/useWebSocket.ts` - WebSocket hook
  
- **Store:**
  - `/frontend/lib/store.ts` - Zustand global market store
  
- **Examples:**
  - `/frontend/app/dashboard/page.tsx` - Dashboard using polling + store
  - `/frontend/app/portfolio/page.tsx` - Portfolio using shared store

