# Stock Sentinel - Remediation Guide

## Apply These Fixes Immediately

---

## FIX #1: Add Axios Request Timeout (5 min)

**File:** `frontend/lib/api-client.ts`

Replace the axios creation:
```typescript
export const api = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: false,
  timeout: 10000,  // ADD THIS LINE - 10 second timeout
});
```

Also add interceptor for safety:
```typescript
api.interceptors.request.use((config) => {
  if (!config.timeout) {
    config.timeout = 10000;
  }
  return config;
});
```

---

## FIX #2: Propagate Scheduler Errors (5 min)

**File:** `backend/app/main.py` (around line 76)

**Current:**
```python
try:
    start_scheduler()
except Exception as e:
    logger.error(f"Failed to start background scheduler: {e}")
```

**Change to:**
```python
try:
    start_scheduler()
except Exception as e:
    logger.error(
        f"Failed to start background scheduler: {e}",
        exc_info=True
    )
    # In production, fail loudly
    if settings.ENVIRONMENT == "production":
        raise RuntimeError(
            "Scheduler initialization required for production. "
            "Alerts cannot run without the background scheduler."
        ) from e
    # In dev/staging, allow startup but warn
    logger.warning("Continuing startup without scheduler - alerts disabled!")
```

---

## FIX #3: Prevent Concurrent Fetch Requests (10 min)

**File:** `frontend/hooks/useSafePollingV2.ts`

Add this ref after line 60:
```typescript
const isRequestInFlight = useRef(false);
```

Modify the `fetchData` function (around line 95):
```typescript
const fetchData = useCallback(async (): Promise<void> => {
  if (!isMounted.current) return;
  if (!shouldPollNow()) {
    logger.debug('[POLL] Skipping - WebSocket or condition check failed');
    return;
  }

  // ADD THIS CHECK - Prevent concurrent requests
  if (isRequestInFlight.current) {
    logger.debug('[POLL] Request already in flight, skipping');
    return;
  }

  isRequestInFlight.current = true;

  let requestSuccess = false;

  try {
    // ... existing fetch logic ...
  } finally {
    isRequestInFlight.current = false;  // ADD THIS LINE
  }
}, [url, shouldPollNow]);
```

---

## FIX #4: Clean Up All Timers on Unmount (10 min)

**File:** `frontend/hooks/useAlertNotifications.ts`

Complete the cleanup in useEffect. Find this around line 140:
```typescript
useEffect(() => {
  connectRef.current();
  // Missing: cleanup function
}, []);
```

**Change to:**
```typescript
useEffect(() => {
  connectRef.current();
  
  return () => {
    // Clean up all timers on unmount
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = undefined;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
}, []);
```

---

## FIX #5: Clear Intervals in useSafePollingV2 (10 min)

**File:** `frontend/hooks/useSafePollingV2.ts`

Add cleanup to the main useEffect. Find where the interval is set (around line 145), add this:

```typescript
useEffect(() => {
  if (!isMounted.current) return;
  if (!shouldPollNow()) return;

  // Existing fetchData call logic...

  return () => {
    // CRITICAL: Clear all timers when deps change
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (requestTimeoutRef.current) clearTimeout(requestTimeoutRef.current);
    intervalRef.current = null;
    timeoutRef.current = null;
    requestTimeoutRef.current = null;
    
    // Also abort any in-flight request
    if (abortController.current) {
      abortController.current.abort();
    }
  };
}, [url, shouldPollNow, customShouldPoll]); // Include all deps
```

---

## FIX #6: Add Null Check for Alert Type (15 min)

**File:** `backend/app/services/alert_service.py`

After fetching an alert from database, add validation. Find where you query alerts (around line 200):

```python
# After fetching alert
alert = db.query(Alert).filter(Alert.id == alert_id).first()

# ADD THIS CHECK
if alert is None:
    raise AlertNotFoundError(alert_id)

# Defensive check for corrupt database state
if alert.alert_type is None:
    logger.error(
        f"Alert {alert.id} has NULL alert_type, auto-fixing to PRICE",
        extra={"user_id": alert.user_id}
    )
    alert.alert_type = AlertType.PRICE
    db.commit()
```

---

## FIX #7: Notify Clients When Stream Fails (15 min)

**File:** `backend/app/ws/price_streamer.py`

Replace line 120 with:
```python
# Stop streaming if too many consecutive errors
if consecutive_errors >= max_consecutive_errors:
    logger.critical(
        f"Stopping stream for {symbol} after {consecutive_errors} consecutive errors"
    )
    # Notify clients of failure
    try:
        await callback(symbol, {
            "type": "stream_error",
            "symbol": symbol,
            "message": f"Stream stopped after {consecutive_errors} errors",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": None,
        })
    except Exception as e:
        logger.error(f"Failed to notify clients of stream failure: {e}")
    break
```

---

## FIX #8: Enhance Database Session Cleanup (20 min)

**File:** `backend/app/db/session.py`

Replace the `get_db()` function:
```python
def get_db():
    """
    Dependency that provides a database session with proper error handling.
    Ensures session is always cleaned up, even on exception.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Log and rollback on any exception
        logger.error(
            f"Database error, rolling back transaction",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        db.rollback()
        raise  # Re-raise so caller knows there was an error
    finally:
        # Always close, even if error occurred
        try:
            db.close()
        except Exception as e:
            logger.warning(
                f"Error closing database session",
                extra={"error": str(e)},
                exc_info=True
            )
```

---

## FIX #9: Multi-Tab Lock - Verify Write Success (20 min)

**File:** `frontend/lib/multi-tab-lock.ts`

Replace the `checkLock()` method:
```typescript
private checkLock(): boolean {
  try {
    const stored = localStorage.getItem(LOCK_KEY);
    const now = Date.now();

    if (!stored) {
      // Try to write
      this.writeLock();
      
      // Verify we actually got it (atomic check)
      const verify = localStorage.getItem(LOCK_KEY);
      if (!verify) return false; // Lost race
      
      try {
        const verifyLock: TabLock = JSON.parse(verify);
        return verifyLock.tabId === this.tabId;
      } catch (e) {
        logger.error('[Lock] Failed to parse lock:', e);
        return false;
      }
    }

    const lock: TabLock = JSON.parse(stored);

    // Check if lock is expired
    if (now - lock.timestamp > LOCK_TTL) {
      logger.debug('[Lock] Previous lock expired, trying to acquire');
      this.writeLock();
      
      // Verify we got it
      const verify = localStorage.getItem(LOCK_KEY);
      if (!verify) return false;
      const verifyLock: TabLock = JSON.parse(verify);
      return verifyLock.tabId === this.tabId;
    }

    // Check if we already hold the lock
    if (lock.tabId === this.tabId) {
      logger.debug('[Lock] Refreshing lock');
      this.writeLock();
      return true;
    }

    // Another tab has the lock
    return false;
  } catch (error) {
    logger.error('[Lock] Check failed:', error);
    return false;
  }
}
```

---

## FIX #10: Fix Dedup Cache to Skip Abortable Requests (15 min)

**File:** `frontend/lib/api-client.ts`

Replace the `api.get` override:
```typescript
const originalGet = api.get.bind(api);
api.get = ((url: string, config?: any) => {
  // Don't cache if AbortSignal provided - can't reuse aborted requests
  if (config?.signal) {
    return originalGet(url, config);
  }
  
  const cacheKey = `${url}${JSON.stringify(config?.params || {})}`;
  const cached = requestCache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TIME_MS) {
    // Return cached promise if still fresh
    logger.debug('[Cache] Returning cached request', { url });
    return cached.promise;
  }
  
  // Make new request and cache it
  const promise = originalGet(url, config);
  requestCache.set(cacheKey, { timestamp: Date.now(), promise });
  
  // Clean up old cache entries
  if (requestCache.size > 50) {
    const now = Date.now();
    for (const [key, value] of requestCache.entries()) {
      if (now - value.timestamp > CACHE_TIME_MS * 2) {
        requestCache.delete(key);
      }
    }
  }
  
  return promise;
}) as typeof api.get;
```

---

## Testing These Fixes

### Unit Test Examples

**Test useSafePollingV2 cleanup:**
```typescript
test('clears all timers on unmount', () => {
  const { unmount } = renderHook(() =>
    useSafePolling({ url: '/test', interval: 1000 })
  );
  
  // Verify timers exist
  expect(setInterval).toHaveBeenCalled();
  
  unmount();
  
  // Verify timers cleared
  expect(clearInterval).toHaveBeenCalled();
});
```

**Test concurrent request prevention:**
```typescript
test('prevents concurrent requests', async () => {
  const { result } = renderHook(() =>
    useSafePolling({ url: '/test' })
  );
  
  // Trigger fetch
  await act(async () => {
    result.current.fetch();
  });
  
  // Try to trigger again immediately
  const fetchAgain = result.current.fetch();
  
  // Should skip
  expect(fetchAgain).toBeNaN(); // Returns without doing work
});
```

### Integration Tests

**Test WebSocket fallback:**
```typescript
test('falls back to polling when WebSocket fails', async () => {
  const { rerender } = render(<DataSyncProvider><TestComponent /></DataSyncProvider>);
  
  // Simulate WebSocket connection error
  act(() => {
    useMarketStore.getState().setWebSocketConnected(false);
  });
  
  // Verify polling active
  expect(mockPollingRequest).toHaveBeenCalled();
});
```

---

## Verification Checklist

After applying each fix:
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No ESLint errors: `npm run lint`
- [ ] Tests pass: `npm test`
- [ ] Built successfully: `npm run build`

---

## Monitoring After Deployment

Monitor these metrics:
1. **Memory usage** - Should not grow over time
2. **Request count** - Should not spike during idle
3. **WebSocket connections** - Should be stable
4. **Database connections** - Should pool correctly
5. **Error rate** - Should be near 0

Set up alerts for:
- Memory growth > 100MB/hour
- Request timeout rate > 1%
- Database connection pool exhaustion
- WebSocket reconnection storms
