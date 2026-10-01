'use client';

import { FormEvent, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { useMarketSummaryQuery } from '@/hooks/queries/use-market';
import { useAddToWatchlistMutation, useStockPriceQueries, useWatchlistQuery } from '@/hooks/queries/use-watchlist';
import { getErrorMessage } from '@/lib/api-service';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

export default function WatchlistPage() {
  const [symbolInput, setSymbolInput] = useState('');

  const watchlistQuery = useWatchlistQuery();
  const symbols = watchlistQuery.data?.tickers ?? [];
  const priceQueries = useStockPriceQueries(symbols);
  const marketQuery = useMarketSummaryQuery();
  const market = marketQuery.data;
  const moversFallback = (empty: string) =>
    marketQuery.isPending ? 'Loading…' : marketQuery.isError ? 'Market data unavailable' : empty;
  const addMutation = useAddToWatchlistMutation();

  function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ticker = symbolInput.trim().toUpperCase();
    if (!ticker) return;
    addMutation.mutate(ticker, { onSuccess: () => setSymbolInput('') });
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Main Watchlist" subtitle={`Monitoring ${symbols.length} selected assets · prices update every 10s`}>
        <div className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="flex items-center justify-between px-6 py-5">
              <div className="flex gap-3">
                <button className="rounded-xl bg-[var(--surface-high)] px-5 py-3 text-sm font-bold text-white">Filter</button>
                <form onSubmit={handleAdd} className="flex gap-3">
                  <input value={symbolInput} onChange={(event) => setSymbolInput(event.target.value)} className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none" placeholder="Add symbol" />
                  <button disabled={addMutation.isPending} className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-3 text-sm font-bold text-[var(--on-primary)] disabled:opacity-60">Add Symbol</button>
                </form>
              </div>
            </div>
            {addMutation.isError ? (
              <p className="px-6 pb-3 text-xs text-tertiary">{getErrorMessage(addMutation.error, 'Unable to add symbol.')}</p>
            ) : null}
            <table className="w-full">
              <thead className="text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                <tr>
                  <th className="px-6 py-4 text-left">Symbol</th>
                  <th className="px-6 py-4 text-left">Price</th>
                  <th className="px-6 py-4 text-left">Change %</th>
                  <th className="px-6 py-4 text-left">Volume</th>
                </tr>
              </thead>
              <tbody>
                {watchlistQuery.isPending ? (
                  <tr className="border-t border-white/5">
                    <td colSpan={4} className="px-6 py-5 text-sm text-[var(--on-surface-variant)]">Loading watchlist…</td>
                  </tr>
                ) : watchlistQuery.isError ? (
                  <tr className="border-t border-white/5">
                    <td colSpan={4} className="px-6 py-5 text-sm text-tertiary">
                      Unable to load your watchlist.{' '}
                      <button type="button" onClick={() => watchlistQuery.refetch()} className="underline">Retry</button>
                    </td>
                  </tr>
                ) : symbols.length === 0 ? (
                  <tr className="border-t border-white/5">
                    <td colSpan={4} className="px-6 py-5 text-sm text-[var(--on-surface-variant)]">No symbols yet. Add one above to start tracking it.</td>
                  </tr>
                ) : (
                  symbols.map((symbol, index) => {
                    const quote = priceQueries[index]?.data;
                    return (
                      <tr key={symbol} className="border-t border-white/5">
                        <td className="px-6 py-5">
                          <p className="font-bold text-white">{symbol}</p>
                          <p className="text-[10px] text-[var(--on-surface-variant)]">NASDAQ</p>
                        </td>
                        <td className="px-6 py-5 font-mono text-white">{quote ? formatCurrency(quote.price) : '—'}</td>
                        <td className={`px-6 py-5 font-mono ${(quote?.change_percent ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>{quote ? formatPercent(quote.change_percent) : '—'}</td>
                        <td className="px-6 py-5 font-mono text-[var(--on-surface-variant)]">{quote ? formatCompactNumber(quote.volume) : '—'}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </SurfaceCard>
          <div className="col-span-12 space-y-5 lg:col-span-4">
            <SurfaceCard className="p-5">
              <h3 className="mb-4 text-sm font-black uppercase tracking-[0.18em] text-white">Top Gainers</h3>
              <div className="space-y-4">
                {market && Array.isArray(market.top_gainers) && market.top_gainers.length > 0 ? (
                  market.top_gainers.slice(0, 5).map((item) => (
                    <div key={item.symbol} className="flex items-center justify-between">
                      <div>
                        <p className="font-bold text-white">{item.symbol}</p>
                        <p className="text-[10px] text-[var(--on-surface-variant)]">Market mover</p>
                      </div>
                      <span className="font-mono text-secondary">{formatPercent(item.change_percent)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-[var(--on-surface-variant)]">{moversFallback('No gainers available')}</p>
                )}
              </div>
            </SurfaceCard>
            <SurfaceCard className="p-5">
              <h3 className="mb-4 text-sm font-black uppercase tracking-[0.18em] text-white">Top Losers</h3>
              <div className="space-y-4">
                {market && Array.isArray(market.top_losers) && market.top_losers.length > 0 ? (
                  market.top_losers.slice(0, 3).map((item) => (
                    <div key={item.symbol} className="flex items-center justify-between">
                      <div>
                        <p className="font-bold text-white">{item.symbol}</p>
                        <p className="text-[10px] text-[var(--on-surface-variant)]">Market mover</p>
                      </div>
                      <span className="font-mono text-tertiary">{formatPercent(item.change_percent)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-[var(--on-surface-variant)]">{moversFallback('No losers available')}</p>
                )}
              </div>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
