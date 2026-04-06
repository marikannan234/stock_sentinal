'use client';

import { useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelLineChart } from '@/components/sentinel/charts';
import { SentinelShell } from '@/components/sentinel/shell';
import { Icon, StatChip, SurfaceCard } from '@/components/sentinel/primitives';
import { alertService, marketService, newsService, portfolioService } from '@/lib/api-service';
import type { AlertItem, LiveQuote, MarketSummary, NewsArticle, PortfolioGrowthPoint, PortfolioSummary } from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/sentinel-utils';

export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [market, setMarket] = useState<MarketSummary | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [growth, setGrowth] = useState<PortfolioGrowthPoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    Promise.allSettled([
      portfolioService.summary(),
      marketService.getLiveRibbon(),
      marketService.getMarketSummary(),
      newsService.global(3),
      portfolioService.growth('1d'),
      alertService.list(),
    ]).then(([summaryResult, ribbonResult, marketResult, newsResult, growthResult, alertsResult]) => {
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
      if (marketResult.status === 'fulfilled') setMarket(marketResult.value);
      if (newsResult.status === 'fulfilled') setNews(newsResult.value.articles.slice(0, 3));
      if (growthResult.status === 'fulfilled') setGrowth(growthResult.value);
      if (alertsResult.status === 'fulfilled') setAlerts(alertsResult.value);
    });
  }, []);

  const movers = market ? [...market.top_gainers.slice(0, 2), ...market.top_losers.slice(0, 1)] : [];

  return (
    <ProtectedScreen>
      <SentinelShell ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <section className="col-span-12 space-y-6 lg:col-span-8">
            <SurfaceCard className="relative overflow-hidden p-8 shadow-[0_30px_80px_rgba(0,0,0,0.24)]">
              <div className="absolute right-0 top-0 h-full w-1/2 bg-[linear-gradient(270deg,rgba(77,142,255,0.18),transparent)]" />
              <div className="relative z-10">
                <div className="mb-10 flex items-start justify-between gap-4">
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Portfolio Net Worth</p>
                    <h1 className="font-mono text-[62px] font-medium tracking-[-0.08em] text-white">
                      {formatCurrency(summary?.current_value ?? 0)}
                    </h1>
                  </div>
                  <div className="rounded-full bg-[rgba(78,222,163,0.12)] px-3 py-1 text-xs font-bold text-secondary">
                    {formatPercent(summary?.day_percent ?? 0)}
                  </div>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                  <StatChip label="Today's P&L" value={formatCurrency(summary?.day_pl ?? 0)} tone={(summary?.day_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
                  <StatChip label="Buying Power" value={formatCurrency(summary?.buying_power ?? 0)} />
                  <StatChip label="Total Return" value={formatPercent(summary?.percent_pl ?? 0)} tone={(summary?.percent_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
                </div>
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Market Overview</h2>
                  <p className="text-xs text-[var(--on-surface-variant)]">Live movement snapshot</p>
                </div>
                <div className="flex rounded-xl bg-[var(--surface-lowest)] p-1 text-xs font-bold">
                  {['1D', '1W', '1M', '1Y'].map((range, index) => (
                    <button key={range} className={index === 0 ? 'rounded-lg bg-[var(--surface-highest)] px-3 py-1 text-white' : 'px-3 py-1 text-[var(--on-surface-variant)]'}>
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl bg-[rgba(14,14,16,0.34)] p-4">
                <SentinelLineChart points={growth} accent="#adc6ff" compact />
              </div>
            </SurfaceCard>
          </section>

          <aside className="col-span-12 space-y-6 lg:col-span-4">
            <SurfaceCard className="p-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-white">Top Movers</h2>
                <Icon name="more_horiz" className="text-[18px] text-[var(--on-surface-variant)]" />
              </div>
              <div className="space-y-3">
                {movers.map((item) => (
                  <div key={item.symbol} className="flex items-center justify-between rounded-2xl px-2 py-2 hover:bg-[var(--surface-high)]">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--surface-high)] font-bold text-[var(--primary)]">
                        {item.symbol[0]}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white">{item.symbol}</p>
                        <p className="text-[10px] text-[var(--on-surface-variant)]">Live market mover</p>
                      </div>
                    </div>
                    <div className="text-right font-mono">
                      <p className="text-sm text-white">{formatCurrency(item.price)}</p>
                      <p className={item.change_percent >= 0 ? 'text-[10px] text-secondary' : 'text-[10px] text-tertiary'}>{formatPercent(item.change_percent)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-6">
              <h2 className="mb-5 text-sm font-bold uppercase tracking-[0.18em] text-white">Market News</h2>
              <div className="space-y-5">
                {news.map((article) => (
                  <a key={article.url} href={article.url} target="_blank" rel="noreferrer" className="block">
                    <p className="mb-1 text-[10px] font-black uppercase tracking-[0.22em] text-[var(--primary)]">{article.source}</p>
                    <h3 className="text-sm font-medium leading-6 text-white">{article.title}</h3>
                    <p className="mt-2 text-[10px] text-[var(--on-surface-variant)]">{article.published_at ?? 'Live feed'}</p>
                  </a>
                ))}
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-6">
              <h2 className="mb-4 text-sm font-bold text-white">Quick Execution</h2>
              <div className="mb-4 grid grid-cols-2 gap-2">
                <button className="rounded-xl border border-secondary/20 bg-secondary/10 py-2 text-xs font-black uppercase tracking-[0.22em] text-secondary">Buy</button>
                <button className="rounded-xl border border-tertiary/20 bg-tertiary/10 py-2 text-xs font-black uppercase tracking-[0.22em] text-tertiary">Sell</button>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3">
                  <p className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Asset</p>
                  <p className="font-mono text-white">{movers[0]?.symbol ?? 'NVDA'}</p>
                </div>
                <div className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3">
                  <p className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Quantity</p>
                  <p className="font-mono text-white">0.00</p>
                </div>
                <button className="w-full rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-4 py-4 text-sm font-black text-[var(--on-primary)]">
                  Review Order
                </button>
              </div>
              {alerts.length ? <p className="mt-4 text-[11px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">{alerts.filter((alert) => alert.is_active).length} active alerts online</p> : null}
            </SurfaceCard>
          </aside>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
