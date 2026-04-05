'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { MetricCard, SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, portfolioService } from '@/lib/api-service';
import { formatCurrency } from '@/lib/format';
import type { PortfolioHolding, PortfolioSummary } from '@/lib/types';

export default function PortfolioPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ ticker: '', quantity: '', price: '' });

  async function loadPortfolio() {
    try {
      setLoading(true);
      setError('');
      const [holdingData, summaryData] = await Promise.all([portfolioService.list(), portfolioService.summary()]);
      setHoldings(holdingData);
      setSummary(summaryData);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load portfolio.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPortfolio();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!form.ticker.trim() || Number(form.quantity) <= 0 || Number(form.price) <= 0) {
      showToast({ title: 'Invalid portfolio input', description: 'Ticker, quantity, and price are required.', variant: 'error' });
      return;
    }

    try {
      setSubmitting(true);
      await portfolioService.add(form.ticker.trim().toUpperCase(), Number(form.quantity), Number(form.price));
      setForm({ ticker: '', quantity: '', price: '' });
      showToast({ title: 'Holding saved', description: 'Your portfolio has been updated.', variant: 'success' });
      await loadPortfolio();
    } catch (err) {
      showToast({ title: 'Unable to save holding', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(ticker: string) {
    try {
      await portfolioService.remove(ticker);
      showToast({ title: 'Holding removed', description: `${ticker} was removed from your portfolio.`, variant: 'success' });
      await loadPortfolio();
    } catch (err) {
      showToast({ title: 'Remove failed', description: getErrorMessage(err), variant: 'error' });
    }
  }

  return (
    <ProtectedShell>
      <AppShell
        currentPage="portfolio"
        title="Portfolio"
        description="Live holdings and summary metrics sourced directly from your backend."
        actions={<Button variant="outline" onClick={() => void loadPortfolio()}>Refresh</Button>}
      >
        {loading ? (
          <LoadingState label="Loading portfolio..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadPortfolio()} />
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Current Value" value={formatCurrency(summary?.current_value)} />
              <MetricCard label="Total Invested" value={formatCurrency(summary?.total_invested)} />
              <MetricCard label="P&L" value={formatCurrency(summary?.total_pl)} tone={(summary?.total_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
              <MetricCard label="P&L %" value={`${(summary?.percent_pl ?? 0).toFixed(2)}%`} tone={(summary?.percent_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
            </div>

            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <SurfaceCard>
                <h2 className="text-xl font-bold text-white">Add Holding</h2>
                <form className="mt-5 space-y-4" onSubmit={handleAdd}>
                  <Input label="Ticker" value={form.ticker} onChange={(event) => setForm((current) => ({ ...current, ticker: event.target.value }))} />
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input label="Quantity" type="number" min="1" step="1" value={form.quantity} onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))} />
                    <Input label="Average Price" type="number" min="0" step="0.01" value={form.price} onChange={(event) => setForm((current) => ({ ...current, price: event.target.value }))} />
                  </div>
                  <Button type="submit" isLoading={submitting} fullWidth>Add / Update</Button>
                </form>
              </SurfaceCard>

              <SurfaceCard>
                <h2 className="text-xl font-bold text-white">Holdings</h2>
                <div className="mt-5 space-y-3">
                  {holdings.length ? holdings.map((holding) => (
                    <div key={holding.ticker} className="grid gap-4 rounded-2xl border border-white/5 bg-[#17161a] px-4 py-4 md:grid-cols-[1fr_auto_auto_auto] md:items-center">
                      <div>
                        <p className="font-semibold text-white">{holding.ticker}</p>
                        <p className="text-sm text-on-surface-variant">Average {formatCurrency(holding.average_price)}</p>
                      </div>
                      <p className="text-sm text-white">{holding.quantity.toFixed(2)} shares</p>
                      <p className="text-sm text-white">{formatCurrency(holding.quantity * holding.average_price)}</p>
                      <Button variant="ghost" onClick={() => void handleRemove(holding.ticker)}>Remove</Button>
                    </div>
                  )) : (
                    <EmptyState title="No holdings yet" message="Add your first position to begin tracking your portfolio." />
                  )}
                </div>
              </SurfaceCard>
            </div>
          </>
        )}
      </AppShell>
    </ProtectedShell>
  );
}
