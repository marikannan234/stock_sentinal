'use client';

/**
 * Persistent Layout Provider
 * Handles:
 * - Ribbon polling globally (no per-page polling)
 * - Market data polling globally
 * - Keeps ribbon persistent during page navigation
 * - Prevents flickering on route changes
 */

import { ReactNode, useEffect, useMemo } from 'react';
import { useSafePolling } from '@/hooks/useSafePolling';
import { useMarketStore } from '@/lib/store';
import { api } from '@/lib/api-client';
import type { LiveQuote, MarketSummary } from '@/lib/types';

interface RibbonResponse {
  stocks?: LiveQuote[];
}

/**
 * Global data syncing component
 * Polls market and ribbon data once per session
 */
export function DataSyncProvider({ children }: { children: ReactNode }) {
  const setMarket = useMarketStore((state) => state.setMarket);
  const setRibbon = useMarketStore((state) => state.setRibbon);
  const setMarketLoading = useMarketStore((state) => state.setMarketLoading);
  const setRibbonLoading = useMarketStore((state) => state.setRibbonLoading);

  // Setup polling for market data (5 seconds)
  useSafePolling(
    async (signal) => {
      try {
        const marketData = await api.get<MarketSummary>('/dashboard/market', { signal });
        if (marketData.data && typeof marketData.data === 'object') {
          setMarket(marketData.data);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('[DataSync] Failed to poll market:', error);
        }
      } finally {
        setMarketLoading(false);
      }
    },
    { interval: 5000 }
  );

  // Setup polling for ribbon data (5 seconds)
  useSafePolling(
    async (signal) => {
      try {
        const ribbonData = await api.get<RibbonResponse>('/dashboard/ribbon', { signal });
        if (ribbonData.data) {
          if (Array.isArray(ribbonData.data)) {
            setRibbon(ribbonData.data);
          } else if (ribbonData.data.stocks && Array.isArray(ribbonData.data.stocks)) {
            setRibbon(ribbonData.data.stocks);
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('[DataSync] Failed to poll ribbon:', error);
        }
      } finally {
        setRibbonLoading(false);
      }
    },
    { interval: 5000 }
  );

  return <>{children}</>;
}
