'use client';

import { useEffect, useRef, useCallback } from 'react';

/**
 * Safe polling hook using setTimeout instead of setInterval
 * Features:
 * - Prevents overlapping API calls
 * - Respects document.hidden (pauses polling when tab inactive)
 * - Uses AbortController for request cancellation
 * - Prevents state updates after unmount
 * - Supports retry logic with exponential backoff
 */

interface UseSafePollingOptions {
  interval: number; // milliseconds
  enabled?: boolean;
  onError?: (error: Error) => void;
  onSuccess?: () => void;
  maxRetries?: number;
  retryDelay?: number;
}

export function useSafePolling(
  pollFn: (signal: AbortSignal) => Promise<void>,
  options: UseSafePollingOptions,
) {
  const {
    interval,
    enabled = true,
    onError,
    onSuccess,
    maxRetries = 3,
    retryDelay = 1000,
  } = options;

  const isMountedRef = useRef(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef(0);
  const isPollingRef = useRef(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  // Recursive polling function
  const executePoll = useCallback(async () => {
    // Prevent overlapping calls
    if (isPollingRef.current) return;

    // Check if component is still mounted and polling is enabled
    if (!isMountedRef.current || !enabled) return;

    // Pause polling if tab is hidden
    if (document.hidden) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      // Schedule retry when tab becomes visible
      timeoutRef.current = setTimeout(executePoll, interval);
      return;
    }

    isPollingRef.current = true;

    try {
      // Create fresh AbortController for this request
      abortControllerRef.current = new AbortController();

      // Execute the polling function
      await pollFn(abortControllerRef.current.signal);

      // Reset retry count on success
      retryCountRef.current = 0;
      onSuccess?.();
    } catch (error) {
      // Don't handle abort errors (expected during cleanup)
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }

      const err = error instanceof Error ? error : new Error(String(error));

      // 🚨 STOP POLLING ON 401 (unauthorized)
      if (error instanceof Error && error.message?.includes('401')) {
        console.warn('[Polling] Unauthorized (401) - stopping polling');
        onError?.(err);
        return;
      }

      // Retry logic with exponential backoff
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        const backoffDelay = retryDelay * Math.pow(2, retryCountRef.current - 1);

        if (isMountedRef.current && enabled) {
          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          timeoutRef.current = setTimeout(executePoll, backoffDelay);
        }
      } else {
        // Max retries exceeded
        onError?.(err);
      }
    } finally {
      isPollingRef.current = false;

      // Schedule next poll if still mounted and enabled
      if (isMountedRef.current && enabled && !document.hidden) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(executePoll, interval);
      }
    }
  }, [pollFn, interval, enabled, onError, onSuccess, maxRetries, retryDelay]);

  // Handle visibility change (pause/resume polling)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Tab became visible - resume polling
        executePoll();
      } else {
        // Tab became hidden - cancel pending poll
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        if (abortControllerRef.current) abortControllerRef.current.abort();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [executePoll]);

  // Start polling when enabled changes
  useEffect(() => {
    if (!enabled || !isMountedRef.current) return;

    // Clear any pending timeout
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    // Start immediately
    executePoll();

    // Return cleanup
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, [enabled, executePoll]);

  // Manual stop function
  const stop = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (abortControllerRef.current) abortControllerRef.current.abort();
    isPollingRef.current = false;
  }, []);

  return { stop };
}
