'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { AllocationDonut, SentinelLineChart } from '@/components/sentinel/charts';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, portfolioService } from '@/lib/api-service';
import type { LiveQuote, PortfolioAllocationResponse, PortfolioGrowthPoint, PortfolioHolding, PortfolioSummary } from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/sentinel-utils';

const ranges: Array<'1d' | '1w' | '1m' | '1y'> = ['1d', '1w', '1m', '1y'];

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [allocation, setAllocation] = useState<PortfolioAllocationResponse | null>(null);
  const [growth, setGrowth] = useState<PortfolioGrowthPoint[]>([]);
  const [range, setRange] = useState<'1d' | '1w' | '1m' | '1y'>('1y');
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([portfolioService.summary(), portfolioService.list(), portfolioService.allocation(), marketService.getLiveRibbon()]).then(
      ([summaryResult, holdingsResult, allocationResult, ribbonResult]) => {
        if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
        if (holdingsResult.status === 'fulfilled') setHoldings(holdingsResult.value);
        if (allocationResult.status === 'fulfilled') setAllocation(allocationResult.value);
        if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
      },
    );
  }, []);

  useEffect(() => {
    portfolioService.growth(range).then(setGrowth).catch(() => setGrowth([]));
  }, [range]);

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
      <SentinelShell
        title="Portfolio Overview"
        subtitle="Real-time valuation and performance metrics."
        ribbon={ribbon}
        headerActions={
          <div className="flex gap-3">
            <button className="rounded-2xl bg-[var(--surface-high)] px-5 py-3 text-sm font-bold text-white">Export Report</button>
            <button className="rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-3 text-sm font-bold text-[var(--on-primary)]">Add New Holding</button>
          </div>
        }
      >
        <section className="mb-8 grid gap-6 md:grid-cols-4">
          {[
            ['Total Invested', formatCurrency(summary?.total_invested)],
            ['Current Value', formatCurrency(summary?.current_value)],
            ['Overall P&L', `${formatCurrency(summary?.total_pl)} ${formatPercent(summary?.percent_pl)}`],
            ['Buying Power', formatCurrency(summary?.buying_power)],
          ].map(([label, value], index) => (
            <SurfaceCard key={label} className="p-6">
              <p className="mb-2 text-[11px] font-black uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">{label}</p>
              <p className={`font-mono text-[38px] font-medium tracking-[-0.06em] ${index === 2 ? ((summary?.total_pl ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary') : 'text-white'}`}>
                {value}
              </p>
            </SurfaceCard>
          ))}
        </section>

        <section className="grid grid-cols-12 gap-8">
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="flex items-center justify-between border-b border-white/5 px-6 py-5">
              <h2 className="text-lg font-bold text-white">Portfolio Holdings</h2>
              <div className="flex gap-2">
                <span className="rounded-full bg-[var(--surface-high)] px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Stocks ({holdings.filter((item) => item.asset_class !== 'Crypto').length})</span>
                <span className="rounded-full bg-[var(--surface-high)] px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Crypto ({holdings.filter((item) => item.asset_class === 'Crypto').length})</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[rgba(53,52,55,0.4)] text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                  <tr>
                    <th className="px-6 py-4">Symbol</th>
                    <th className="px-6 py-4">Quantity</th>
                    <th className="px-6 py-4">Avg Price</th>
                    <th className="px-6 py-4">Current Price</th>
                    <th className="px-6 py-4 text-right">P&L Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding, index) => (
                    <tr key={holding.ticker} className={index % 2 ? 'bg-[rgba(14,14,16,0.16)]' : ''}>
                      <td className="px-6 py-5">
                        <div>
                          <p className="font-bold text-white">{holding.ticker}</p>
                          <p className="text-[10px] text-[var(--on-surface-variant)]">{holding.name ?? holding.ticker}</p>
                        </div>
                      </td>
                      <td className="px-6 py-5 font-mono">{holding.quantity.toFixed(2)}</td>
                      <td className="px-6 py-5 font-mono text-[var(--on-surface-variant)]">{formatCurrency(holding.average_price)}</td>
                      <td className="px-6 py-5 font-mono text-white">{formatCurrency(holding.current_price)}</td>
                      <td className="px-6 py-5 text-right">
                        <p className={`font-mono ${((holding.pl_amount ?? 0) >= 0) ? 'text-secondary' : 'text-tertiary'}`}>{formatCurrency(holding.pl_amount)}</p>
                        <p className={`text-[10px] font-mono ${((holding.pl_percent ?? 0) >= 0) ? 'text-secondary/80' : 'text-tertiary/80'}`}>{formatPercent(holding.pl_percent)}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SurfaceCard>

          <div className="col-span-12 space-y-8 lg:col-span-4">
            <SurfaceCard className="p-6">
              <h2 className="mb-6 text-sm font-bold uppercase tracking-[0.18em] text-white">Asset Allocation</h2>
              <AllocationDonut items={allocation?.allocations ?? []} totalValue={allocation?.total_value ?? 0} />
            </SurfaceCard>

            <SurfaceCard className="flex items-center justify-between border border-secondary/20 bg-[rgba(78,222,163,0.08)] p-5">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.22em] text-secondary">Top Performer</p>
                <p className="text-sm font-bold text-white">{topPerformer?.ticker ?? 'N/A'}</p>
              </div>
              <p className="font-mono text-lg font-bold text-secondary">{formatPercent(topPerformer?.pl_percent)}</p>
            </SurfaceCard>
            <SurfaceCard className="flex items-center justify-between border border-[#7d3933]/30 bg-[rgba(125,57,51,0.18)] p-5">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.22em] text-tertiary">Worst Performer</p>
                <p className="text-sm font-bold text-white">{worstPerformer?.ticker ?? 'N/A'}</p>
              </div>
              <p className="font-mono text-lg font-bold text-tertiary">{formatPercent(worstPerformer?.pl_percent)}</p>
            </SurfaceCard>
          </div>
        </section>

        <SurfaceCard className="mt-8 p-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Portfolio Growth</h2>
              <p className="text-sm text-[var(--on-surface-variant)]">Value tracked over the selected period.</p>
            </div>
            <div className="flex rounded-xl bg-[var(--surface-lowest)] p-1">
              {ranges.map((option) => (
                <button key={option} onClick={() => setRange(option)} className={option === range ? 'rounded-lg bg-[var(--surface-bright)] px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-white' : 'px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]'}>
                  {option.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <SentinelLineChart points={growth} />
        </SurfaceCard>
      </SentinelShell>
    </ProtectedScreen>
  );
}
