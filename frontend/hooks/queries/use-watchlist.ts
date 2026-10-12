'use client';

import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { marketService, watchlistService } from '@/lib/api-service';
import { MARKET_REFETCH_INTERVAL_MS } from '@/lib/query-client';
import { queryKeys } from '@/lib/query-keys';
import { useIsAuthenticated } from './use-is-authenticated';

/** The signed-in user's watchlist tickers. */
export function useWatchlistQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.watchlist.list(),
    queryFn: () => watchlistService.list(),
    enabled: isAuthenticated,
  });
}

/** Adds a ticker; the response is the updated list, so it replaces the cache directly. */
export function useAddToWatchlistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker: string) => watchlistService.add(ticker),
    onSuccess: (watchlist) => {
      queryClient.setQueryData(queryKeys.watchlist.list(), watchlist);
    },
  });
}

/** Removes a ticker and immediately updates the cached list. */
export function useRemoveFromWatchlistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker: string) => watchlistService.remove(ticker),
    onSuccess: (watchlist) => {
      queryClient.setQueryData(queryKeys.watchlist.list(), watchlist);
    },
  });
}

/**
 * Latest quote per symbol, refreshed every 10 s. There is no batch quote
 * endpoint, so this is one request per symbol; each is cached under
 * ['stocks', symbol, 'price'] and shared with any other consumer.
 */
export function useStockPriceQueries(symbols: string[]) {
  const isAuthenticated = useIsAuthenticated();
  return useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: queryKeys.stocks.price(symbol),
      queryFn: () => marketService.getStockPrice(symbol),
      enabled: isAuthenticated,
      staleTime: MARKET_REFETCH_INTERVAL_MS,
      refetchInterval: MARKET_REFETCH_INTERVAL_MS,
    })),
  });
}
