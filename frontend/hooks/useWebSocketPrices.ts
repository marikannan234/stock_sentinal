'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

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

const THROTTLE_DELAY_MS = 1000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocketPrices(
  symbols: string[],
  onPriceUpdate: PriceUpdateCallback,
  enabled: boolean = true,
) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectCountRef = useRef(0);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastUpdateRef = useRef<Record<string, number>>({});
  const isUnmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') {
      return;
    }

    if (isUnmountedRef.current) {
      console.log('Component unmounted, skipping connection');
      return;
    }

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
    }

    if (!enabled || symbols.length === 0) {
      console.log('WebSocket not enabled or no symbols provided');
      return;
    }

    try {
      const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      const symbol = symbols[0];
      const wsUrl = `${wsBaseUrl}/ws/stocks/${symbol}`;

      console.log(`Creating WebSocket connection to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }

        if (wsRef.current !== ws) {
          console.log('WebSocket instance mismatch, closing old connection');
          ws.close();
          return;
        }

        setConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        console.log(`WebSocket connected to ${symbol}`);

        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        heartbeatIntervalRef.current = setInterval(() => {
          try {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          } catch (err) {
            console.error('Failed to send heartbeat:', err);
          }
        }, 10000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as PortfolioPriceUpdate;
          const now = Date.now();
          const lastUpdate = lastUpdateRef.current[data.symbol] || 0;

          if (now - lastUpdate < THROTTLE_DELAY_MS) {
            return;
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
        console.log('WebSocket disconnected');

        if (wsRef.current === ws && !isUnmountedRef.current) {
          if (heartbeatIntervalRef.current) {
            clearInterval(heartbeatIntervalRef.current);
            heartbeatIntervalRef.current = null;
          }

          if (enabled && reconnectCountRef.current < MAX_RECONNECT_ATTEMPTS) {
            const delay = Math.max(1000, Math.min(1000 * Math.pow(2, reconnectCountRef.current), 10000));

            if (reconnectTimeoutRef.current) {
              clearTimeout(reconnectTimeoutRef.current);
            }

            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectCountRef.current++;
              if (reconnectCountRef.current <= MAX_RECONNECT_ATTEMPTS && !isUnmountedRef.current) {
                console.log(`Auto-reconnecting (attempt ${reconnectCountRef.current}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms...`);
                connect();
              }
            }, delay);
          } else if (reconnectCountRef.current >= MAX_RECONNECT_ATTEMPTS) {
            console.warn(`Max reconnect attempts (${MAX_RECONNECT_ATTEMPTS}) reached`);
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

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    isUnmountedRef.current = false;

    if (enabled && symbols.length > 0) {
      connect();
    }

    return () => {
      isUnmountedRef.current = true;

      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

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
    reconnect: useCallback(() => {
      if (typeof window === 'undefined') {
        return;
      }

      isUnmountedRef.current = false;
      reconnectCountRef.current = 0;

      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      connect();
    }, [connect]),
  };
}
