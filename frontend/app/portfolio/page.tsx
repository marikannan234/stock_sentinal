'use client';

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { AllocationDonut, SentinelLineChart } from '@/components/sentinel/charts';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard, Icon } from '@/components/sentinel/primitives';
import { ErrorBoundary } from '@/components/sentinel/error-boundary';
import {
  usePortfolioAllocationQuery,
  usePortfolioGrowthQuery,
  usePortfolioHoldingsQuery,
  usePortfolioSummaryQuery,
} from '@/hooks/queries/use-portfolio';
import { useSymbolSearchQuery } from '@/hooks/queries/use-symbol-search';
import { useBuyMutation } from '@/hooks/queries/use-trades';
import { getErrorMessage } from '@/lib/api-service';
import type { SymbolSearchItem } from '@/lib/types';
import { formatCurrency, formatPercent, exportToCSV } from '@/lib/sentinel-utils';

const ranges: Array<'1d' | '1w' | '1m' | '1y'> = ['1d', '1w', '1m', '1y'];

export default function PortfolioPage() {
  const [range, setRange] = useState<'1d' | '1w' | '1m' | '1y'>('1y');

  // Server data; refreshed by the trade mutations (they invalidate ['portfolio']).
  const summaryQuery = usePortfolioSummaryQuery();
  const holdingsQuery = usePortfolioHoldingsQuery();
  const allocationQuery = usePortfolioAllocationQuery();
  const growthQuery = usePortfolioGrowthQuery(range);
  const summary = summaryQuery.data;
  const holdings = useMemo(() => holdingsQuery.data ?? [], [holdingsQuery.data]);
  const allocation = allocationQuery.data;
  const growth = growthQuery.data ?? [];
  const loadingSummary = summaryQuery.isPending;
  const loadingHoldings = holdingsQuery.isPending;
  // First load of a range, or a new range loading behind the previous chart.
  const loadingGrowth = growthQuery.isPending || growthQuery.isPlaceholderData;

  const buyMutation = useBuyMutation();

  // Add Holding form state
  const [showAddForm, setShowAddForm] = useState(false);

  // Symbol autocomplete state
  const [symbolQuery, setSymbolQuery] = useState('');          // raw text the user types
  const [debouncedSymbolQuery, setDebouncedSymbolQuery] = useState('');
  const [symbolValidated, setSymbolValidated] = useState('');  // confirmed ticker from a suggestion
  const [symbolName, setSymbolName] = useState('');            // human name of the validated ticker
  const [symbolDropdownOpen, setSymbolDropdownOpen] = useState(false);
  const symbolDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const symbolWrapRef = useRef<HTMLDivElement>(null);

  const searchQuery = useSymbolSearchQuery(symbolValidated ? '' : debouncedSymbolQuery);
  const symbolSuggestions: SymbolSearchItem[] = useMemo(() => (searchQuery.data ?? []).slice(0, 8), [searchQuery.data]);
  const symbolSearching = searchQuery.isFetching;

  const [addQty, setAddQty] = useState('');
  const [addError, setAddError] = useState('');
  const addLoading = buyMutation.isPending;

  // Close dropdown on outside click
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (symbolWrapRef.current && !symbolWrapRef.current.contains(e.target as Node)) {
        setSymbolDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  function handleSymbolChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setSymbolQuery(val);
    setSymbolValidated('');   // reset validation when user edits freely
    setSymbolName('');
    setAddError('');
    setSymbolDropdownOpen(true);
    if (symbolDebounce.current) clearTimeout(symbolDebounce.current);
    symbolDebounce.current = setTimeout(() => setDebouncedSymbolQuery(val), 280);
  }

  function handleSymbolSelect(item: SymbolSearchItem) {
    setSymbolQuery(item.ticker);      // show ticker in the input
    setSymbolValidated(item.ticker);  // lock in the validated symbol
    setSymbolName(item.name ?? '');
    setSymbolDropdownOpen(false);
    setAddError('');
  }

  function resetAddForm() {
    setSymbolQuery('');
    setDebouncedSymbolQuery('');
    setSymbolValidated('');
    setSymbolName('');
    setSymbolDropdownOpen(false);
    setAddQty('');
    setAddError('');
  }

  async function handleAddHolding(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!symbolValidated) {
      setAddError('Please search and select a valid stock symbol from the dropdown.');
      return;
    }
    if (!addQty) return;

    setAddError('');
    try {
      // Buy at the current market price; the server sets the execution price
      await buyMutation.mutateAsync({ symbol: symbolValidated, quantity: Number(addQty) });
      resetAddForm();
      setShowAddForm(false);
    } catch (err) {
      setAddError(getErrorMessage(err));
    }
  }

  const topPerformer = useMemo(
    () => [...holdings].sort((a, b) => (b.pl_percent ?? -Infinity) - (a.pl_percent ?? -Infinity))[0],
    [holdings],
  );
  const worstPerformer = useMemo(
    () => [...holdings].sort((a, b) => (a.pl_percent ?? Infinity) - (b.pl_percent ?? Infinity))[0],
    [holdings],
  );

  return (
    <ProtectedScreen>
      <ErrorBoundary>
        <SentinelShell
          title="Portfolio Overview"
          subtitle="Real-time valuation and performance metrics."
          headerActions={
            <div className="flex gap-3">
              <button
                onClick={() => { setShowAddForm((p) => !p); setAddError(''); }}
                className="rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-3 text-sm font-bold text-[var(--on-primary)]"
              >
                {showAddForm ? 'Cancel' : 'Add Holding'}
              </button>
            </div>
          }
        >
        {/* ── Summary Cards ── */}
        <section className="mb-8 grid gap-4 md:grid-cols-4">
          {loadingSummary ? (
            <>
              {Array.from({ length: 4 }).map((_, i) => (
                <SurfaceCard key={i} className="p-5 min-h-[140px] flex flex-col justify-between">
                  <div className="mb-2 h-3 w-24 animate-pulse rounded bg-[var(--surface-bright)]" />
                  <div className="h-8 w-32 animate-pulse rounded bg-[var(--surface-bright)]" />
                </SurfaceCard>
              ))}
            </>
          ) : (
            (
              [
                ['Total Invested', summary ? formatCurrency(summary.total_invested) : '—'],
                ['Current Value', summary ? formatCurrency(summary.current_value) : '—'],
                ['Overall P&L', summary ? `${formatCurrency(summary.total_pl)} ${formatPercent(summary.percent_pl)}` : '—'],
                ['Buying Power', summary ? formatCurrency(summary.buying_power) : '—'],
              ] as [string, string][]
            ).map(([label, value], index) => (
              <SurfaceCard key={label} className="p-5 min-h-[140px] flex flex-col justify-between">
                <p className="mb-2 text-[11px] font-black uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">{label}</p>
                <p className={`font-mono text-[28px] font-medium tracking-[-0.05em] transition-all duration-300 ease-out ${
                  index === 2 ? ((summary?.total_pl ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary') : 'text-white'
                }`}>
                  {value}
                </p>
              </SurfaceCard>
            ))
          )}
        </section>

        {/* ── Add Holding Inline Form ── */}
        <div
          className="overflow-hidden transition-all duration-300"
          style={{ maxHeight: showAddForm ? '420px' : '0', opacity: showAddForm ? 1 : 0 }}
        >
          <SurfaceCard className="mb-6 p-6">
            <h3 className="mb-4 text-base font-bold text-white">Add New Holding</h3>
            <form onSubmit={handleAddHolding}>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 mb-4">
                {/* ── Symbol autocomplete ── */}
                <div ref={symbolWrapRef} className="relative">
                  <div className={`flex items-center rounded-xl px-3 py-3 text-sm font-mono outline-none transition-all ${
                    symbolValidated
                      ? 'bg-[var(--surface-lowest)] ring-2 ring-secondary/40'
                      : 'bg-[var(--surface-lowest)] focus-within:ring-2 focus-within:ring-[var(--primary)]/40'
                  }`}>
                    {symbolValidated ? (
                      <Icon name="check_circle" className="mr-2 shrink-0 text-[16px] text-secondary" />
                    ) : symbolSearching ? (
                      <Icon name="progress_activity" className="mr-2 shrink-0 animate-spin text-[16px] text-[var(--on-surface-variant)]" />
                    ) : (
                      <Icon name="search" className="mr-2 shrink-0 text-[16px] text-[var(--on-surface-variant)]" />
                    )}
                    <input
                      value={symbolQuery}
                      onChange={handleSymbolChange}
                      onFocus={() => symbolQuery && !symbolValidated && setSymbolDropdownOpen(symbolSuggestions.length > 0)}
                      className="w-full bg-transparent text-white outline-none placeholder:text-[var(--on-surface-variant)]"
                      placeholder="Search symbol or company…"
                      autoComplete="off"
                    />
                    {symbolValidated && (
                      <button
                        type="button"
                        onClick={() => { setSymbolQuery(''); setSymbolValidated(''); setSymbolName(''); setAddError(''); }}
                        className="ml-1 shrink-0 text-[var(--on-surface-variant)] hover:text-white"
                      >
                        <Icon name="close" className="text-[14px]" />
                      </button>
                    )}
                  </div>
                  {symbolValidated && symbolName && (
                    <p className="mt-1 truncate px-1 text-[10px] text-secondary">{symbolName}</p>
                  )}
                  {/* Dropdown */}
                  {symbolDropdownOpen && symbolSuggestions.length > 0 && !symbolValidated && (
                    <div className="absolute left-0 top-full z-[300] mt-1 w-full rounded-2xl border border-white/10 bg-[#1c1c1e] shadow-2xl">
                      {symbolSuggestions.map((item) => (
                        <button
                          key={item.ticker}
                          type="button"
                          onMouseDown={(e) => { e.preventDefault(); handleSymbolSelect(item); }}
                          className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-[var(--surface-high)] first:rounded-t-2xl last:rounded-b-2xl"
                        >
                          <span className="font-mono text-sm font-bold text-white">{item.ticker}</span>
                          {item.name && <span className="truncate text-xs text-[var(--on-surface-variant)]">{item.name}</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* ── Quantity ── */}
                <input
                  value={addQty}
                  onChange={(e) => setAddQty(e.target.value)}
                  type="number"
                  min="0.001"
                  step="0.001"
                  className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm font-mono text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                  placeholder="Quantity"
                  required
                />
              </div>
              <p className="mb-3 text-xs text-[var(--on-surface-variant)]">Buys at the current market price using your available cash.</p>
              {addError && <p className="mb-3 text-xs text-tertiary">{addError}</p>}
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={addLoading || !symbolValidated}
                  className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-6 py-2.5 text-sm font-bold text-[var(--on-primary)] disabled:opacity-40"
                >
                  {addLoading ? 'Saving…' : 'Add'}
                </button>
                <button
                  type="button"
                  onClick={() => { resetAddForm(); setShowAddForm(false); }}
                  className="rounded-xl bg-[var(--surface-high)] px-6 py-2.5 text-sm font-bold text-white"
                >
                  Cancel
                </button>
              </div>
            </form>
          </SurfaceCard>
        </div>

        {/* ── Holdings + Allocation ── */}
        <section className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
              <h2 className="text-base font-bold text-white">Portfolio Holdings</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => exportToCSV(holdings, 'portfolio-holdings.csv')}
                  className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--on-primary)] hover:bg-[var(--primary)]/80"
                >
                  Export CSV
                </button>
                <span className="rounded-full bg-[var(--surface-high)] px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">
                  Stocks ({holdings.filter((h) => h.asset_class !== 'Crypto').length})
                </span>
                <span className="rounded-full bg-[var(--surface-high)] px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">
                  Crypto ({holdings.filter((h) => h.asset_class === 'Crypto').length})
                </span>
              </div>
            </div>
            {holdingsQuery.isError ? (
              <div className="flex items-center justify-between px-6 py-6">
                <p className="text-sm text-tertiary">Failed to load holdings.</p>
                <button onClick={() => holdingsQuery.refetch()} className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs text-white">Retry</button>
              </div>
            ) : loadingHoldings || holdings.length === 0 ? (
              loadingHoldings ? (
                <div className="space-y-2 p-6">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-4 border-b border-white/5 py-4 px-5">
                      <div className="h-4 w-12 animate-pulse rounded bg-[var(--surface-bright)]" />
                      <div className="flex-1 space-y-2">
                        <div className="h-3 w-24 animate-pulse rounded bg-[var(--surface-bright)]" />
                        <div className="h-2 w-32 animate-pulse rounded bg-[var(--surface-low)]" />
                      </div>
                      <div className="h-4 w-16 animate-pulse rounded bg-[var(--surface-bright)]" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="px-6 py-8 text-sm text-[var(--on-surface-variant)]">No holdings found. Add one above to get started.</p>
              )
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-[rgba(53,52,55,0.4)] text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                    <tr>
                      <th className="px-5 py-3">Symbol</th>
                      <th className="px-5 py-3">Qty</th>
                      <th className="px-5 py-3">Avg Price</th>
                      <th className="px-5 py-3">Current</th>
                      <th className="px-5 py-3">Day %</th>
                      <th className="px-5 py-3 text-right">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map((holding, index) => (
                      <tr key={holding.ticker} className={index % 2 ? 'bg-[rgba(14,14,16,0.16)]' : ''}>
                        <td className="px-5 py-4">
                          <div>
                            <p className="text-sm font-bold text-white">{holding.ticker}</p>
                            <p className="text-[10px] text-[var(--on-surface-variant)]">{holding.name ?? holding.ticker}</p>
                          </div>
                        </td>
                        <td className="px-5 py-4 font-mono text-sm">{holding.quantity.toFixed(2)}</td>
                        <td className="px-5 py-4 font-mono text-sm text-[var(--on-surface-variant)]">{formatCurrency(holding.average_price)}</td>
                        <td className="px-5 py-4 font-mono text-sm text-white">{formatCurrency(holding.current_price)}</td>
                        <td className={`px-5 py-4 font-mono text-sm ${(holding.day_change_percent ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                          {formatPercent(holding.day_change_percent)}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <p className={`font-mono text-sm transition-colors duration-300 ${(holding.pl_amount ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                            {formatCurrency(holding.pl_amount)}
                          </p>
                          <p className={`font-mono text-[10px] transition-colors duration-300 ${(holding.pl_percent ?? 0) >= 0 ? 'text-secondary/80' : 'text-tertiary/80'}`}>
                            {formatPercent(holding.pl_percent)}
                          </p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SurfaceCard>

          <div className="col-span-12 space-y-6 lg:col-span-4">
            <SurfaceCard className="p-6">
              <h2 className="mb-5 text-sm font-bold uppercase tracking-[0.18em] text-white">Asset Allocation</h2>
              <AllocationDonut items={allocation?.allocations ?? []} totalValue={allocation?.total_value ?? 0} />
            </SurfaceCard>

            {topPerformer && (
              <SurfaceCard className="flex items-center justify-between border border-secondary/20 bg-[rgba(78,222,163,0.08)] p-5">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.22em] text-secondary">Top Performer</p>
                  <p className="text-sm font-bold text-white">{topPerformer.ticker}</p>
                </div>
                <p className="font-mono text-lg font-bold text-secondary">{formatPercent(topPerformer.pl_percent)}</p>
              </SurfaceCard>
            )}
            {worstPerformer && topPerformer?.ticker !== worstPerformer?.ticker && (
              <SurfaceCard className="flex items-center justify-between border border-[#7d3933]/30 bg-[rgba(125,57,51,0.18)] p-5">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.22em] text-tertiary">Worst Performer</p>
                  <p className="text-sm font-bold text-white">{worstPerformer.ticker}</p>
                </div>
                <p className="font-mono text-lg font-bold text-tertiary">{formatPercent(worstPerformer.pl_percent)}</p>
              </SurfaceCard>
            )}
          </div>
        </section>

        {/* ── Portfolio Growth ── */}
        <SurfaceCard className="relative mt-6 p-6 min-h-[450px]">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Portfolio Growth</h2>
              <p className="text-sm text-[var(--on-surface-variant)]">Value tracked over the selected period (real data).</p>
            </div>
            <div className="flex rounded-xl bg-[var(--surface-lowest)] p-1">
              {ranges.map((option) => (
                <button
                  key={option}
                  onClick={() => setRange(option)}
                  className={
                    option === range
                      ? 'rounded-lg bg-[var(--surface-bright)] px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-white transition-colors duration-200'
                      : 'px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)] hover:text-white transition-colors duration-200'
                  }
                >
                  {(option || "").toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div className={`transition-opacity duration-300 ease-in-out ${loadingGrowth ? 'opacity-50' : 'opacity-100'}`}>
            <SentinelLineChart points={growth} />
          </div>
          {loadingGrowth && (
            <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-[rgba(0,0,0,0.3)] backdrop-blur-sm">
              <div className="flex flex-col items-center gap-2">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--primary)] border-r-transparent" />
                <p className="text-xs text-[var(--on-surface-variant)]">Loading chart...</p>
              </div>
            </div>
          )}
        </SurfaceCard>
      </SentinelShell>
      </ErrorBoundary>
    </ProtectedScreen>
  );
}
