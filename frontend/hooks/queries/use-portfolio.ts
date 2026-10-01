'use client';

import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { portfolioService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import { useIsAuthenticated } from './use-is-authenticated';

export type PortfolioRange = '1d' | '1w' | '1m' | '1y';

/** Portfolio totals and buying power (server-calculated). */
export function usePortfolioSummaryQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.portfolio.summary(),
    queryFn: () => portfolioService.summary(),
    enabled: isAuthenticated,
  });
}

/** Open positions with server-calculated P&L. */
export function usePortfolioHoldingsQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.portfolio.holdings(),
    queryFn: () => portfolioService.list(),
    enabled: isAuthenticated,
  });
}

/** Allocation by asset class. */
export function usePortfolioAllocationQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.portfolio.allocation(),
    queryFn: () => portfolioService.allocation(),
    enabled: isAuthenticated,
  });
}

/**
 * Portfolio value history for one range; each range is cached separately.
 * While a newly selected range loads, the previous range's chart stays visible
 * (`isPlaceholderData` is true) instead of the chart going blank.
 */
export function usePortfolioGrowthQuery(range: PortfolioRange) {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.portfolio.growth(range),
    queryFn: () => portfolioService.growth(range),
    enabled: isAuthenticated,
    placeholderData: keepPreviousData,
  });
}
