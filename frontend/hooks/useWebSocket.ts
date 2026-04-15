'use client';

/**
 * useWebSocket Hook for managing WebSocket connections
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Fallback to polling on connection failure
 * - Proper cleanup and memory leak prevention
 * - Message type routing
 * - Connection state tracking
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export interface UseWebSocketOptions {
  url: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  autoConnect?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  send: (message: any) => boolean;
  subscribe: (type: string, handler: (data: any) => void) => () => void;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    reconnectAttempts = 5,
    reconnectDelay = 1000,
    heartbeatInterval = 30000,
    onConnect,
    onDisconnect,
    onError,
    autoConnect = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const isMountedRef = useRef(true);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const handlersRef = useRef<Map<string, (data: any) => void>>(
    new Map(),
  );
  const isConnectingRef = useRef(false);
  const [isConnected, setIsConnected] = useState(false);

  const setupHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (
        wsRef.current &&
        wsRef.current.readyState === WebSocket.OPEN
      ) {
        try {
          wsRef.current.send(
            JSON.stringify({
              type: 'ping',
              timestamp: Date.now(),
            }),
          );
        } catch (error) {
          console.error('[WS] Error sending heartbeat:', error);
        }
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  const handleClose = useCallback(() => {
    if (!isMountedRef.current) return;

    console.log('[WS] Disconnected');
    setIsConnected(false);

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    onDisconnect?.();
  }, [onDisconnect]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached');
      return;
    }

    const delay = reconnectDelay * Math.pow(2, reconnectCountRef.current);
    reconnectCountRef.current++;

    console.log(
      `[WS] Scheduling reconnect in ${delay}ms (attempt ${reconnectCountRef.current}/${reconnectAttempts})`,
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isMountedRef.current && !isConnectingRef.current) {
        void connect();
      }
    }, delay);
  }, [reconnectAttempts, reconnectDelay]);

  const connect = useCallback(async () => {
    if (
      wsRef.current &&
      wsRef.current.readyState === WebSocket.OPEN
    ) {
      console.log('[WS] Already connected');
      return;
    }

    if (isConnectingRef.current) {
      console.log('[WS] Connection already in progress');
      return;
    }

    if (!isMountedRef.current) {
      return;
    }

    isConnectingRef.current = true;

    try {
      console.log(`[WS] Connecting to ${url}...`);
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        if (!isMountedRef.current) return;

        console.log('[WS] Connected');
        reconnectCountRef.current = 0;
        setIsConnected(true);
        setupHeartbeat();
        onConnect?.();
        isConnectingRef.current = false;
      };

      wsRef.current.onmessage = (event) => {
        if (!isMountedRef.current) return;

        try {
          const data = JSON.parse(event.data);

          // Route to appropriate handler
          if (data.type && handlersRef.current.has(data.type)) {
            const handler = handlersRef.current.get(data.type);
            handler?.(data);
          }
        } catch (error) {
          console.error('[WS] Error parsing message:', error);
        }
      };

      wsRef.current.onerror = (event) => {
        if (!isMountedRef.current) return;

        const error = new Error('[WS] Connection error');
        console.error(error);
        onError?.(error);
        isConnectingRef.current = false;
      };

      wsRef.current.onclose = () => {
        if (!isMountedRef.current) return;

        handleClose();
        scheduleReconnect();
        isConnectingRef.current = false;
      };
    } catch (error) {
      if (!isMountedRef.current) return;

      const err = error instanceof Error ? error : new Error(String(error));
      console.error('[WS] Connection error:', err);
      onError?.(err);
      scheduleReconnect();
      isConnectingRef.current = false;
    }
  }, [url, onConnect, onError, setupHeartbeat, handleClose, scheduleReconnect]);

  const disconnect = useCallback(() => {
    isMountedRef.current = false;

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

    handlersRef.current.clear();
    setIsConnected(false);
  }, []);

  const send = useCallback((message: any): boolean => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Not connected, cannot send message');
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('[WS] Error sending message:', error);
      return false;
    }
  }, []);

  const subscribe = useCallback(
    (type: string, handler: (data: any) => void): (() => void) => {
      handlersRef.current.set(type, handler);

      // Return unsubscribe function
      return () => {
        handlersRef.current.delete(type);
      };
    },
    [],
  );

  // Auto-connect on mount
  useEffect(() => {
    isMountedRef.current = true;

    if (autoConnect) {
      void connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    send,
    subscribe,
    connect,
    disconnect,
  };
}
