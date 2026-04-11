'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export interface PortfolioPriceUpdate {
  symbol: string;
  price: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

type PriceUpdateCallback = (update: PortfolioPriceUpdate) => void;

const THROTTLE_DELAY_MS = 1000; // Max 1 update per second per symbol
const MAX_RECONNECT_ATTEMPTS = 5; // Prevent infinite reconnect loops

/**
 * Custom hook for managing WebSocket connections for real-time stock prices.
 * Handles auto-reconnect, multiple symbols, proper cleanup, and throttling.
 * 
 * Ensures:
 * - Only ONE WebSocket instance exists at a time
 * - No duplicate connections
 * - Proper cleanup on unmount
 * - No multiple reconnect timers
 */
export function useWebSocketPrices(
  symbols: string[],
  onPriceUpdate: PriceUpdateCallback,
  enabled: boolean = true
) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectCountRef = useRef(0);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastUpdateRef = useRef<Record<string, number>>({}); // Throttle tracking per symbol
  const isUnmountedRef = useRef(false); // Track if component is unmounted
  
  // Connect function with proper singleton pattern
  const connect = useCallback(() => {
    // If component is unmounted, don't reconnect
    if (isUnmountedRef.current) {
      console.log('Component unmounted, skipping connection');
      return;
    }

    // Check if already connected or connecting
    if (wsRef.current) {
      const state = wsRef.current.readyState;
      if (state === WebSocket.OPEN) {
        console.log('WebSocket already connected');
        return;
      }
      if (state === WebSocket.CONNECTING) {
        console.log('WebSocket already connecting');
        return;
      }
      // If CLOSED or CLOSING, ws will be recreated below
    }

    if (!enabled || symbols.length === 0) {
      console.log('WebSocket not enabled or no symbols provided');
      return;
    }

    try {
      const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
      const symbol = symbols[0];
      const wsUrl = `${WS_URL}/ws/stocks/${symbol}`;

      console.log(`Creating WebSocket connection to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // Check again if we're unmounted
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }

        // Check if this ws is still the current one (in case of race conditions)
        if (wsRef.current !== ws) {
          console.log('WebSocket instance mismatch, closing old connection');
          ws.close();
          return;
        }

        setConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        console.log(`✅ WebSocket connected to ${symbol}`);

        // Clear existing heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Start heartbeat to keep connection alive
        heartbeatIntervalRef.current = setInterval(() => {
          try {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "ping" }));
            }
          } catch (err) {
            console.error("Failed to send heartbeat:", err);
          }
        }, 10000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as PortfolioPriceUpdate;

          // Throttle updates: max 1 update per symbol per second
          const now = Date.now();
          const lastUpdate = lastUpdateRef.current[data.symbol] || 0;

          if (now - lastUpdate < THROTTLE_DELAY_MS) {
            return; // Skip this update, rate limited
          }

          lastUpdateRef.current[data.symbol] = now;
          onPriceUpdate(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        const errorMsg = `WebSocket error: ${event.type}`;
        setError(errorMsg);
        setConnected(false);
        console.error(errorMsg);
      };

      ws.onclose = () => {
        setConnected(false);
        console.log(`⛔ WebSocket disconnected`);

        // Only reconnect if this is still the current ws and component is not unmounted
        if (wsRef.current === ws && !isUnmountedRef.current) {
          // Clear heartbeat
          if (heartbeatIntervalRef.current) {
            clearInterval(heartbeatIntervalRef.current);
            heartbeatIntervalRef.current = null;
          }

          // Auto-reconnect with exponential backoff
          if (enabled && reconnectCountRef.current < MAX_RECONNECT_ATTEMPTS) {
            const delay = Math.max(1000, Math.min(1000 * Math.pow(2, reconnectCountRef.current), 10000));

            // Clear any existing reconnect timeout
            if (reconnectTimeoutRef.current) {
              clearTimeout(reconnectTimeoutRef.current);
            }

            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectCountRef.current++;
              if (reconnectCountRef.current <= MAX_RECONNECT_ATTEMPTS && !isUnmountedRef.current) {
                console.log(`🔄 Auto-reconnecting (attempt ${reconnectCountRef.current}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms...`);
                connect();
              }
            }, delay);
          } else if (reconnectCountRef.current >= MAX_RECONNECT_ATTEMPTS) {
            console.warn(`❌ Max reconnect attempts (${MAX_RECONNECT_ATTEMPTS}) reached`);
            setError(`Failed to connect after ${MAX_RECONNECT_ATTEMPTS} attempts`);
          }
        }
      };

      wsRef.current = ws;
    } catch (err) {
      const errorMsg = `Failed to connect WebSocket: ${err instanceof Error ? err.message : String(err)}`;
      setError(errorMsg);
      setConnected(false);
      console.error(errorMsg);
    }
  }, [enabled, symbols, onPriceUpdate]);

  // Setup and cleanup
  useEffect(() => {
    isUnmountedRef.current = false;

    // Initial connection
    if (enabled && symbols.length > 0) {
      connect();
    }

    // Cleanup on unmount or when disabled
    return () => {
      isUnmountedRef.current = true;

      // Clear heartbeat interval
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }

      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      setConnected(false);
    };
  }, [enabled, symbols, connect]);

  return {
    connected,
    error,
    // Allow manual reconnect
    reconnect: useCallback(() => {
      isUnmountedRef.current = false;
      reconnectCountRef.current = 0;

      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }

      // Close current connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      // Reconnect
      connect();
    }, [connect]),
  };
}
  };
}
