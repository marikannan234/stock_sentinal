# Production System Validation Guide

## Overview
This guide helps you validate that all production system components are working correctly.

---

## Pre-Integration Validation

### ✓ All Files Exist
```bash
# Run this to verify all new files are present:

ls -la frontend/lib/config.ts
ls -la frontend/lib/store-v2.ts
ls -la frontend/lib/websocket-manager.ts
ls -la frontend/lib/multi-tab-lock.ts
ls -la frontend/hooks/useSafePollingV2.ts
ls -la frontend/components/providers/error-boundary-provider.tsx
ls -la frontend/components/providers/data-sync-provider-v2.tsx
ls -la frontend/.env.staging
ls -la frontend/.env.production
```

All should return file info (not "file not found").

### ✓ TypeScript Compilation
```bash
npm run type-check
```

Expected output:
```
✓ No errors
✓ No warnings (except maybe ignored warnings)
✓ Exits with code 0
```

### ✓ Linting
```bash
npm run lint
```

Expected output:
```
✓ No errors
✓ No critical warnings
✓ Exits with code 0
```

---

## Post-Integration Validation

### ✓ Build Succeeds
```bash
npm run build
```

Expected output:
```
✓ No build errors
✓ ".next" folder created
✓ Exits with code 0
```

### ✓ Import Paths Work
In VS Code, verify these resolve correctly:
- `@/lib/config`
- `@/lib/store-v2`
- `@/lib/websocket-manager`
- `@/lib/multi-tab-lock`
- `@/hooks/useSafePollingV2`
- `@/components/providers/error-boundary-provider`
- `@/components/providers/data-sync-provider-v2`

No red squiggles under imports.

---

## Runtime Validation - Single Tab

### Test 1: App Starts Without Errors
1. Run `npm run dev`
2. Open http://localhost:3000
3. Check browser console
4. **Should see NO errors**, only:
   - Normal Next.js messages
   - Maybe: "[Config] Production config loaded" or similar

### Test 2: Data Loads
1. Dashboard page should show ribbon data
2. Market data should appear
3. No "loading" or error fallback UI
4. **Expected**: Data displayed normally

### Test 3: Error Boundary Works
1. Force a component error (break a component intentionally)
2. Page should show error UI instead of crashing
3. See: "Something went wrong" with error details
4. Should have "Try Again" and "Reload Page" buttons
5. **Expected**: Graceful fallback UI, not blank page

---

## Runtime Validation - Multi-Tab

### Test 1: Primary Tab Detection
1. Open Tab A: Dashboard
2. Open browser console
3. Look for one of these messages:
   - "[Lock] PRIMARY TAB" 
   - "[Lock] SECONDARY TAB"
4. **Expected**: Exactly ONE tab should show "PRIMARY"

### Test 2: Verify Only Primary Polls
1. Ensure Tab A shows "PRIMARY TAB" in console
2. Open Network tab
3. Filter by `top-movers` API calls
4. Initially: Should see some API calls from Tab A
5. Open Tab B (secondary)
6. Network should still show calls only from Tab A (~1 per 5s)
7. Tab B console should show "SECONDARY TAB"
8. **Expected**: No increase in API call frequency despite 2 tabs

### Test 3: Multi-Tab Data Sync
1. Keep both tabs open
2. In Tab A Network tab, watch for `market-snapshot` response
3. Wait for response to complete
4. Check Tab B - should show same data
5. No additional API call in Tab B
6. **Expected**: Data synchronized without duplicate calls

### Test 4: Tab Closing & Takeover
1. Close Tab A (the primary tab)
2. Go to Tab B console
3. Should see message like "[Lock] SECONDARY TAB" → "[Lock] PRIMARY TAB"
4. Open Network tab in Tab B
5. Should start seeing API calls again (~1 per 5s)
6. **Expected**: Automatic primary tab takeover

### Test 5: LocalStorage Lock
1. Open Tab A and Tab B
2. Open browser DevTools → Application → LocalStorage
3. Look for key: `stock-sentinel:tab-lock`
4. Should see JSON like: `{"tabId": "tab-1234-xyz", "timestamp": 1234567890}`
5. Open Tab C
6. Should still see the SAME lock (from primary tab)
7. **Expected**: Single lock across all tabs

---

## WebSocket Validation

### Test 1: WebSocket Connects
1. Open Dashboard
2. Open DevTools → Network tab
3. Filter: `ws://` or `wss://`
4. Should see WebSocket connection line
5. Status: 101 Switching Protocols (green)
6. **Expected**: WebSocket connection established

### Test 2: WebSocket Receives Messages
1. Keep WebSocket open (from Test 1)
2. Click "Messages" subtab on WebSocket
3. Should see incoming messages for:
   - ribbon updates
   - market updates
   - news updates
4. No red error frames
5. **Expected**: Steady message flow (depends on server)

### Test 3: Polling Stops When WebSocket Connected
1. Complete Test 1 & 2 (confirm WS connected)
2. Open Network tab (HTTP requests only)
3. Filter: `api` or your API path
4. Observe: Should see NO API calls
5. **Expected**: Zero polling while WS connected

### Test 4: Polling Resumes on WebSocket Disconnect
1. Chrome DevTools: Network Conditions → Disconnect
2. Or disable WebSocket in DevTools (Network → WebSocket → block)
3. Open Network (HTTP) tab
4. Should start seeing API calls every ~5 seconds
5. API URLs like: `/api/stocks/top-movers`, `/api/stocks/market-snapshot`
6. **Expected**: Automatic fallback to polling

### Test 5: Polling Stops on WebSocket Reconnect
1. Resume WebSocket (enable network)
2. Page should reconnect
3. API calls should stop
4. **Expected**: Automatic switch back to WebSocket

---

## Configuration Validation

### Test 1: Development Config
1. Check `.env.local` has correct values:
   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
   NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/ws
   NEXT_PUBLIC_ENABLE_LOGGING=true
   ```

2. Run app
3. Open console
4. Should see detailed logs like:
   - `[Config] Environment: development`
   - `[WS] Connecting to ws://localhost:8000/ws`
   - `[Poll] Fetching: http://localhost:8000/api/...`
5. **Expected**: Verbose logging

### Test 2: Staging Config
1. Build with staging env: `npm run build`
2. Look in `.next/server/pages` for env values
3. Should have staging URLs, not dev
4. **Expected**: Correct URLs for staging

### Test 3: Production Config
1. Production build won't show DEBUG logs
2. `NEXT_PUBLIC_ENABLE_LOGGING=false`
3. Console should be QUIET (no verbose logs)
4. Only errors if they occur
5. **Expected**: Silent operation in prod

---

## Performance Validation

### Test 1: Page Load Time
1. Open Dashboard in new incognito tab
2. DevTools → Performance → Start recording
3. Record full page load
4. Stop recording
5. Check: Largest Contentful Paint (LCP) < 2.5s
6. Check: Cumulative Layout Shift (CLS) < 0.1
7. **Expected**: All within Web Vitals targets

### Test 2: Memory Usage
1. Open DevTools → Memory tab
2. Click camera icon to take heap snapshot
3. Note size (should be ~50-80MB on Dashboard)
4. Let page run for 15 minutes with periodic data updates
5. Take another snapshot
6. Size should NOT significantly increase
7. **Expected**: Stable memory, no growth over time

### Test 3: CPU Usage
1. Open DevTools → Performance tab
2. Record for 30 seconds while page is idle
3. Check CPU usage graph
4. Should be mostly flat, near 0%
5. Spikes only when data updates
6. **Expected**: Low CPU when idle, brief spikes on updates

### Test 4: Network Efficiency
1. Two tabs open
2. Record Network for 60 seconds
3. Count API calls in Network tab
4. Expected: ~12 calls (one per 5s × 60s ÷ 5s)
5. NOT ~24 calls (which would mean 2 tabs polling)
6. **Expected**: Single set of calls regardless of tab count

### Test 5: Data Sync Latency
1. Monitor WebSocket Messages (from WS validation test)
2. Note timestamp of message
3. Check store updates (use React DevTools or console log)
4. Latency: timestamp difference should be < 500ms
5. **Expected**: < 500ms for WebSocket, < 5s for polling

---

## Error Handling Validation

### Test 1: Missing API (404)
1. Temporarily change API URL in config
2. Set invalid URL: `http://localhost:8000/invalid/path`
3. Watch console for error logs
4. Should see: `[Poll] Error: HTTP 404`
5. Page should still show cached/previous data
6. **Expected**: Graceful degradation, not crash

### Test 2: Network Timeout
1. Use DevTools Throttling: Set to "Offline"
2. Wait for timeout
3. Should see error logs
4. Polling should retry with backoff
5. UI should still be responsive
6. Restore network - should recover
7. **Expected**: Recovery after network restoration

### Test 3: Component Error
1. Break a component intentionally (e.g., `return undefined`)
2. Page should catch error
3. Show error boundary UI
4. Should NOT crash to blank screen
5. Other parts of page should still work
6. **Expected**: Error boundary catches and displays gracefully

### Test 4: Monitoring Integration
1. Check if monitoring is enabled: `NEXT_PUBLIC_ENABLE_MONITORING=true`
2. Trigger an error
3. If monitoring service configured, error should be tracked
4. Check monitoring dashboard
5. **Expected**: Error appears in monitoring dashboard

---

## Store Validation

### Test 1: Data in Store
In browser console (DevTools → Console):
```javascript
// Check store has data
const state = window.__store__; // If exposed for dev
console.log(state);

// Or via React DevTools:
// Select component → Hooks → useMarketStore → state {}
```

Store should have:
```javascript
{
  ribbon: Array,
  market: Array,
  news: Array,
  ribbonTimestamp: number,
  marketTimestamp: number,
  newsTimestamp: number,
  isWebSocketConnected: boolean,
  isPollingActive: boolean,
  isPollingSuspended: boolean,
  // ... error states
}
```

### Test 2: Store Subscribe
In DevTools Console:
```javascript
// This should work if store is properly integrated
// Check if components are reading from store
const state = useMarketStore.getState();
console.log(state.ribbon); // Should have data
```

### Test 3: Store Broadcast
1. Open two tabs
2. Update store in Tab A (if possible)
3. Monitor Tab B store
4. Should see same data shortly after
5. **Expected**: Cross-tab sync working

---

## Browser Compatibility

Test on these browsers:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

Expected:
- ✓ All data loads
- ✓ WebSocket connects
- ✓ Multi-tab sync (except Safari mobile - single window)
- ✓ No console errors
- ✓ Performance acceptable

Note: Some features may degrade:
- BroadcastChannel not in older browsers (falls back gracefully)
- WebSocket might not connect on some networks

---

## Integration Testing Checklist

After integration, verify:

- [ ] Root layout has ErrorBoundaryProvider
- [ ] Root layout has DataSyncProvider
- [ ] All pages import from `store-v2` not `store`
- [ ] No TypeScript errors
- [ ] App builds successfully
- [ ] No runtime errors on load
- [ ] Data displays correctly
- [ ] WebSocket connects (if configured)
- [ ] Polling works (if WS unavailable)
- [ ] Multi-tab sync works
- [ ] Error boundary catches errors
- [ ] Environment variables load correctly
- [ ] Performance targets met
- [ ] All browsers working

---

## Deployment Readiness Checklist

Before going to production:

- [ ] Staging deployment passes validation (24+ hours)
- [ ] All performance metrics acceptable
- [ ] No critical issues found
- [ ] Team trained on new system
- [ ] Monitoring configured
- [ ] Rollback procedures documented
- [ ] Communication plan ready
- [ ] On-call team prepared
- [ ] Backup plan ready

---

## Quick Debug Commands

If something's wrong, try these in browser console:

```javascript
// Check WebSocket status
getWebSocketManager().getStatus()

// Check tab lock status
getTabLock().getIsPrimary()

// Check store data
useMarketStore.getState()

// Manual store update (for testing)
useMarketStore.getState().setRibbon(data, 'manual')

// Check config
console.log(config)

// Enable detailed logging (if available)
// Check .env file has NEXT_PUBLIC_ENABLE_LOGGING=true
```

---

## Success Indicators

System is working correctly when you see:
- ✅ "[Lock] PRIMARY TAB" in exactly ONE tab's console
- ✅ "[WS] Connected" in console (if WebSocket available)
- ✅ Stable data across all tabs
- ✅ API call frequency matches configuration (~1 per 5s)
- ✅ Zero errors in console
- ✅ Memory stable over time
- ✅ Page responsive and fast

---

## Next Steps if Issues Found

1. **Identify the problem** using this guide
2. **Check relevant log** in browser console
3. **Review the component code** for that feature
4. **Test in staging** before production
5. **Report findings** and iterate

All production system code was designed to be:
- Debuggable (detailed logging)
- Replaceable (modular design)
- Testable (clear responsibilities)
- Monitorable (comprehensive tracking)

You should be able to pinpoint issues quickly using the above validation steps.

---

## You're Ready! ✅

If all validation steps pass, your production system is working correctly and ready for deployment.
