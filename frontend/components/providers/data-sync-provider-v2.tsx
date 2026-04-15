/**
 * Production-Grade Data Sync Provider
 * Orchestrates:
 * - WebSocket connections (singleton)
 * - Multi-tab coordination (primary tab only polls)
 * - Safe polling with intelligent fallback
 * - Global state management
 * - Error handling and recovery
 * 
 * Architecture:
 * 1. WebSocket manager connects globally
 * 2. Tab lock determines if this tab should poll
 * 3. Primary tab polls only if WebSocket disconnected
 * 4. All tabs stay in sync via store-v2 with BroadcastChannel
 */

'use client';

import React, { useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { useSafePolling } from '@/hooks/useSafePollingV2';
import { getWebSocketManager } from '@/lib/websocket-manager';
import { useTabLock } from '@/lib/multi-tab-lock';
import { useMarketStore } from '@/lib/store-v2';
import { config, logger } from '@/lib/config';

interface DataSyncProviderProps {
  children: React.ReactNode;
}

/**
 * Ribbon polling data handler
 */
function RibbonPolling() {
  const isPrimary = useTabLock();
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('stocksentinel_token')
      : null;
  const setRibbon = useMarketStore((state) => state.setRibbon);

  // 🚨 ONLY POLL WHEN TOKEN EXISTS
  if (!token) return null;

  const handleRibbonData = useCallback(
    (data: any) => {
      setRibbon(data, 'polling');
    },
    [setRibbon]
  );

  const handleRibbonError = useCallback((error: Error) => {
    logger.error('[Ribbon] Poll error:', error);
    useMarketStore.getState().setRibbonError?.(error.message);
  }, []);

  // Only poll if primary tab
  const shouldPoll = useCallback(() => {
    return isPrimary;
  }, [isPrimary]);

  useSafePolling({
    url: `${config.API_BASE_URL}/stocks/top-movers`,
    onData: handleRibbonData,
    onError: handleRibbonError,
    interval: config.POLLING_INTERVAL,
    shouldPoll,
  });

  return null;
}

/**
 * Market polling data handler
 */
function MarketPolling() {
  const isPrimary = useTabLock();
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('stocksentinel_token')
      : null;
  const setMarket = useMarketStore((state) => state.setMarket);

  // 🚨 ONLY POLL WHEN TOKEN EXISTS
  if (!token) return null;

  const handleMarketData = useCallback(
    (data: any) => {
      setMarket(data, 'polling');
    },
    [setMarket]
  );

  const handleMarketError = useCallback((error: Error) => {
    logger.error('[Market] Poll error:', error);
    useMarketStore.getState().setMarketError?.(error.message);
  }, []);

  const shouldPoll = useCallback(() => isPrimary, [isPrimary]);

  useSafePolling({
    url: `${config.API_BASE_URL}/stocks/market-snapshot`,
    onData: handleMarketData,
    onError: handleMarketError,
    interval: config.POLLING_INTERVAL,
    shouldPoll,
  });

  return null;
}

/**
 * News polling data handler
 */
function NewsPolling() {
  const isPrimary = useTabLock();
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('stocksentinel_token')
      : null;
  const setNews = useMarketStore((state) => state.setNews);

  // 🚨 ONLY POLL WHEN TOKEN EXISTS
  if (!token) return null;

  const handleNewsData = useCallback(
    (data: any) => {
      setNews(data, 'polling');
    },
    [setNews]
  );

  const handleNewsError = useCallback((error: Error) => {
    logger.error('[News] Poll error:', error);
    useMarketStore.getState().setNewsError?.(error.message);
  }, []);

  const shouldPoll = useCallback(() => isPrimary, [isPrimary]);

  useSafePolling({
    url: `${config.API_BASE_URL}/news/headlines`,
    onData: handleNewsData,
    onError: handleNewsError,
    interval: config.POLLING_INTERVAL * 2, // News updates less frequently
    shouldPoll,
  });

  return null;
}

/**
 * WebSocket manager initialization
 */
function WebSocketInitializer() {
  const setWebSocketConnected = useMarketStore(
    (state) => state.setWebSocketConnected
  );
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('stocksentinel_token')
      : null;

  // 🚨 ONLY RUN WHEN TOKEN EXISTS
  if (!token) return null;

  useEffect(() => {
    let isMounted = true;
    const unsubscribers: Array<() => void> = [];

    const initWebSocket = async () => {
      if (!isMounted) return;

      try {
        const wsUrl =
          (config as any).WS_BASE_URL ||
          config.API_BASE_URL.replace(/^http/, "ws");
        const manager = getWebSocketManager(wsUrl);

        // Register connection listeners
        unsubscribers.push(
          manager.onConnect(() => {
            logger.info('[WS] Connected');
            useMarketStore.getState().setWebSocketConnected(true);
          })
        );

        unsubscribers.push(
          manager.onDisconnect(() => {
            logger.info('[WS] Disconnected');
            useMarketStore.getState().setWebSocketConnected(false);
          })
        );

        unsubscribers.push(
          manager.onError((error: Error) => {
            logger.error('[WS] Error:', error);
          })
        );

        // Register message handlers
        unsubscribers.push(
          manager.on('ribbon', (data: any) => {
            useMarketStore.getState().setRibbon(data, 'websocket');
          })
        );

        unsubscribers.push(
          manager.on('market', (data: any) => {
            useMarketStore.getState().setMarket(data, 'websocket');
          })
        );

        unsubscribers.push(
          manager.on('news', (data: any) => {
            useMarketStore.getState().setNews(data, 'websocket');
          })
        );

        // Attempt connection
        if (isMounted) {
          await manager.connect();
        }
      } catch (error) {
        logger.error('[WS] Initialization failed:', error);
        // Non-fatal error - polling will fallback
      }
    };

    initWebSocket();

    return () => {
      isMounted = false;
      unsubscribers.forEach((fn) => fn());
    };
  }, []);

  return null;
}

/**
 * Main Data Sync Provider
 */
export function DataSyncProvider({ children }: DataSyncProviderProps) {
  const pathname = usePathname();
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('stocksentinel_token')
      : null;

  // 🚨 STOP ALL BACKGROUND WORK ON AUTH PAGES
  const isAuthPage =
    pathname.includes('/login') ||
    pathname.includes('/register');

  if (isAuthPage || !token) {
    return <>{children}</>;
  }

  useEffect(() => {
    logger.info('[DataSync] Provider initialized');
    return () => {
      logger.info('[DataSync] Provider cleanup');
    };
  }, []);

  return (
    <>
      {/* Initialize WebSocket */}
      <WebSocketInitializer />

      {/* Ribbon polling (primary tab only) */}
      <RibbonPolling />

      {/* Market polling (primary tab only) */}
      <MarketPolling />

      {/* News polling (primary tab only) */}
      <NewsPolling />

      {/* Render children */}
      {children}
    </>
  );
}
