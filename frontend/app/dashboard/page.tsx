'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { QuickTradePanel } from '@/components/dashboard/QuickTradePanel';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { MetricCard, SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, marketService, newsService, portfolioService, tradeService } from '@/lib/api-service';
import { formatCompactNumber, formatCurrency, formatPercent, formatRelativeTime } from '@/lib/format';
import type { MarketSummary, NewsArticle, PortfolioSummary, StockDetails, TradeHistoryItem } from '@/lib/types';

const ranges = ['1d', '1w', '1m', '1y'] as const;

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [market, setMarket] = useState<MarketSummary | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [tradeHistory, setTradeHistory] = useState<TradeHistoryItem[]>([]);
  const [chartRange, setChartRange] = useState<(typeof ranges)[number]>('1m');
  const [chartData, setChartData] = useState<StockDetails | null>(null);
  const [chartLoading, setChartLoading] = useState(true);
  const [chartError, setChartError] = useState('');
  const [tradeOpen, setTradeOpen] = useState(false);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError('');
      const [summaryData, marketData, newsData, historyData] = await Promise.all([
        portfolioService.summary(),
        marketService.getMarketSummary(),
        newsService.global(6),
        tradeService.history(),
      ]);
      setSummary(summaryData);
      setMarket(marketData);
      setNews(newsData.articles);
      setTradeHistory(historyData.slice(0, 5));
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load dashboard data.'));
    } finally {
      setLoading(false);
    }
  };

  const loadChart = async () => {
    try {
      setChartLoading(true);
      setChartError('');
      const details = await marketService.getStockDetails('SPY', chartRange);
      setChartData(details);
    } catch (err) {
      setChartError(getErrorMessage(err, 'Unable to load market chart.'));
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  useEffect(() => {
    void loadChart();
  }, [chartRange]);

  useEffect(() => {
    if (searchParams.get('quickTrade') === '1') {
      setTradeOpen(true);
    }
  }, [searchParams]);

  const recentWinners = useMemo(
    () => tradeHistory.filter((item) => (item.profit_loss ?? 0) >= 0).slice(0, 3),
    [tradeHistory],
  );

  const recentLosers = useMemo(
    () => tradeHistory.filter((item) => (item.profit_loss ?? 0) < 0).slice(0, 3),
    [tradeHistory],
  );

  return (
    <ProtectedShell>
      <AppShell
        currentPage="dashboard"
        title="Dashboard"
        description="Live portfolio context, market movers, and execution tools tied directly to your backend."
        actions={(
          <>
            <Button variant="outline" onClick={() => void loadDashboard()}>
              Refresh
            </Button>
            <Button onClick={() => setTradeOpen(true)}>Quick Trade</Button>
          </>
        )}
      >
        {loading ? (
          <LoadingState label="Loading dashboard..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadDashboard()} />
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Portfolio Value"
                value={formatCurrency(summary?.current_value)}
                helper={`Invested ${formatCurrency(summary?.total_invested)}`}
                tone="primary"
              />
              <MetricCard
                label="Total P&L"
                value={formatCurrency(summary?.total_pl)}
                helper={formatPercent(summary?.percent_pl)}
                tone={(summary?.total_pl ?? 0) >= 0 ? 'positive' : 'negative'}
              />
              <MetricCard
                label="Market Status"
                value={market?.market_status?.toUpperCase() || 'UNKNOWN'}
                helper={`Updated ${market?.market_time ? formatRelativeTime(market.market_time) : 'just now'}`}
              />
              <MetricCard
                label="Closed Trades"
                value={String(tradeHistory.length)}
                helper={tradeHistory.length ? 'Recent execution history loaded' : 'No trades closed yet'}
              />
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.65fr_1fr]">
              <SurfaceCard className="space-y-6">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-on-surface-variant">Market Overview</p>
                    <h2 className="mt-2 text-2xl font-black text-white">SPY trend and live snapshot</h2>
                  </div>
                  <div className="flex gap-2 rounded-full bg-[#161518] p-1">
                    {ranges.map((range) => (
                      <button
                        key={range}
                        onClick={() => setChartRange(range)}
                        className={`rounded-full px-4 py-2 text-xs font-bold uppercase transition ${
                          chartRange === range ? 'bg-[#adc6ff] text-[#05214a]' : 'text-on-surface-variant hover:text-white'
                        }`}
                      >
                        {range}
                      </button>
                    ))}
                  </div>
                </div>
                {chartLoading ? (
                  <LoadingState label="Loading chart..." />
                ) : chartError ? (
                  <ErrorState message={chartError} onRetry={() => void loadChart()} />
                ) : chartData && chartData.historical_data.length > 0 ? (
                  <div className="space-y-5">
                    <div className="flex flex-wrap items-end justify-between gap-4">
                      <div>
                        <p className="text-3xl font-black text-white">{formatCurrency(chartData.current_price)}</p>
                        <p className={`mt-2 text-sm font-semibold ${chartData.day_change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                          {formatPercent(chartData.day_change_percent)} today
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm text-on-surface-variant md:grid-cols-4">
                        <div>
                          <p>Open</p>
                          <p className="mt-1 font-semibold text-white">{formatCurrency(chartData.open)}</p>
                        </div>
                        <div>
                          <p>High</p>
                          <p className="mt-1 font-semibold text-white">{formatCurrency(chartData.high)}</p>
                        </div>
                        <div>
                          <p>Low</p>
                          <p className="mt-1 font-semibold text-white">{formatCurrency(chartData.low)}</p>
                        </div>
                        <div>
                          <p>Volume</p>
                          <p className="mt-1 font-semibold text-white">{formatCompactNumber(chartData.volume)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="h-[320px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData.historical_data}>
                          <defs>
                            <linearGradient id="dashboardChart" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#4edea3" stopOpacity={0.35} />
                              <stop offset="100%" stopColor="#4edea3" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                          <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} stroke="#8f97ad" minTickGap={30} />
                          <YAxis stroke="#8f97ad" width={84} tickFormatter={(value) => `$${Number(value).toFixed(0)}`} />
                          <Tooltip
                            contentStyle={{ background: '#151518', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '16px' }}
                            formatter={(value: number) => [formatCurrency(value), 'Close']}
                            labelFormatter={(value) => new Date(value).toLocaleString()}
                          />
                          <Area type="monotone" dataKey="close" stroke="#4edea3" strokeWidth={3} fill="url(#dashboardChart)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <EmptyState title="No market history" message="Historical pricing is not available right now." />
                )}
              </SurfaceCard>

              <div className="space-y-6">
                <SurfaceCard>
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white">Top Gainers</h2>
                    <Link href="/stocks/NVDA" className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Explore
                    </Link>
                  </div>
                  <div className="mt-5 space-y-3">
                    {market?.top_gainers?.length ? market.top_gainers.slice(0, 5).map((stock) => (
                      <button
                        key={`gainer-${stock.symbol}`}
                        onClick={() => router.push(`/stocks/${stock.symbol}`)}
                        className="flex w-full items-center justify-between rounded-xl border border-white/5 bg-[#17161a] px-4 py-3 text-left transition hover:border-primary/30 hover:bg-white/5"
                      >
                        <div>
                          <p className="font-semibold text-white">{stock.symbol}</p>
                          <p className="text-xs text-on-surface-variant">Vol {formatCompactNumber(stock.volume)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-white">{formatCurrency(stock.price)}</p>
                          <p className="text-sm font-semibold text-secondary">{formatPercent(stock.change_percent)}</p>
                        </div>
                      </button>
                    )) : (
                      <EmptyState title="No gainers" message="Market mover data is unavailable." />
                    )}
                  </div>
                </SurfaceCard>

                <SurfaceCard>
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white">Trade Pulse</h2>
                    <Link href="/trade-history" className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Full history
                    </Link>
                  </div>
                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-secondary">Best recent</p>
                      <div className="mt-3 space-y-2">
                        {recentWinners.length ? recentWinners.map((trade) => (
                          <div key={`win-${trade.id}`} className="rounded-xl bg-[#17161a] px-4 py-3">
                            <p className="font-semibold text-white">{trade.symbol}</p>
                            <p className="text-sm text-secondary">{formatCurrency(trade.profit_loss)}</p>
                          </div>
                        )) : <p className="text-sm text-on-surface-variant">No winning trades yet.</p>}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tertiary">Needs review</p>
                      <div className="mt-3 space-y-2">
                        {recentLosers.length ? recentLosers.map((trade) => (
                          <div key={`loss-${trade.id}`} className="rounded-xl bg-[#17161a] px-4 py-3">
                            <p className="font-semibold text-white">{trade.symbol}</p>
                            <p className="text-sm text-tertiary">{formatCurrency(trade.profit_loss)}</p>
                          </div>
                        )) : <p className="text-sm text-on-surface-variant">No losing trades recorded.</p>}
                      </div>
                    </div>
                  </div>
                </SurfaceCard>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_1.1fr_0.9fr]">
              <SurfaceCard>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-white">Market Intelligence</h2>
                  <Link href="/news" className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                    View all
                  </Link>
                </div>
                <div className="mt-5 space-y-4">
                  {news.length ? news.map((article) => (
                    <a
                      key={article.url}
                      href={article.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-2xl border border-white/5 bg-[#17161a] p-4 transition hover:border-primary/30"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">{article.source}</p>
                        <p className="text-xs text-on-surface-variant">{formatRelativeTime(article.published_at)}</p>
                      </div>
                      <h3 className="mt-3 text-base font-semibold text-white">{article.title}</h3>
                      <p className="mt-2 text-sm text-on-surface-variant">{article.summary || 'Open the article for the full market brief.'}</p>
                    </a>
                  )) : (
                    <EmptyState title="No news yet" message="No market news is available right now." />
                  )}
                </div>
              </SurfaceCard>

              <SurfaceCard>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-white">Most Active</h2>
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                    Live
                  </span>
                </div>
                <div className="mt-5 space-y-3">
                  {market?.most_active?.length ? market.most_active.slice(0, 6).map((stock) => (
                    <button
                      key={`active-${stock.symbol}`}
                      onClick={() => router.push(`/stocks/${stock.symbol}`)}
                      className="grid w-full grid-cols-[1fr_auto_auto] items-center gap-4 rounded-xl border border-white/5 bg-[#17161a] px-4 py-3 text-left transition hover:border-primary/30"
                    >
                      <div>
                        <p className="font-semibold text-white">{stock.symbol}</p>
                        <p className="text-xs text-on-surface-variant">{stock.market_cap || 'Market cap unavailable'}</p>
                      </div>
                      <p className="text-sm font-semibold text-white">{formatCurrency(stock.price)}</p>
                      <p className={`text-sm font-semibold ${stock.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                        {formatPercent(stock.change_percent)}
                      </p>
                    </button>
                  )) : (
                    <EmptyState title="No active names" message="Most-active market data is currently unavailable." />
                  )}
                </div>
              </SurfaceCard>

              <SurfaceCard className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-white">Execution</h2>
                  <span className="text-xs text-on-surface-variant">Connected to backend</span>
                </div>
                <p className="text-sm text-on-surface-variant">
                  Place real trades, refresh your portfolio, and jump directly into detailed analysis without leaving the dashboard.
                </p>
                <Button
                  fullWidth
                  onClick={() => setTradeOpen(true)}
                >
                  Open Quick Trade
                </Button>
                <Button variant="outline" fullWidth onClick={() => router.push('/portfolio')}>
                  Review Portfolio
                </Button>
                <Button variant="ghost" fullWidth onClick={() => router.push('/watchlist')}>
                  Manage Watchlist
                </Button>
              </SurfaceCard>
            </div>
          </>
        )}
        <QuickTradePanel
          isOpen={tradeOpen}
          onClose={() => {
            setTradeOpen(false);
            if (searchParams.get('quickTrade') === '1') {
              router.replace('/dashboard');
            }
          }}
          onTradeCreated={async () => {
            await loadDashboard();
            showToast({
              title: 'Dashboard refreshed',
              description: 'Portfolio, history, and market context were updated after your trade.',
              variant: 'success',
            });
          }}
        />
      </AppShell>
    </ProtectedShell>
  );
}
