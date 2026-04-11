'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { ErrorBoundary } from '@/components/sentinel/error-boundary';
import { marketService, tradeService } from '@/lib/api-service';
import type { LiveQuote, TradeHistoryItem, TradeHistorySummary } from '@/lib/types';
import { formatCurrency, formatPercent, exportToCSV } from '@/lib/sentinel-utils';

type FilterType = 'all' | 'profitable' | 'loss';
type SortType = 'latest' | 'oldest' | 'highest-profit';

export default function TradeHistoryPage() {
  const [summary, setSummary] = useState<TradeHistorySummary | null>(null);
  const [history, setHistory] = useState<TradeHistoryItem[]>([]);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  
  // UI States
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<SortType>('latest');

  // Fetch data
  useEffect(() => {
    setLoadingSummary(true);
    Promise.all([
      tradeService.historySummary().then(setSummary).catch(() => setSummary(null)),
      marketService.getLiveRibbon().then((res) => setRibbon(res.stocks.slice(0, 8))).catch(() => setRibbon([])),
    ]).finally(() => setLoadingSummary(false));
  }, []);

  useEffect(() => {
    setLoadingHistory(true);
    tradeService
      .history()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false));
  }, []);

  // Listen for trade completion events to refresh history
  useEffect(() => {
    const handleTradeCompleted = () => {
      // Refresh trade history and summary after trade
      setLoadingHistory(true);
      Promise.all([
        tradeService.historySummary().then(setSummary).catch(() => setSummary(null)),
        tradeService.history()
          .then(setHistory)
          .catch(() => setHistory([])),
      ]).finally(() => setLoadingHistory(false));
    };

    window.addEventListener('tradeCompleted', handleTradeCompleted);
    return () => window.removeEventListener('tradeCompleted', handleTradeCompleted);
  }, []);

  // Filter trades
  const filteredTrades = useMemo(() => {
    let filtered = [...history];

    if (filter === 'profitable') {
      filtered = filtered.filter((trade) => (trade.profit_loss ?? 0) > 0);
    } else if (filter === 'loss') {
      filtered = filtered.filter((trade) => (trade.profit_loss ?? 0) < 0);
    }

    return filtered;
  }, [history, filter]);

  // Sort trades
  const sortedTrades = useMemo(() => {
    const sorted = [...filteredTrades];

    if (sortBy === 'latest') {
      return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else if (sortBy === 'oldest') {
      return sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    } else if (sortBy === 'highest-profit') {
      return sorted.sort((a, b) => (b.profit_loss ?? 0) - (a.profit_loss ?? 0));
    }

    return sorted;
  }, [filteredTrades, sortBy]);

  const hasNoTrades = history.length === 0 && !loadingHistory;
  const filteredCount = filteredTrades.length;

  return (
    <ProtectedScreen>
      <ErrorBoundary>
        <SentinelShell
          title="Trade History"
          subtitle="Comprehensive ledger of all completed and pending executions."
          ribbon={ribbon}
        >
        {/* Summary Cards */}
        <section className="mb-8 grid gap-4 md:grid-cols-4">
          <SurfaceCard className="p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
              Total Trades
            </p>
            {loadingSummary ? (
              <div className="mt-2 h-10 w-20 animate-pulse rounded bg-[var(--surface-high)]" />
            ) : (
              <p className="font-mono text-4xl text-white">{summary?.total_trades ?? 0}</p>
            )}
          </SurfaceCard>

          <SurfaceCard className="p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
              Win Rate
            </p>
            {loadingSummary ? (
              <div className="mt-2 h-10 w-20 animate-pulse rounded bg-[var(--surface-high)]" />
            ) : (
              <p className="font-mono text-4xl text-secondary">{formatPercent(summary?.win_rate)}</p>
            )}
          </SurfaceCard>

          <SurfaceCard className="p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
              Net Profit
            </p>
            {loadingSummary ? (
              <div className="mt-2 h-10 w-20 animate-pulse rounded bg-[var(--surface-high)]" />
            ) : (
              <p className={`font-mono text-4xl ${(summary?.net_profit ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                {(summary?.net_profit ?? 0) >= 0 ? '+' : ''}{formatCurrency(summary?.net_profit ?? 0)}
              </p>
            )}
          </SurfaceCard>

          <SurfaceCard className="p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
              Avg Execution
            </p>
            {loadingSummary ? (
              <div className="mt-2 h-10 w-20 animate-pulse rounded bg-[var(--surface-high)]" />
            ) : (
              <p className="font-mono text-4xl text-[var(--primary)]">
                {summary?.avg_execution ? Math.round(summary.avg_execution) + 'min' : 'N/A'}
              </p>
            )}
          </SurfaceCard>
        </section>

        {/* Main Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Table Section */}
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-9">
            {/* Header with Controls */}
            <div className="border-b border-white/5 px-6 py-4">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Trade History</h2>
                  <p className="text-sm text-[var(--on-surface-variant)]">
                    {loadingHistory ? 'Loading...' : filteredCount === 0 && hasNoTrades ? 'No trades' : `${filteredCount} trade${filteredCount !== 1 ? 's' : ''}`}
                  </p>
                </div>

                <button
                  onClick={() => exportToCSV(sortedTrades, 'trade-history.csv')}
                  disabled={sortedTrades.length === 0}
                  className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--on-primary)] hover:bg-[var(--primary)]/80 disabled:opacity-40"
                >
                  Export CSV
                </button>
              </div>

              {/* Filter and Sort Controls */}
              <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex gap-2">
                  {(['all', 'profitable', 'loss'] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => setFilter(f)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-wider transition-all ${
                        filter === f
                          ? 'bg-[var(--primary)]/20 text-[var(--primary)]'
                          : 'bg-[var(--surface-high)] text-[var(--on-surface-variant)] hover:text-white'
                      }`}
                    >
                      {f === 'all' ? 'All Trades' : f === 'profitable' ? 'Profitable' : 'Loss'}
                    </button>
                  ))}
                </div>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortType)}
                  className="rounded-lg bg-[var(--surface-high)] px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white outline-none transition-all hover:bg-[var(--surface-highest)]"
                >
                  <option value="latest">Latest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="highest-profit">Highest Profit</option>
                </select>
              </div>
            </div>

            {/* Empty State */}
            {hasNoTrades ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="text-center">
                  <p className="text-3xl mb-2">📊</p>
                  <p className="text-lg font-bold text-white">No trades yet</p>
                  <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
                    Start your trading journey by executing your first trade.
                  </p>
                </div>
              </div>
            ) : (
              <>
                {/* Loading State */}
                {loadingHistory ? (
                  <div className="space-y-2 p-6">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="h-12 animate-pulse rounded bg-[var(--surface-high)]" />
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left">
                        <thead className="bg-[rgba(53,52,55,0.4)] text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                          <tr>
                            <th className="px-6 py-3">Symbol</th>
                            <th className="px-6 py-3">Quantity</th>
                            <th className="px-6 py-3">Entry</th>
                            <th className="px-6 py-3">Exit</th>
                            <th className="px-6 py-3">Profit/Loss</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3">Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedTrades.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="px-6 py-8 text-center">
                                <p className="text-sm text-[var(--on-surface-variant)]">
                                  No trades match your filter
                                </p>
                              </td>
                            </tr>
                          ) : (
                            sortedTrades.map((trade, idx) => {
                              const isOpen = !trade.exit_price;
                              const profit = trade.profit_loss ?? 0;
                              const isProfitable = profit > 0;

                              return (
                                <tr
                                  key={trade.id}
                                  className={`border-t border-white/5 transition-colors hover:bg-[rgba(255,255,255,0.03)] ${
                                    idx % 2 ? 'bg-[rgba(14,14,16,0.16)]' : ''
                                  }`}
                                >
                                  <td className="px-6 py-4 font-bold text-white">{trade.symbol}</td>
                                  <td className="px-6 py-4 font-mono text-sm">{trade.quantity.toFixed(2)}</td>
                                  <td className="px-6 py-4 font-mono text-sm text-[var(--on-surface-variant)]">
                                    {formatCurrency(trade.entry_price)}
                                  </td>
                                  <td className="px-6 py-4 font-mono text-sm text-[var(--on-surface-variant)]">
                                    {trade.exit_price ? formatCurrency(trade.exit_price) : '—'}
                                  </td>
                                  <td className={`px-6 py-4 font-mono font-bold ${isProfitable ? 'text-[#4edea3]' : 'text-[#ffb3ad]'}`}>
                                    <div>
                                      {profit >= 0 ? '+' : ''}{formatCurrency(profit)}
                                    </div>
                                    {trade.profit_loss_percent !== null && trade.profit_loss_percent !== undefined && (
                                      <div className="text-xs opacity-80">
                                        ({profit >= 0 ? '+' : ''}{trade.profit_loss_percent.toFixed(2)}%)
                                      </div>
                                    )}
                                  </td>
                                  <td className="px-6 py-4">
                                    <span
                                      className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] transition-all ${
                                        isOpen
                                          ? 'bg-[#f9c74f]/10 text-[#f9c74f]'
                                          : profit >= 0
                                            ? 'bg-secondary/10 text-secondary'
                                            : 'bg-tertiary/10 text-tertiary'
                                      }`}
                                    >
                                      {isOpen ? 'Open' : profit >= 0 ? 'Win' : 'Loss'}
                                    </span>
                                  </td>
                                  <td className="px-6 py-4 text-sm text-[var(--on-surface-variant)]">
                                    {new Date(trade.created_at).toLocaleDateString('en-US', {
                                      month: 'short',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })}
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </>
            )}
          </SurfaceCard>

          {/* Sidebar */}
          <div className="col-span-12 space-y-6 lg:col-span-3">
            {/* Stats Card */}
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-white">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--on-surface-variant)]">Total Trades</span>
                  <span className="font-mono text-sm font-bold text-white">{history.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--on-surface-variant)]">Winning Trades</span>
                  <span className="font-mono text-sm font-bold text-[#4edea3]">
                    {history.filter((t) => (t.profit_loss ?? 0) > 0).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--on-surface-variant)]">Losing Trades</span>
                  <span className="font-mono text-sm font-bold text-[#ffb3ad]">
                    {history.filter((t) => (t.profit_loss ?? 0) < 0).length}
                  </span>
                </div>
                <div className="border-t border-white/10 pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--on-surface-variant)]">Open Trades</span>
                    <span className="font-mono text-sm font-bold text-[#f9c74f]">
                      {history.filter((t) => !t.exit_price).length}
                    </span>
                  </div>
                </div>
              </div>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
      </ErrorBoundary>
    </ProtectedScreen>
  );
}
