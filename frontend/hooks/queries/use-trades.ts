'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { portfolioService, tradeService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import { useIsAuthenticated } from './use-is-authenticated';

/** Closed and open trade records, newest data from the server. */
export function useTradeHistoryQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.trades.history(),
    queryFn: () => tradeService.history(),
    enabled: isAuthenticated,
  });
}

/** Win rate, net profit and counts for the trade history page. */
export function useTradeHistorySummaryQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.trades.historySummary(),
    queryFn: () => tradeService.historySummary(),
    enabled: isAuthenticated,
  });
}

export type MarketOrder = { symbol: string; quantity: number };

/**
 * After any trade, refresh everything it can change: portfolio (summary,
 * holdings, allocation, growth), trade history, and the traded symbol's data.
 */
function useRefreshAfterTrade() {
  const queryClient = useQueryClient();
  return (symbol: string) =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.portfolio.all }),
      queryClient.invalidateQueries({ queryKey: queryKeys.trades.all }),
      queryClient.invalidateQueries({ queryKey: queryKeys.stocks.bySymbol(symbol) }),
    ]);
}

/** Market BUY. The server validates the symbol and cash and sets the price. */
export function useBuyMutation() {
  const refreshAfterTrade = useRefreshAfterTrade();
  return useMutation({
    mutationFn: ({ symbol, quantity }: MarketOrder) => portfolioService.add(symbol, quantity),
    onSuccess: (_, { symbol }) => refreshAfterTrade(symbol),
  });
}

/**
 * Market SELL through the trading engine, which rejects selling a symbol you
 * do not hold or more shares than you hold (DELETE /portfolio/{ticker} would
 * silently succeed without selling anything for an unknown ticker).
 */
export function useSellMutation() {
  const refreshAfterTrade = useRefreshAfterTrade();
  return useMutation({
    mutationFn: ({ symbol, quantity }: MarketOrder) =>
      tradeService.create({ symbol, quantity, trade_type: 'SELL' }),
    onSuccess: (_, { symbol }) => refreshAfterTrade(symbol),
  });
}
