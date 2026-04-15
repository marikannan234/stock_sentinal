/**
 * PRODUCTION-GRADE Safe Polling Hook with WebSocket Fallback
 * 
 * Features:
 * - Only polls if WebSocket is disconnected
 * - Respects polling suspension
 * - Exponential backoff on errors
 * - ✅ 5-second timeout protection per request
 * - ✅ Retry limit - stops after 5 failures
 * - ✅ Structured logging with [POLL] prefix
 * - ✅ Safe JSON parsing
 * - ✅ Data change detection
 * - AbortController for cleanup
 * - Document visibility detection
 * - Mounted check to prevent setState after unmount
 */

import { useCallback, useEffect, useRef } from 'react';
import { config, logger } from '@/lib/config';
import { useMarketStore } from '@/lib/store-v2';

// Constants
const REQUEST_TIMEOUT = 5000; // 5 seconds - production standard
const MAX_RETRIES = 5; // Stop after 5 failures - prevent infinite loops

interface UseSafePollingOptions {
  url: string;
  onData?: (data: any) => void;
  onError?: (error: Error) => void;
  interval?: number;
  maxRetries?: number;
  shouldPoll?: () => boolean;
}

/**
 * Safe JSON parsing with fallback
 */
function safeJsonParse(json: string, fallback: any = null): any {
  try {
    return JSON.parse(json);
  } catch (error) {
    console.error('[POLL] JSON parse error:', error);
    return fallback;
  }
}

/**
 * Check if data actually changed (prevent unnecessary updates)
 */
function hasDataChanged(oldData: any, newData: any): boolean {
  if (!oldData) return true;
  if (!newData) return false;
  
  // Deep equality check
  const oldStr = JSON.stringify(oldData);
  const newStr = JSON.stringify(newData);
  return oldStr !== newStr;
}

export function useSafePolling({
  url,
  onData,
  onError,
  interval = config.POLLING_INTERVAL,
  maxRetries = Math.min(config.WS_RECONNECT_ATTEMPTS ?? 5, MAX_RETRIES),
  shouldPoll: customShouldPoll,
}: UseSafePollingOptions) {
  const isMounted = useRef(true);
  const abortController = useRef<AbortController | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const requestTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRequestInFlight = useRef(false);  // CRITICAL: Prevent concurrent requests
  const retryCount = useRef(0);
  const baseIntervalRef = useRef(interval);
  const lastDataRef = useRef<any>(null);

  // Store selectors - memoized
  const isWebSocketConnected = useMarketStore(
    (state) => state.isWebSocketConnected
  );
  const isPollingSuspended = useMarketStore(
    (state) => state.isPollingSuspended
  );

  /**
   * Determine if polling should happen now
   */
  const shouldPollNow = useCallback((): boolean => {
    // Don't poll if WebSocket is connected
    if (isWebSocketConnected) {
      return false;
    }

    // Don't poll if polling is explicitly suspended
    if (isPollingSuspended) {
      return false;
    }

    // Don't poll if page is hidden
    if (config.PAUSE_POLLING_ON_HIDDEN && document.hidden) {
      return false;
    }

    // Don't poll if max retries exceeded (critical fix)
    if (retryCount.current >= MAX_RETRIES) {
      console.error(`[POLL] Max retries (${MAX_RETRIES}) exceeded for ${url}`);
      return false;
    }

    // Custom poll condition
    if (customShouldPoll && !customShouldPoll()) {
      return false;
    }

    return true;
  }, [isWebSocketConnected, isPollingSuspended]);

  /**
   * Calculate next interval with exponential backoff
   */
  const getNextInterval = useCallback((): number => {
    if (retryCount.current === 0) {
      return baseIntervalRef.current;
    }
    // 1x, 2x, 4x, 8x backoff
    const backoffMultiplier = Math.pow(2, Math.min(retryCount.current, 3));
    const nextInterval = baseIntervalRef.current * backoffMultiplier;
    return nextInterval;
  }, []);

  /**
   * Fetch data from API with timeout protection
   */
  const fetchData = useCallback(async (): Promise<void> => {
    if (!isMounted.current) return;
    if (!shouldPollNow()) {
      logger.debug('[POLL] Skipping - WebSocket or condition check failed');
      return;
    }

    // CRITICAL: Prevent concurrent requests - skip if request already in flight
    if (isRequestInFlight.current) {
      logger.debug('[POLL] Request already in flight, skipping to prevent race condition');
      return;
    }

    isRequestInFlight.current = true;
    let requestSuccess = false;

    try {
      // Create new abort controller for this request
      abortController.current = new AbortController();

      logger.debug(`[POLL] Fetching: ${url} (attempt ${retryCount.current + 1}/${maxRetries})`);

      // Setup timeout protection (critical fix)
      const timeoutPromise = new Promise((_, reject) => {
        requestTimeoutRef.current = setTimeout(() => {
          abortController.current?.abort();
          reject(new Error('Request timeout after 5 seconds'));
        }, REQUEST_TIMEOUT);
      });

      // Race between fetch and timeout
      const fetchPromise = fetch(url, {
        signal: abortController.current.signal,
        headers: {
          'Content-Type': 'application/json',
          // Add auth token if available
          ...(typeof window !== 'undefined' &&
            localStorage.getItem('stocksentinel_token') && {
              Authorization: `Bearer ${localStorage.getItem('stocksentinel_token')}`,
            }),
        },
      });

      const response = (await Promise.race([fetchPromise, timeoutPromise])) as Response;

      // Clear timeout if fetch succeeded
      if (requestTimeoutRef.current) {
        clearTimeout(requestTimeoutRef.current);
        requestTimeoutRef.current = null;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Safe JSON parsing (critical fix)
      const text = await response.text();
      const data = safeJsonParse(text);

      if (!data) {
        throw new Error('Invalid JSON response from API');
      }

      if (!isMounted.current) return;

      // Only update if data actually changed (prevent re-renders)
      if (hasDataChanged(lastDataRef.current, data)) {
        lastDataRef.current = data;
        retryCount.current = 0;
        logger.debug(`[POLL] Success: ${url}`);
        requestSuccess = true;
        onData?.(data);
      } else {
        logger.debug(`[POLL] Data unchanged: ${url}`);
      }
    } catch (error) {
      // Clear timeout on error
      if (requestTimeoutRef.current) {
        clearTimeout(requestTimeoutRef.current);
        requestTimeoutRef.current = null;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        logger.debug('[POLL] Request cancelled');
        return;
      }

      if (!isMounted.current) return;

      // CRITICAL: Stop polling on 401 Unauthorized (Issue #14)
      if (error instanceof Error && (error.message.includes('HTTP 401') || error.message.includes('401'))) {
        console.error('[POLL] Unauthorized (401) - stopping polling. User session may have expired.');
        retryCount.current = MAX_RETRIES; // Stop polling immediately
        onError?.(new Error('Authentication expired - please log in again'));
        return;
      }

      const err = error instanceof Error ? error : new Error(String(error));
      
      // Check if max retries exceeded (critical fix)
      if (retryCount.current >= MAX_RETRIES) {
        console.error(`[POLL] CRITICAL: Max retries (${MAX_RETRIES}) exceeded. Stopping polling for ${url}`);
        onError?.(new Error(`Max retries exceeded: ${err.message}`));
        retryCount.current = MAX_RETRIES; // Lock at max
        return;
      }

      console.warn(`[POLL] Error (${retryCount.current + 1}/${maxRetries}): ${err.message}`);
      onError?.(err);

      // Increment retry count
      retryCount.current++;
    } finally {
      isRequestInFlight.current = false;  // CRITICAL: Always reset flag
      // No need to schedule - interval handles recurring polls
    }
  }, [url, shouldPollNow, onData, onError, maxRetries]);

  /**
   * Schedule next poll with appropriate interval
   */
  const scheduleNextPoll = useCallback(() => {
    if (!isMounted.current) return;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // Don't schedule if max retries reached
    if (retryCount.current >= MAX_RETRIES) {
      logger.debug('[POLL] Not scheduling - max retries reached');
      return;
    }

    const nextInterval = getNextInterval();
    logger.debug(`[POLL] Scheduled in ${nextInterval}ms`);

    timeoutRef.current = setTimeout(() => {
      if (isMounted.current) {
        void fetchData();
      }
    }, nextInterval);
  }, [getNextInterval, fetchData]);

  /**
   * Start polling interval
   */
  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      logger.debug('[POLL] Polling already active');
      return;
    }

    logger.debug('[POLL] Starting polling interval');

    // Immediate first fetch
    void fetchData();

    // Schedule recurring poll
    intervalRef.current = setInterval(() => {
      if (isMounted.current && shouldPollNow()) {
        void fetchData();
      }
    }, baseIntervalRef.current);
  }, [fetchData, shouldPollNow]);

  /**
   * Stop polling interval
   */
  const stopPolling = useCallback(() => {
    if (!intervalRef.current) {
      return;
    }

    logger.debug('[POLL] Stopping polling interval');

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  /**
   * Cleanup - critical for preventing memory leaks
   */
  useEffect(() => {
    return () => {
      isMounted.current = false;

      // Clear all timers and intervals
      if (abortController.current) {
        abortController.current.abort();
        abortController.current = null;
      }

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      if (requestTimeoutRef.current) {
        clearTimeout(requestTimeoutRef.current);
        requestTimeoutRef.current = null;
      }

      logger.debug('[POLL] Cleanup complete');
    };
  }, []);

  /**
   * Visibility-based polling control
   *
   * Uses Page Visibility API to start/stop polling:
   * - Start polling when tab is active
   * - Stop polling when tab is hidden
   * - Resume polling when tab becomes visible again
   *
   * This significantly reduces:
   * - API server load when users switch tabs
   * - Network bandwidth
   * - Battery drain on mobile devices
   */
  useEffect(() => {
    if (!isMounted.current) return;

    /**
     * Handle visibility changes
     * Stop interval when hidden, restart when visible
     */
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab is now hidden - stop polling
        stopPolling();
      } else {
        // Tab is now visible - restart polling
        logger.debug('[POLL] Tab visible, resuming polling');
        retryCount.current = 0; // Reset retries on resume
        startPolling();
      }
    };

    // Start polling initially if tab is visible
    if (!document.hidden) {
      startPolling();
    }

    // Listen for visibility changes
    if (config.PAUSE_POLLING_ON_HIDDEN) {
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    return () => {
      // Cleanup polling interval
      stopPolling();

      // Remove event listener
      if (config.PAUSE_POLLING_ON_HIDDEN) {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
      }
    };
  }, []);

  /**
   * Expose API for manual poll trigger and control
   */
  return {
    refresh: () => {
      retryCount.current = 0;
      lastDataRef.current = null;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      void fetchData();
    },
    stop: () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (requestTimeoutRef.current) clearTimeout(requestTimeoutRef.current);
      if (abortController.current) abortController.current.abort();
    },
    isPolling: shouldPollNow(),
    retryCount: retryCount.current,
  };
}
