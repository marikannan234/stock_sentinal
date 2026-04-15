# Stock Sentinel Code Audit - Quick Reference

## 📊 Overview
- **Total Issues:** 28
- **CRITICAL (Must Fix):** 8
- **WARNING (High Priority):** 10
- **INFO (Best Practice):** 10

---

## 🔴 CRITICAL ISSUES - MUST FIX BEFORE PRODUCTION

### Backend
| # | Issue | File | Fix Time | Impact |
|---|-------|------|----------|--------|
| 1 | Scheduler exception not propagated to app | `main.py:76` | 5 min | App starts without alerts |
| 5 | Price streamer stops silently on errors | `price_streamer.py:120` | 10 min | WebSocket data stops |
| 6 | Alert.alert_type can be NULL | `alert_service.py:150` | 15 min | Alert checking crashes |
| 8 | DB session cleanup edge case | `session.py:35` | 20 min | Connection pool leak |

### Frontend
| # | Issue | File | Fix Time | Impact |
|---|-------|------|----------|--------|
| 2 | Memory leak: orphaned intervals | `useSafePollingV2.ts:150` | 15 min | CPU spike, duplicates |
| 3 | Memory leak: uncleaned timeouts | `useAlertNotifications.ts:90` | 10 min | Memory exhaustion |
| 4 | Race: concurrent fetch requests | `useSafePollingV2.ts:100` | 20 min | State corruption |
| 7 | Missing axios timeout | `api-client.ts:5` | 5 min | Hung requests |

---

## 🟡 WARNING ISSUES - HIGH PRIORITY

### Must Fix This Sprint
1. **Dedup cache race** (`api-client.ts:35`) - Returns stale data on concurrent requests
2. **Multi-tab lock race** (`multi-tab-lock.ts:60`) - Two tabs acquire lock simultaneously
3. **Store concurrent updates** (`store-v2.ts:100`) - Inconsistent state under race
4. **WebSocket init silently fails** (`data-sync-provider-v2.tsx:140`) - Polling doesn't fallback

### Should Fix This Sprint
5. **Clock adjustment in cache** (`news_service.py:30`) - Stale cache on system clock change
6. **Dashboard no partial data** (`dashboard.py:90`) - No indication of timeouts
7. **Stale handlers on reconnect** (`useWebSocket.ts:85`) - Old data in new connection
8. **No alert data validation** (`connection_manager.py:60`) - JSON serialization crashes
9. **No error reporting** (`error-boundary.tsx:25`) - Errors go unnoticed
10. **Stale token accepted** (`session-bootstrap.tsx`) - Revoked tokens used

---

## ℹ️ INFO ISSUES - BEST PRACTICES

1. **Error format inconsistency** - Different routes use different formats
2. **No axios retry logic** - Network glitches cause immediate failures
3. **BroadcastChannel unsafe parsing** - No error handling for corrupted messages
4. **No timeout interceptor** - One-off requests can hang
5. **Scheduler no queue** - Missed alerts if check takes > 30s
6. **Inconsistent logging** - Mix of direct logging and extra dicts
7. **No Suspense boundaries** - Multiple loading states needed
8. **No TypeScript strict** - Type errors not caught
9. **Health endpoint hammered** - No caching/rate-limiting
10. **useCallback not optimized** - Unnecessary re-renders

---

## ✅ QUICK FIX CHECKLIST

### Day 1 (Critical Fixes - 2 hours)
```
☐ [5 min]  Add axios timeout: config.API_BASE_URL timeout: 10000
☐ [5 min]  Propagate scheduler errors in main.py
☐ [10 min] Add is_in_flight check to useSafePollingV2.fetchData
☐ [10 min] Clear all timeouts in useAlertNotifications.useEffect cleanup
☐ [15 min] Add defensive null check for Alert.alert_type
☐ [20 min] Enhance DB session cleanup in session.py
☐ [15 min] Add client notification to price_streamer stream failure
```

### Day 2 (High-Value Warnings - 2 hours)
```
☐ [20 min] Fix multi-tab lock race condition
☐ [15 min] Fix dedup cache to skip AbortSignal requests
☐ [10 min] Add atomic transaction to useMarketStore.setMarket
☐ [20 min] Add error handling to WebSocket init in DataSyncProvider
☐ [15 min] Add alert data validation to connection_manager.broadcast_alert
```

---

## 🎯 Most Important Fixes (by Impact)

1. **Axios timeout** - Prevents hung requests (5 min, high impact)
2. **Memory leaks** - Prevents crashes after hours of use (25 min, high impact)
3. **Race conditions** - Fixes data corruption (40 min, critical)
4. **Error handling** - Prevents silent failures (30 min, critical)

---

## 📈 Testing Recommendations

### Unit Tests to Add
- [ ] Test useSafePollingV2 cleanup on unmount
- [ ] Test useAlertNotifications timeout cleanup
- [ ] Test multi-tab lock atomicity
- [ ] Test concurrent store updates

### Integration Tests to Add
- [ ] Test WebSocket fallback to polling
- [ ] Test dashboard timeout handling
- [ ] Test alert creation with various enum states
- [ ] Test request deduplication

### Load Tests to Add
- [ ] Polling under high frequency (~1000 req/sec)
- [ ] WebSocket broadcast with 100+ subscribers
- [ ] Multi-tab coordination under race conditions
- [ ] Store concurrency updates from multiple sources

---

## 📋 Deployment Checklist

Before going to production:
```
☐ All 8 CRITICAL issues fixed
☐ Tests passing for critical fixes
☐ Load test: polling @ 2000 req/sec for 1 hour - no memory growth
☐ Load test: WebSocket 100+ connections, malformed broadcasts handled
☐ Monitoring in place for:
  - Request timeout rate
  - WebSocket connection errors
  - Alert scheduler duration
  - Memory usage over time
☐ Error reporting configured
☐ Logging rotation configured
☐ Database connection pool tuned
☐ API timeouts configured in all services
```

---

## 📚 Related Documentation
- Full detailed audit: [CODE_AUDIT_COMPREHENSIVE.md](CODE_AUDIT_COMPREHENSIVE.md)
- Configuration: [backend/.env](backend/.env) and [frontend/.env.local](frontend/.env.local)
- Architecture: See project documentation files
