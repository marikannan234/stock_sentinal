'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { MetricCard, SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getErrorMessage, tradeService } from '@/lib/api-service';
import { formatCurrency, formatDateTime, formatPercent } from '@/lib/format';
import type { TradeHistoryItem, TradeHistorySummary } from '@/lib/types';

export default function TradeHistoryPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState<TradeHistorySummary | null>(null);
  const [history, setHistory] = useState<TradeHistoryItem[]>([]);
  const [filter, setFilter] = useState('');

  async function loadHistory(symbolFilter?: string) {
    try {
      setLoading(true);
      setError('');
      const [summaryData, historyData] = await Promise.all([
        tradeService.summary(),
        tradeService.history(symbolFilter?.trim() ? symbolFilter.trim().toUpperCase() : undefined),
      ]);
      setSummary(summaryData);
      setHistory(historyData);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load trade history.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadHistory();
  }, []);

  return (
    <ProtectedShell>
      <AppShell
        currentPage="trade history"
        title="Trade History"
        description="Closed trade performance and execution analytics from `/trade/history/list` and `/trade/summary/stats`."
        actions={<Button variant="outline" onClick={() => void loadHistory(filter)}>Refresh</Button>}
      >
        <SurfaceCard>
          <form
            className="flex flex-col gap-3 md:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              void loadHistory(filter);
            }}
          >
            <Input label="Filter by Symbol" value={filter} onChange={(event) => setFilter(event.target.value)} className="md:flex-1" />
            <Button type="submit" className="md:self-end">Apply Filter</Button>
          </form>
        </SurfaceCard>
        {loading ? (
          <LoadingState label="Loading trade history..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadHistory(filter)} />
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Total Trades" value={String(summary?.total_trades ?? 0)} />
              <MetricCard label="Net P&L" value={formatCurrency(summary?.total_profit_loss)} tone={(summary?.total_profit_loss ?? 0) >= 0 ? 'positive' : 'negative'} />
              <MetricCard label="Win Rate" value={formatPercent(summary?.win_rate)} tone="primary" />
              <MetricCard label="Average Trade" value={formatCurrency(summary?.avg_profit_loss)} />
            </div>
            <SurfaceCard>
              <h2 className="text-xl font-bold text-white">Closed Trades</h2>
              <div className="mt-5 space-y-3">
                {history.length ? history.map((trade) => (
                  <div key={trade.id} className="grid gap-4 rounded-2xl border border-white/5 bg-[#17161a] px-4 py-4 lg:grid-cols-[1fr_auto_auto_auto] lg:items-center">
                    <div>
                      <p className="font-semibold text-white">{trade.symbol}</p>
                      <p className="mt-1 text-sm text-on-surface-variant">{trade.trade_type} · {trade.quantity} shares</p>
                      <p className="mt-1 text-xs text-on-surface-variant">Closed {formatDateTime(trade.closed_at)}</p>
                    </div>
                    <div className="text-sm text-white">
                      <p>Entry {formatCurrency(trade.entry_price)}</p>
                      <p className="mt-1">Exit {formatCurrency(trade.exit_price)}</p>
                    </div>
                    <div className={`text-sm font-semibold ${(trade.profit_loss ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                      <p>{formatCurrency(trade.profit_loss)}</p>
                      <p className="mt-1">{formatPercent(trade.profit_loss_percent)}</p>
                    </div>
                    <p className="text-sm text-on-surface-variant">{trade.duration_minutes ?? 0} min</p>
                  </div>
                )) : (
                  <EmptyState title="No closed trades" message="Complete a trade to see history and performance metrics here." />
                )}
              </div>
            </SurfaceCard>
          </>
        )}
      </AppShell>
    </ProtectedShell>
  );
}
