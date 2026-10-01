'use client';

import { useQuery } from '@tanstack/react-query';
import { indicatorService, marketService, newsService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import { useIsAuthenticated } from './use-is-authenticated';

/**
 * Stock detail data. Every key includes the symbol (and the range where the
 * endpoint takes one), so a response for one symbol can never be shown for
 * another: switching symbols switches to a different cache entry.
 */

const STOCK_SENTIMENT_ARTICLES = 4;

/** Quote, day stats and chart history for one symbol and range. */
export function useStockDetailsQuery(symbol: string, range: string) {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.stocks.details(symbol, range),
    queryFn: () => marketService.getStockDetails(symbol, range),
    enabled: isAuthenticated && Boolean(symbol),
  });
}

/** SMA / EMA / RSI for one symbol (the endpoint has no range parameter). */
export function useStockIndicatorsQuery(symbol: string) {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.stocks.indicators(symbol),
    queryFn: () => indicatorService.combined(symbol),
    enabled: isAuthenticated && Boolean(symbol),
  });
}

/** Recent news for one symbol with a sentiment summary. */
export function useStockSentimentQuery(symbol: string) {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.news.symbolSentiment(symbol),
    queryFn: () => newsService.withSentiment(symbol, STOCK_SENTIMENT_ARTICLES),
    enabled: isAuthenticated && Boolean(symbol),
  });
}
