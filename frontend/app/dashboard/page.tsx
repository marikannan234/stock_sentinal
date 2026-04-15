'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelLineChart } from '@/components/sentinel/charts';
import { SentinelShell } from '@/components/sentinel/shell';
import { Icon, StatChip, SurfaceCard, Skeleton } from '@/components/sentinel/primitives';
import { portfolioService } from '@/lib/api-service';
import { api } from '@/lib/api-client';
import { useMarketStore } from '@/lib/store-v2';
import type { LiveQuote, MarketSummary, NewsArticle, PortfolioGrowthPoint, PortfolioSummary } from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/sentinel-utils';

const dashRanges = ['1D', '1W', '1M', '1Y'] as const;
type DashRange = typeof dashRanges[number];
const rangeMap: Record<DashRange, '1d' | '1w' | '1m' | '1y'> = { '1D': '1d', '1W': '1w', '1M': '1m', '1Y': '1y' };

type RibbonResponse = {
  stocks?: LiveQuote[];
};

export default function DashboardPage() {
  const router = useRouter();
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [growth, setGrowth] = useState<PortfolioGrowthPoint[]>([]);
  const [activeRange, setActiveRange] = useState<DashRange>('1D');
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [growthLoading, setGrowthLoading] = useState(true);

  // Use global store for market data (no local polling needed - DataSyncProvider handles it)
  const market = useMarketStore((state) => state.market);
  const isMarketLoading = useMarketStore((state) => state.isMarketLoading);

  // 🚨 PREVENT API CALLS WITHOUT TOKEN
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('stocksentinel_token') : null;
    if (!token) {
      router.replace('/login');
      return;
    }
  }, [router]);

  // Load portfolio and news data once on mount
  useEffect(() => {
    let isMounted = true;

    // Don't load without token
    const token = typeof window !== 'undefined' ? localStorage.getItem('stocksentinel_token') : null;
    if (!token) return;

    const loadInitialData = async () => {
      if (!isMounted) return;

      try {
        // Portfolio load
        setPortfolioLoading(true);
        const portfolioData = await api.get<PortfolioSummary>('/dashboard/portfolio');
        if (isMounted) setPortfolio(portfolioData.data ?? null);
      } catch (error) {
        if (isMounted) {
          console.warn('Failed to fetch portfolio:', error);
          setPortfolio(null);
        }
      } finally {
        if (isMounted) setPortfolioLoading(false);
      }

      try {
        // News load
        setNewsLoading(true);
        const newsData = await api.get<NewsArticle[]>('/dashboard/news', { params: { limit: 3 } });
        if (isMounted) {
          setNews(Array.isArray(newsData.data) && newsData.data.length > 0 ? newsData.data.slice(0, 3) : []);
        }
      } catch (error) {
        if (isMounted) {
          console.warn('Failed to fetch news:', error);
          setNews([]);
        }
      } finally {
        if (isMounted) setNewsLoading(false);
      }
    };

    void loadInitialData();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setGrowthLoading(true);

    portfolioService
      .growth(rangeMap[activeRange])
      .then((points) => {
        if (!cancelled) {
          setGrowth(points);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setGrowth([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setGrowthLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeRange]);

  const handleRangeChange = useCallback((range: DashRange) => {
    setActiveRange(range);
  }, []);

  const movers = useMemo(() => {
    if (!market) return [];
    return [...(market.top_gainers ?? []).slice(0, 2), ...(market.top_losers ?? []).slice(0, 1)];
  }, [market]);

  const noMarketData = !isMarketLoading && !market;

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
                      {portfolioLoading ? <Skeleton className="h-12 w-48" /> : formatCurrency(portfolio?.current_value ?? 0)}
                    </h1>
                  </div>
                  <div className="rounded-full bg-[rgba(78,222,163,0.12)] px-3 py-1 text-xs font-bold text-secondary">
                    {portfolioLoading ? <Skeleton className="h-4 w-12" /> : formatPercent(portfolio?.day_percent ?? 0)}
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
                      <StatChip label="Today's P&L" value={formatCurrency(portfolio?.day_pl ?? 0)} tone={(portfolio?.day_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
                      <StatChip label="Buying Power" value={formatCurrency(portfolio?.buying_power ?? 0)} />
                      <StatChip label="Total Return" value={formatPercent(portfolio?.percent_pl ?? 0)} tone={(portfolio?.percent_pl ?? 0) >= 0 ? 'positive' : 'negative'} />
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
                      onClick={() => handleRangeChange(range)}
                      className={range === activeRange ? 'rounded-lg bg-[var(--surface-highest)] px-3 py-1 text-white' : 'px-3 py-1 text-[var(--on-surface-variant)] hover:text-white'}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl bg-[rgba(14,14,16,0.34)] p-4">
                {growthLoading ? (
                  <Skeleton className="h-32 w-full" />
                ) : growth.length > 0 ? (
                  <SentinelLineChart points={growth} accent="#adc6ff" compact />
                ) : (
                  <div className="flex h-32 items-center justify-center text-sm text-[var(--on-surface-variant)]">
                    No data available
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
                {isMarketLoading ? (
                  <>
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                  </>
                ) : movers.length === 0 ? (
                  <p className="text-xs text-[var(--on-surface-variant)]">{noMarketData ? 'No data available' : 'No market movers available'}</p>
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
                {newsLoading ? (
                  <>
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </>
                ) : news.length === 0 ? (
                  <p className="text-sm text-[var(--on-surface-variant)]">Unable to load news</p>
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
