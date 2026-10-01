'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelLineChart } from '@/components/sentinel/charts';
import { SentinelShell } from '@/components/sentinel/shell';
import { Icon, StatChip, SurfaceCard, Skeleton } from '@/components/sentinel/primitives';
import { useMarketSummaryQuery } from '@/hooks/queries/use-market';
import { useGlobalNewsQuery } from '@/hooks/queries/use-news';
import { usePortfolioGrowthQuery, usePortfolioSummaryQuery, type PortfolioRange } from '@/hooks/queries/use-portfolio';
import { formatCurrency, formatPercent } from '@/lib/sentinel-utils';

const dashRanges = ['1D', '1W', '1M', '1Y'] as const;
type DashRange = typeof dashRanges[number];
const rangeMap: Record<DashRange, PortfolioRange> = { '1D': '1d', '1W': '1w', '1M': '1m', '1Y': '1y' };

const DASHBOARD_NEWS_COUNT = 3;

/** Shows '—' instead of a fabricated $0.00 when the value could not be loaded. */
function orDash(value: number | undefined, format: (v: number) => string) {
  return value === undefined ? '—' : format(value);
}

export default function DashboardPage() {
  const [activeRange, setActiveRange] = useState<DashRange>('1D');

  const portfolioQuery = usePortfolioSummaryQuery();
  const growthQuery = usePortfolioGrowthQuery(rangeMap[activeRange]);
  const marketQuery = useMarketSummaryQuery();
  const newsQuery = useGlobalNewsQuery();

  const portfolio = portfolioQuery.data;
  const portfolioLoading = portfolioQuery.isPending;
  const growth = growthQuery.data ?? [];
  const news = useMemo(() => (newsQuery.data ?? []).slice(0, DASHBOARD_NEWS_COUNT), [newsQuery.data]);

  const market = marketQuery.data;
  const movers = useMemo(() => {
    if (!market) return [];
    return [...(market.top_gainers ?? []).slice(0, 2), ...(market.top_losers ?? []).slice(0, 1)];
  }, [market]);

  return (
    <ProtectedScreen>
      <SentinelShell>
        <div className="grid grid-cols-12 gap-6">
          <section className="col-span-12 space-y-6 lg:col-span-8">
            <SurfaceCard className="relative overflow-hidden p-8 shadow-[0_30px_80px_rgba(0,0,0,0.24)]">
              <div className="absolute right-0 top-0 h-full w-1/2 bg-[linear-gradient(270deg,rgba(77,142,255,0.18),transparent)]" />
              <div className="relative z-10">
                <div className="mb-10 flex items-start justify-between gap-4">
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Portfolio Net Worth</p>
                    <h1 className="font-mono text-[48px] font-medium tracking-[-0.07em] text-white">
                      {portfolioLoading ? <Skeleton className="h-12 w-48" /> : orDash(portfolio?.current_value, formatCurrency)}
                    </h1>
                    {portfolioQuery.isError && !portfolio ? (
                      <p className="mt-1 text-xs text-tertiary">Unable to load portfolio.</p>
                    ) : null}
                  </div>
                  <div className="rounded-full bg-[rgba(78,222,163,0.12)] px-3 py-1 text-xs font-bold text-secondary">
                    {portfolioLoading ? <Skeleton className="h-4 w-12" /> : orDash(portfolio?.day_percent, formatPercent)}
                  </div>
                </div>
                <div className="grid gap-6 md:grid-cols-3">
                  {portfolioLoading ? (
                    <>
                      <Skeleton className="h-20 w-full" />
                      <Skeleton className="h-20 w-full" />
                      <Skeleton className="h-20 w-full" />
                    </>
                  ) : (
                    <>
                      <StatChip label="Today's P&L" value={orDash(portfolio?.day_pl, formatCurrency)} tone={(portfolio?.day_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
                      <StatChip label="Buying Power" value={orDash(portfolio?.buying_power, formatCurrency)} />
                      <StatChip label="Total Return" value={orDash(portfolio?.percent_pl, formatPercent)} tone={(portfolio?.percent_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
                    </>
                  )}
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
                  {dashRanges.map((range) => (
                    <button
                      key={range}
                      onClick={() => setActiveRange(range)}
                      className={range === activeRange ? 'rounded-lg bg-[var(--surface-highest)] px-3 py-1 text-white' : 'px-3 py-1 text-[var(--on-surface-variant)] hover:text-white'}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl bg-[rgba(14,14,16,0.34)] p-4">
                {growthQuery.isPending ? (
                  <Skeleton className="h-32 w-full" />
                ) : growth.length > 0 ? (
                  <SentinelLineChart points={growth} accent="#adc6ff" compact />
                ) : (
                  <div className="flex h-32 items-center justify-center text-sm text-[var(--on-surface-variant)]">
                    {growthQuery.isError ? 'Unable to load chart data' : 'No data available'}
                  </div>
                )}
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
                {marketQuery.isPending ? (
                  <>
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                  </>
                ) : movers.length === 0 ? (
                  <p className="text-xs text-[var(--on-surface-variant)]">{marketQuery.isError && !market ? 'Market data unavailable' : 'No market movers available'}</p>
                ) : (
                  movers.map((item) => (
                    <Link key={item.symbol} href={`/stocks/${item.symbol}`} className="flex items-center justify-between rounded-2xl px-2 py-2 hover:bg-[var(--surface-high)] transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--surface-high)] text-sm font-bold text-[var(--primary)]">
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
                    </Link>
                  ))
                )}
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-6">
              <h2 className="mb-5 text-sm font-bold uppercase tracking-[0.18em] text-white">Market News</h2>
              <div className="space-y-5">
                {newsQuery.isPending ? (
                  <>
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </>
                ) : news.length === 0 ? (
                  <p className="text-sm text-[var(--on-surface-variant)]">{newsQuery.isError ? 'Unable to load news' : 'No news available'}</p>
                ) : (
                  news.map((article) => (
                    <a key={article.url} href={article.url} target="_blank" rel="noreferrer" className="block">
                      <p className="mb-1 text-[10px] font-black uppercase tracking-[0.22em] text-[var(--primary)]">{article.source}</p>
                      <h3 className="text-sm font-medium leading-6 text-white">{article.title}</h3>
                      <p className="mt-2 text-[10px] text-[var(--on-surface-variant)]">{article.published_at ?? 'Live feed'}</p>
                    </a>
                  ))
                )}
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-6">
              <h2 className="mb-4 text-sm font-bold text-white">Quick Links</h2>
              <div className="space-y-2">
                <Link href="/portfolio" className="flex items-center gap-3 rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm font-medium text-white hover:bg-[var(--surface-high)] transition-colors">
                  <Icon name="pie_chart" className="text-[18px] text-[var(--primary)]" />
                  Portfolio
                </Link>
                <Link href="/alerts" className="flex items-center gap-3 rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm font-medium text-white hover:bg-[var(--surface-high)] transition-colors">
                  <Icon name="notifications_active" className="text-[18px] text-[var(--primary)]" />
                  Manage Alerts
                </Link>
                <Link href="/news" className="flex items-center gap-3 rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm font-medium text-white hover:bg-[var(--surface-high)] transition-colors">
                  <Icon name="article" className="text-[18px] text-[var(--primary)]" />
                  News Feed
                </Link>
                <Link href="/trade-history" className="flex items-center gap-3 rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm font-medium text-white hover:bg-[var(--surface-high)] transition-colors">
                  <Icon name="history" className="text-[18px] text-[var(--primary)]" />
                  Trade History
                </Link>
              </div>
            </SurfaceCard>
          </aside>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
