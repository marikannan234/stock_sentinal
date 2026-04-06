'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { indicatorService, marketService, newsService } from '@/lib/api-service';
import type { CombinedIndicators, LiveQuote, NewsWithSentiment, StockDetails } from '@/lib/types';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

function SimplePriceChart({ data }: { data: StockDetails['historical_data'] }) {
  if (!data.length) return <div className="h-[320px] rounded-2xl bg-[var(--surface-lowest)]" />;
  const closes = data.map((point) => point.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const path = closes.map((value, index) => {
    const x = (index / Math.max(closes.length - 1, 1)) * 1000;
    const y = 300 - ((value - min) / span) * 260;
    return `${index === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  return (
    <svg className="h-[320px] w-full rounded-2xl bg-[rgba(12,22,28,0.65)]" preserveAspectRatio="none" viewBox="0 0 1000 320">
      <path d={`${path} L1000,320 L0,320 Z`} fill="rgba(20,126,207,0.18)" />
      <path d={path} fill="none" stroke="#3ee0a0" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = String(params.symbol ?? 'NVDA').toUpperCase();
  const [details, setDetails] = useState<StockDetails | null>(null);
  const [sentiment, setSentiment] = useState<NewsWithSentiment | null>(null);
  const [combined, setCombined] = useState<CombinedIndicators | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([
      marketService.getStockDetails(symbol, '1y'),
      newsService.withSentiment(symbol, 2),
      indicatorService.combined(symbol),
      marketService.getLiveRibbon(),
    ]).then(([detailsResult, sentimentResult, indicatorsResult, ribbonResult]) => {
      if (detailsResult.status === 'fulfilled') setDetails(detailsResult.value);
      if (sentimentResult.status === 'fulfilled') setSentiment(sentimentResult.value);
      if (indicatorsResult.status === 'fulfilled') setCombined(indicatorsResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, [symbol]);

  const safetyLabel = useMemo(() => {
    const score = sentiment?.sentiment_analysis.sentiment_score ?? 0.5;
    if (score >= 0.6) return 'SAFE';
    if (score <= 0.4) return 'RISK';
    return 'HOLD';
  }, [sentiment]);

  return (
    <ProtectedScreen>
      <SentinelShell ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <section className="col-span-12 lg:col-span-8">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h1 className="text-[54px] font-black tracking-[-0.08em] text-white">{symbol}</h1>
                <p className="text-xl text-[var(--on-surface-variant)]">{symbol} live view</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-[58px] font-medium tracking-[-0.08em] text-white">{formatCurrency(details?.current_price)}</p>
                <p className={(details?.day_change_percent ?? 0) >= 0 ? 'font-mono text-secondary' : 'font-mono text-tertiary'}>{formatCurrency(details?.day_change)} {formatPercent(details?.day_change_percent)}</p>
              </div>
            </div>
            <SurfaceCard className="p-4">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex gap-2">
                  {['1H', '1D', '1W', '1M', '1Y'].map((item, index) => (
                    <button key={item} className={index === 4 ? 'rounded-xl bg-[var(--surface-highest)] px-4 py-2 text-xs font-black text-white' : 'rounded-xl bg-[var(--surface-lowest)] px-4 py-2 text-xs font-black text-[var(--on-surface-variant)]'}>
                      {item}
                    </button>
                  ))}
                </div>
                <div className="flex gap-2">
                  {['SMA', 'EMA', 'RSI'].map((item) => (
                    <button key={item} className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs font-black text-white">{item}</button>
                  ))}
                </div>
              </div>
              <SimplePriceChart data={details?.historical_data ?? []} />
            </SurfaceCard>
            <div className="mt-6 grid gap-6 md:grid-cols-2">
              {sentiment?.articles.map((article) => (
                <SurfaceCard key={article.url} className="p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="rounded-full bg-secondary/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-secondary">{article.sentiment ?? 'Neutral'}</span>
                    <span className="text-[10px] text-[var(--on-surface-variant)]">{article.source}</span>
                  </div>
                  <p className="text-sm font-semibold text-white">{article.title}</p>
                  <p className="mt-2 text-xs leading-6 text-[var(--on-surface-variant)]">{article.summary}</p>
                </SurfaceCard>
              ))}
            </div>
          </section>
          <aside className="col-span-12 space-y-6 lg:col-span-4">
            <SurfaceCard className="p-6 text-center">
              <div className="mx-auto mb-4 flex h-32 w-32 items-center justify-center rounded-full border-[10px] border-secondary/25">
                <span className="text-3xl font-black text-secondary">{safetyLabel}</span>
              </div>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Sentinel AI Analysis</p>
              <p className="text-sm leading-7 text-[var(--on-surface-variant)]">{sentiment?.sentiment_analysis.recommendation ?? 'Live analysis pending.'}</p>
            </SurfaceCard>
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-xl font-bold text-white">Execution Panel</h3>
              <div className="mb-4 grid grid-cols-2 gap-2">
                <button className="rounded-xl border border-[var(--primary)] py-2 text-sm font-bold text-white">Buy</button>
                <button className="rounded-xl bg-[var(--surface-lowest)] py-2 text-sm font-bold text-white">Sell</button>
              </div>
              <div className="rounded-xl bg-[var(--surface-lowest)] px-4 py-4">
                <p className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Quantity</p>
                <p className="font-mono text-white">1</p>
              </div>
              <Link href="/portfolio" className="mt-4 block rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-4 text-center text-sm font-bold text-[var(--on-primary)]">
                Confirm Transaction
              </Link>
            </SurfaceCard>
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-xl font-bold text-white">Market Vital Signs</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Market Cap</p><p className="font-mono text-white">{details?.market_cap ?? 'N/A'}</p></div>
                <div><p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">EMA</p><p className="font-mono text-white">{combined?.ema?.ema?.toFixed?.(2) ?? 'N/A'}</p></div>
                <div><p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">52W High</p><p className="font-mono text-secondary">{formatCurrency(details?.high)}</p></div>
                <div><p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">52W Low</p><p className="font-mono text-tertiary">{formatCurrency(details?.low)}</p></div>
                <div className="col-span-2"><p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Volume</p><p className="font-mono text-white">{formatCompactNumber(details?.volume)}</p></div>
              </div>
            </SurfaceCard>
          </aside>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
