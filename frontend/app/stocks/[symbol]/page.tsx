'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
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
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { getErrorMessage, indicatorService, marketService, newsService } from '@/lib/api-service';
import { formatCompactNumber, formatCurrency, formatPercent, formatRelativeTime } from '@/lib/format';
import type { CombinedIndicators, NewsArticle, StockDetails } from '@/lib/types';

const ranges = ['1d', '1w', '1m', '1y'] as const;

export default function StockDetailsPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = String(params.symbol || 'AAPL').toUpperCase();
  const [range, setRange] = useState<(typeof ranges)[number]>('1m');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [details, setDetails] = useState<StockDetails | null>(null);
  const [combinedIndicators, setCombinedIndicators] = useState<CombinedIndicators | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);

  async function loadStock() {
    try {
      setLoading(true);
      setError('');
      const [detailData, indicatorData, newsData] = await Promise.all([
        marketService.getStockDetails(symbol, range),
        indicatorService.combined(symbol),
        newsService.bySymbol(symbol, 5),
      ]);
      setDetails(detailData);
      setCombinedIndicators(indicatorData);
      setNews(newsData.articles);
    } catch (err) {
      setError(getErrorMessage(err, `Unable to load ${symbol} details.`));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStock();
  }, [symbol, range]);

  return (
    <ProtectedShell>
      <AppShell
        currentPage="dashboard"
        title={`${symbol} Details`}
        description="Price action, historical charting, and technical indicators powered by your FastAPI backend."
        actions={(
          <>
            <Button variant="outline" asChild>
              <Link href="/dashboard">Back to Dashboard</Link>
            </Button>
            <Button onClick={() => void loadStock()}>Refresh</Button>
          </>
        )}
      >
        {loading ? (
          <LoadingState label={`Loading ${symbol}...`} />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadStock()} />
        ) : !details ? (
          <EmptyState title="No stock data" message="The selected stock did not return any details." />
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <SurfaceCard>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">Current Price</p>
                <p className="mt-4 text-3xl font-black text-white">{formatCurrency(details.current_price)}</p>
                <p className={`mt-2 text-sm font-semibold ${details.day_change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                  {formatPercent(details.day_change_percent)}
                </p>
              </SurfaceCard>
              <SurfaceCard>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">Day Range</p>
                <p className="mt-4 text-xl font-bold text-white">
                  {formatCurrency(details.low)} - {formatCurrency(details.high)}
                </p>
                <p className="mt-2 text-sm text-on-surface-variant">Open {formatCurrency(details.open)}</p>
              </SurfaceCard>
              <SurfaceCard>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">Volume</p>
                <p className="mt-4 text-3xl font-black text-white">{formatCompactNumber(details.volume)}</p>
                <p className="mt-2 text-sm text-on-surface-variant">{details.market_cap || 'Market cap unavailable'}</p>
              </SurfaceCard>
              <SurfaceCard>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">Valuation</p>
                <p className="mt-4 text-xl font-bold text-white">PE {details.pe_ratio?.toFixed(2) ?? 'N/A'}</p>
                <p className="mt-2 text-sm text-on-surface-variant">Dividend {details.dividend_yield?.toFixed(2) ?? '0.00'}%</p>
              </SurfaceCard>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
              <SurfaceCard className="space-y-6">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <h2 className="text-2xl font-black text-white">{symbol} Price History</h2>
                    <p className="mt-2 text-sm text-on-surface-variant">Range-aware historical chart using `/stocks/{symbol}`.</p>
                  </div>
                  <div className="flex gap-2 rounded-full bg-[#161518] p-1">
                    {ranges.map((value) => (
                      <button
                        key={value}
                        onClick={() => setRange(value)}
                        className={`rounded-full px-4 py-2 text-xs font-bold uppercase transition ${
                          range === value ? 'bg-[#adc6ff] text-[#05214a]' : 'text-on-surface-variant hover:text-white'
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
                {details.historical_data.length ? (
                  <div className="h-[360px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={details.historical_data}>
                        <defs>
                          <linearGradient id="stockHistory" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#adc6ff" stopOpacity={0.4} />
                            <stop offset="100%" stopColor="#adc6ff" stopOpacity={0} />
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
                        <Area dataKey="close" type="monotone" stroke="#adc6ff" strokeWidth={3} fill="url(#stockHistory)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <EmptyState title="No chart data" message="Historical prices are not available for the selected range." />
                )}
              </SurfaceCard>

              <SurfaceCard>
                <h2 className="text-xl font-bold text-white">Indicators</h2>
                <div className="mt-5 grid gap-3">
                  {[
                    ['SMA (14)', combinedIndicators?.sma.sma ?? details.indicators.sma_20],
                    ['EMA (20)', combinedIndicators?.ema.ema ?? details.indicators.ema_12],
                    ['RSI (14)', combinedIndicators?.rsi.rsi ?? details.indicators.rsi],
                    ['MACD', details.indicators.macd],
                    ['Bollinger Upper', details.indicators.bollinger_upper],
                    ['Bollinger Lower', details.indicators.bollinger_lower],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-center justify-between rounded-xl bg-[#17161a] px-4 py-3">
                      <span className="text-sm text-on-surface-variant">{label}</span>
                      <span className="text-sm font-semibold text-white">{typeof value === 'number' ? value.toFixed(2) : 'N/A'}</span>
                    </div>
                  ))}
                </div>
              </SurfaceCard>
            </div>

            <SurfaceCard>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">Latest News</h2>
                <Link href="/news" className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                  Full feed
                </Link>
              </div>
              <div className="mt-5 grid gap-4 lg:grid-cols-2">
                {news.length ? news.map((article) => (
                  <a
                    key={article.url}
                    href={article.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-2xl border border-white/5 bg-[#17161a] p-4 transition hover:border-primary/30"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">{article.source}</p>
                      <p className="text-xs text-on-surface-variant">{formatRelativeTime(article.published_at)}</p>
                    </div>
                    <h3 className="mt-3 text-base font-semibold text-white">{article.title}</h3>
                    <p className="mt-2 text-sm text-on-surface-variant">{article.summary || 'Open the article for details.'}</p>
                  </a>
                )) : (
                  <EmptyState title="No related headlines" message={`No news is available for ${symbol} right now.`} />
                )}
              </div>
            </SurfaceCard>
          </>
        )}
      </AppShell>
    </ProtectedShell>
  );
}
