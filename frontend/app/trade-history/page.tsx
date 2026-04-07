'use client';

import { useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, portfolioService, tradeService } from '@/lib/api-service';
import type { LiveQuote, PortfolioAllocationResponse, TradeHistoryItem, TradeHistorySummary } from '@/lib/types';
import { formatCurrency, formatPercent, exportToCSV } from '@/lib/sentinel-utils';

export default function TradeHistoryPage() {
  const [summary, setSummary] = useState<TradeHistorySummary | null>(null);
  const [history, setHistory] = useState<TradeHistoryItem[]>([]);
  const [allocation, setAllocation] = useState<PortfolioAllocationResponse | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([tradeService.summary(), tradeService.history(), portfolioService.allocation(), marketService.getLiveRibbon()]).then(([summaryResult, historyResult, allocationResult, ribbonResult]) => {
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
      if (historyResult.status === 'fulfilled') setHistory(historyResult.value);
      if (allocationResult.status === 'fulfilled') setAllocation(allocationResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  return (
    <ProtectedScreen>
      <SentinelShell title="Trade History" subtitle="Comprehensive ledger of all completed and pending executions." ribbon={ribbon}>
        <section className="mb-8 grid gap-4 md:grid-cols-4">
          <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Total Trades</p><p className="font-mono text-4xl text-white">{summary?.total_trades ?? 0}</p></SurfaceCard>
          <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Win Rate</p><p className="font-mono text-4xl text-secondary">{formatPercent(summary?.win_rate)}</p></SurfaceCard>
          <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Net Profit</p><p className="font-mono text-4xl text-secondary">{formatCurrency(summary?.total_profit_loss)}</p></SurfaceCard>
          <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Avg Execution</p><p className="font-mono text-4xl text-[var(--primary)]">142ms</p></SurfaceCard>
        </section>

        <div className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-9">
            <div className="flex items-center justify-between p-6 pb-0">
              <h3 className="text-lg font-bold text-white">Trade History</h3>
              <button
                onClick={() => exportToCSV(history, 'trade-history.csv')}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--on-primary)] hover:bg-[var(--primary)]/80"
              >
                Export CSV
              </button>
            </div>
            <table className="w-full">
              <thead className="text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                <tr>
                  <th className="px-6 py-4 text-left">Symbol</th>
                  <th className="px-6 py-4 text-left">Quantity</th>
                  <th className="px-6 py-4 text-left">Entry</th>
                  <th className="px-6 py-4 text-left">Exit</th>
                  <th className="px-6 py-4 text-left">Profit/Loss</th>
                  <th className="px-6 py-4 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((trade) => (
                  <tr key={trade.id} className="border-t border-white/5">
                    <td className="px-6 py-5 font-bold text-white">{trade.symbol}</td>
                    <td className="px-6 py-5 font-mono text-white">{trade.quantity.toFixed(2)}</td>
                    <td className="px-6 py-5 font-mono text-[var(--on-surface-variant)]">{formatCurrency(trade.entry_price)}</td>
                    <td className="px-6 py-5 font-mono text-[var(--on-surface-variant)]">{formatCurrency(trade.exit_price)}</td>
                    <td className={`px-6 py-5 font-mono ${(trade.profit_loss ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>{formatCurrency(trade.profit_loss)}</td>
                    <td className="px-6 py-5"><span className="rounded-full bg-secondary/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-secondary">Closed</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </SurfaceCard>
          <div className="col-span-12 space-y-6 lg:col-span-3">
            <SurfaceCard className="p-6">
              <h3 className="mb-5 text-xl font-bold text-white">Asset Allocation</h3>
              <div className="space-y-4">
                {allocation?.allocations.map((item) => (
                  <div key={item.category}>
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <span className="text-[var(--on-surface-variant)]">{item.category}</span>
                      <span className="font-mono text-white">{item.percent.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--surface-high)]">
                      <div className="h-full rounded-full bg-[var(--primary)]" style={{ width: `${item.percent}%` }} />
                    </div>
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
