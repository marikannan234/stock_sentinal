'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, watchlistService } from '@/lib/api-service';
import type { LiveQuote, MarketSummary } from '@/lib/types';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [quotes, setQuotes] = useState<LiveQuote[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [symbolInput, setSymbolInput] = useState('');

  const refreshWatchlist = useCallback(async () => {
    const watchlist = await watchlistService.list();
    setSymbols(watchlist.tickers);
    const quoteResults = await Promise.allSettled(watchlist.tickers.map((ticker) => marketService.getStockPrice(ticker)));
    setQuotes(quoteResults.filter((item): item is PromiseFulfilledResult<LiveQuote> => item.status === 'fulfilled').map((item) => item.value));
  }, []);

  useEffect(() => {
    Promise.allSettled([refreshWatchlist(), marketService.getMarketSummary(), marketService.getLiveRibbon()]).then((results) => {
      const summaryResult = results[1];
      const ribbonResult = results[2];
      if (summaryResult.status === 'fulfilled') setMarketSummary(summaryResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  const handleAdd = useCallback(async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!symbolInput.trim()) return;
    await watchlistService.add((symbolInput.trim() || "").toUpperCase());
    setSymbolInput('');
    await refreshWatchlist();
  }, [symbolInput, refreshWatchlist]);

  return (
    <ProtectedScreen>
      <SentinelShell title="Main Watchlist" subtitle={`Real-time monitoring of ${symbols.length} selected assets`} ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="flex items-center justify-between px-6 py-5">
              <div className="flex gap-3">
                <button className="rounded-xl bg-[var(--surface-high)] px-5 py-3 text-sm font-bold text-white">Filter</button>
                <form onSubmit={handleAdd} className="flex gap-3">
                  <input value={symbolInput} onChange={(event) => setSymbolInput(event.target.value)} className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none" placeholder="Add symbol" />
                  <button className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-3 text-sm font-bold text-[var(--on-primary)]">Add Symbol</button>
                </form>
              </div>
            </div>
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
                {quotes.map((quote) => (
                  <tr key={quote.symbol} className="border-t border-white/5">
                    <td className="px-6 py-5">
                      <p className="font-bold text-white">{quote.symbol}</p>
                      <p className="text-[10px] text-[var(--on-surface-variant)]">NASDAQ</p>
                    </td>
                    <td className="px-6 py-5 font-mono text-white">{formatCurrency(quote.price)}</td>
                    <td className={`px-6 py-5 font-mono ${quote.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>{formatPercent(quote.change_percent)}</td>
                    <td className="px-6 py-5 font-mono text-[var(--on-surface-variant)]">{formatCompactNumber(quote.volume)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </SurfaceCard>
          <div className="col-span-12 space-y-5 lg:col-span-4">
            <SurfaceCard className="p-5">
              <h3 className="mb-4 text-sm font-black uppercase tracking-[0.18em] text-white">Top Gainers</h3>
              <div className="space-y-4">
                {marketSummary?.top_gainers.slice(0, 5).map((item) => (
                  <div key={item.symbol} className="flex items-center justify-between">
                    <div>
                      <p className="font-bold text-white">{item.symbol}</p>
                      <p className="text-[10px] text-[var(--on-surface-variant)]">Live market</p>
                    </div>
                    <span className="font-mono text-secondary">{formatPercent(item.change_percent)}</span>
                  </div>
                ))}
              </div>
            </SurfaceCard>
            <SurfaceCard className="p-5">
              <h3 className="mb-4 text-sm font-black uppercase tracking-[0.18em] text-white">Top Losers</h3>
              <div className="space-y-4">
                {marketSummary?.top_losers.slice(0, 3).map((item) => (
                  <div key={item.symbol} className="flex items-center justify-between">
                    <div>
                      <p className="font-bold text-white">{item.symbol}</p>
                      <p className="text-[10px] text-[var(--on-surface-variant)]">Live market</p>
                    </div>
                    <span className="font-mono text-tertiary">{formatPercent(item.change_percent)}</span>
                  </div>
                ))}
              </div>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
