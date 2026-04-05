'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, marketService, watchlistService } from '@/lib/api-service';
import { formatCurrency, formatPercent } from '@/lib/format';
import type { LiveQuote } from '@/lib/types';

export default function WatchlistPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quotes, setQuotes] = useState<LiveQuote[]>([]);
  const [ticker, setTicker] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function loadWatchlist() {
    try {
      setLoading(true);
      setError('');
      const list = await watchlistService.list();
      if (!list.tickers.length) {
        setQuotes([]);
        return;
      }
      const priceResults = await Promise.all(list.tickers.map((item) => marketService.getStockPrice(item)));
      setQuotes(priceResults);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load watchlist.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadWatchlist();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!ticker.trim()) {
      showToast({ title: 'Ticker required', description: 'Enter a symbol to add to the watchlist.', variant: 'error' });
      return;
    }

    try {
      setSubmitting(true);
      await watchlistService.add(ticker.trim().toUpperCase());
      setTicker('');
      showToast({ title: 'Watchlist updated', description: 'The ticker was added successfully.', variant: 'success' });
      await loadWatchlist();
    } catch (err) {
      showToast({ title: 'Unable to add symbol', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(symbol: string) {
    try {
      await watchlistService.remove(symbol);
      showToast({ title: 'Removed from watchlist', description: `${symbol} was removed.`, variant: 'success' });
      await loadWatchlist();
    } catch (err) {
      showToast({ title: 'Unable to remove symbol', description: getErrorMessage(err), variant: 'error' });
    }
  }

  return (
    <ProtectedShell>
      <AppShell
        currentPage="watchlist"
        title="Watchlist"
        description="Track symbols you care about with live quote widgets and direct links to the details page."
        actions={<Button variant="outline" onClick={() => void loadWatchlist()}>Refresh</Button>}
      >
        <SurfaceCard>
          <form className="flex flex-col gap-3 md:flex-row" onSubmit={handleAdd}>
            <Input label="Add Symbol" value={ticker} onChange={(event) => setTicker(event.target.value)} className="md:flex-1" />
            <Button type="submit" isLoading={submitting} className="md:self-end">Add to Watchlist</Button>
          </form>
        </SurfaceCard>
        {loading ? (
          <LoadingState label="Loading watchlist..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadWatchlist()} />
        ) : !quotes.length ? (
          <EmptyState title="Watchlist is empty" message="Add a stock symbol to begin monitoring live prices." />
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {quotes.map((quote) => (
              <SurfaceCard key={quote.symbol}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-black text-white">{quote.symbol}</p>
                    <p className="mt-2 text-on-surface-variant">{formatCurrency(quote.price)}</p>
                  </div>
                  <p className={`text-sm font-semibold ${quote.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                    {formatPercent(quote.change_percent)}
                  </p>
                </div>
                <div className="mt-5 flex gap-3">
                  <Button variant="outline" fullWidth asChild>
                    <Link href={`/stocks/${quote.symbol}`}>Open Details</Link>
                  </Button>
                  <Button variant="ghost" fullWidth onClick={() => void handleRemove(quote.symbol)}>
                    Remove
                  </Button>
                </div>
              </SurfaceCard>
            ))}
          </div>
        )}
      </AppShell>
    </ProtectedShell>
  );
}
