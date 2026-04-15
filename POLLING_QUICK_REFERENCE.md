# Polling Architecture Quick Reference

## Single Polling Loop (DataSyncProvider)

**Location:** `components/providers/data-sync-provider-v2.tsx`

### Polling Endpoints
| Endpoint | Interval | Component | Data Flow |
|----------|----------|-----------|-----------|
| `/stocks/top-movers` | 5s | RibbonPolling | → store.ribbon |
| `/stocks/market-snapshot` | 5s | MarketPolling | → store.market |
| `/news/headlines` | 10s | NewsPolling | → store.news |

### Polling Rules
- Primary tab only (multi-tab lock)
- Stops if WebSocket connected
- Resumes on visibility change
- 5-second timeout per request
- 5 retries max per request
- Exponential backoff on errors

---

## Global State Management

**Location:** `lib/store-v2.ts`

### What to Use
```typescript
// ✅ All pages should use this
import { useMarketStore } from '@/lib/store-v2';

export default function MyPage() {
  const ribbon = useMarketStore((state) => state.ribbon);
  const market = useMarketStore((state) => state.market);
  const news = useMarketStore((state) => state.news);
  
  const isRibbonLoading = useMarketStore((state) => state.isRibbonLoading);
  const isMarketLoading = useMarketStore((state) => state.isMarketLoading);
  const isNewsLoading = useMarketStore((state) => state.isNewsLoading);
  
  return <div>{/* render using global data */}</div>;
}
```

### What NOT to Do
```typescript
// ❌ DON'T make duplicate API calls
const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
useEffect(() => {
  marketService.getLiveRibbon() // ← AVOID! Already polled globally
    .then(setRibbon);
}, []);
```

---

## Pages Using Global Store

✅ **Dashboard** - Reads market + ribbon from store  
✅ **Portfolio** - Reads portfolio (not polled) + uses store  
✅ **Watchlist** - Reads market + ribbon from store  
✅ **Trade-history** - Reads ribbon from store  
✅ **Alerts** - Reads ribbon from store  

---

## API Call Patterns

### For Shared Data (ribbon, market, news)
```typescript
// ✅ USE GLOBAL STORE
const ribbon = useMarketStore((state) => state.ribbon);
```

### For Page-Specific Data (portfolio, alerts, etc.)
```typescript
// ✅ USE DIRECT API CALLS (on mount only)
useEffect(() => {
  let isMounted = true;
  
  portfolioService.summary().then(data => {
    if (isMounted) setSummary(data);
  });
  
  return () => { isMounted = false; };
}, []); // Empty dependency - runs once
```

### For Real-time Alerts
```typescript
// ✅ USE WEBSOCKET (already set up)
// /ws/alerts is handled by WebSocketInitializer
// Messages automatically update store + trigger notifications
```

---

## Multi-Tab Synchronization

- Primary tab: Polls APIs → updates store
- Secondary tabs: Listen via BroadcastChannel → stay in sync
- No polling in secondary tabs (saves resources)
- Uses localStorage for persistence

---

## Adding New Polling Sources

If you need to poll a new endpoint:

1. **Create new polling component:**
```typescript
function CustomPolling() {
  const isPrimary = useTabLock();
  const setCustom = useMarketStore((state) => state.setCustom);
  
  const handleData = useCallback(
    (data: any) => {
      setCustom(data, 'polling');
    },
    [setCustom]
  );

  useSafePolling({
    url: `${config.API_BASE_URL}/custom/endpoint`,
    onData: handleData,
    onError: (err) => console.error(err),
    interval: 5000, // 5 seconds
    shouldPoll: () => isPrimary,
  });

  return null;
}
```

2. **Add setter to store:**
```typescript
// In store-v2.ts
setCustom: (data: CustomType[], source: 'websocket' | 'polling' = 'polling') =>
  set((state) => ({
    custom: data,
    customTimestamp: Date.now(),
    customError: null,
    isCustomLoading: false,
    lastUpdateSource: source,
  })),
```

3. **Add to DataSyncProvider:**
```typescript
// In data-sync-provider-v2.tsx
<CustomPolling />
```

4. **Use in pages:**
```typescript
const custom = useMarketStore((state) => state.custom);
```

---

## Debugging Tips

### Check Active Polling
```typescript
// In browser console
// Should see only 3 polling logs per 5 seconds:
// [POLL] Fetching: .../stocks/top-movers
// [POLL] Fetching: .../stocks/market-snapshot
// [POLL] Fetching: .../news/headlines
```

### Verify Single Store
```typescript
// Should return same reference
import { useMarketStore } from '@/lib/store-v2';
const store1 = useMarketStore();
const store2 = useMarketStore();
store1 === store2; // Should be true
```

### Check Multi-Tab Sync
```typescript
// Open 2 tabs, in Tab A console:
useMarketStore.subscribe(
  (state) => state.ribbon,
  (ribbon) => console.log('Ribbon updated:', ribbon)
);
// Now update data in Tab B - should log in Tab A
```

### Monitor Store Changes
```typescript
// Log every state change
useMarketStore.subscribe(
  (state) => state,
  (state) => console.log('Store changed:', state)
);
```

---

## Common Mistakes to Avoid

❌ **Calling API directly in useEffect without dependency array:**
```typescript
useEffect(() => {
  marketService.getLiveRibbon().then(setRibbon);
  // Runs on every render!
});
```

✅ **Use empty dependency array:**
```typescript
useEffect(() => {
  marketService.getLiveRibbon().then(setRibbon);
}, []); // Runs once on mount
```

---

❌ **Including unstable functions in dependencies:**
```typescript
const fetchData = () => marketService.getData();

useEffect(() => {
  fetchData();
}, [fetchData]); // fetchData is new every render!
```

✅ **Use useCallback for stable references:**
```typescript
const fetchData = useCallback(() => {
  marketService.getData();
}, []); // Stable reference

useEffect(() => {
  fetchData();
}, []); // Fine with empty dependency
```

---

❌ **Creating multiple polling instances:**
```typescript
// Wrong - every component creates own interval
function Page1() {
  useEffect(() => {
    const interval = setInterval(() => fetch('/api'), 5000);
    return () => clearInterval(interval);
  }, []);
}

function Page2() {
  useEffect(() => {
    const interval = setInterval(() => fetch('/api'), 5000);
    return () => clearInterval(interval);
  }, []);
}
```

✅ **Use single DataSyncProvider:**
```typescript
// Correct - one provider at top
<DataSyncProvider>
  <Page1 /> {/* reads from store */}
  <Page2 /> {/* reads from store */}
</DataSyncProvider>
```

---

## Performance Metrics

**Target:**
- [ ] Max 1 API call per endpoint per interval
- [ ] No duplicate interval registrations
- [ ] Memory stable (no accumulating timers)
- [ ] UI updates within 100ms
- [ ] No console errors related to polling

---

## Support

For issues related to polling:
1. Check browser console for `[POLL]` logs
2. Open DevTools Network tab - verify single calls
3. Check store-v2.ts for data structure
4. Verify component uses correct store selector
5. Check if WebSocket is connected (affects polling)

---

Last Updated: April 13, 2026
