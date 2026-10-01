'use client';

import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/lib/api-service';
import { MARKET_REFETCH_INTERVAL_MS } from '@/lib/query-client';
import { queryKeys } from '@/lib/query-keys';
import type { LiveQuote, LiveRibbon } from '@/lib/types';
import { useIsAuthenticated } from './use-is-authenticated';

// The queryFns deliberately ignore TanStack's abort signal: with it, navigating
// between pages (which remounts the shell) cancels and restarts the in-flight
// poll instead of letting the next page reuse it.
const selectStocks = (ribbon: LiveRibbon): LiveQuote[] => ribbon.stocks ?? [];

/** Header ticker quotes, refreshed every 10 s while signed in and the tab is visible. */
export function useRibbonQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.market.ribbon(),
    queryFn: () => dashboardService.ribbon(),
    select: selectStocks,
    enabled: isAuthenticated,
    staleTime: MARKET_REFETCH_INTERVAL_MS,
    refetchInterval: MARKET_REFETCH_INTERVAL_MS,
  });
}

/** Market summary (top gainers/losers/most active), refreshed every 10 s while signed in. */
export function useMarketSummaryQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.market.summary(),
    queryFn: () => dashboardService.market(),
    enabled: isAuthenticated,
    staleTime: MARKET_REFETCH_INTERVAL_MS,
    refetchInterval: MARKET_REFETCH_INTERVAL_MS,
  });
}
