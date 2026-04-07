'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { indicatorService, marketService, newsService } from '@/lib/api-service';
import type { CombinedIndicators, HistoricalPoint, LiveQuote, NewsWithSentiment, StockDetails } from '@/lib/types';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

/* ─── Chart with optional indicator lines ─── */
function StockChart({
  data,
  indicators,
  activeIndicators,
}: {
  data: HistoricalPoint[];
  indicators: CombinedIndicators | null;
  activeIndicators: Set<string>;
}) {
  if (!data.length)
    return (
      <div className="flex h-[320px] items-center justify-center rounded-2xl bg-[var(--surface-lowest)]">
        <p className="text-sm text-[var(--on-surface-variant)]">No chart data available.</p>
      </div>
    );

  const closes = data.map((p) => p.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;

  const toX = (index: number) => (index / Math.max(closes.length - 1, 1)) * 1000;
  const toY = (value: number) => 300 - ((value - min) / span) * 260;

  const path = closes.map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i)},${toY(v)}`).join(' ');
  const area = `${path} L1000,320 L0,320 Z`;

  // indicator horizontal lines at their value
  const smaY = indicators?.sma?.sma != null ? toY(indicators.sma.sma) : null;
  const emaY = indicators?.ema?.ema != null ? toY(indicators.ema.ema) : null;
  // RSI is 0-100, map onto 0-320 vertical range (inverted: 100 → top, 0 → bottom)
  const rsiY = indicators?.rsi?.rsi != null ? 320 - (indicators.rsi.rsi / 100) * 280 : null;

  return (
    <svg className="h-[320px] w-full rounded-2xl bg-[rgba(12,22,28,0.65)]" preserveAspectRatio="none" viewBox="0 0 1000 320">
      <defs>
        <linearGradient id="chartGrad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#3ee0a0" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#3ee0a0" stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* grid lines */}
      {[0.2, 0.5, 0.8].map((r) => (
        <line key={r} x1="0" y1={320 * r} x2="1000" y2={320 * r} stroke="rgba(255,255,255,0.05)" strokeDasharray="6 10" />
      ))}
      {/* price area & line */}
      <path d={area} fill="url(#chartGrad)" />
      <path d={path} fill="none" stroke="#3ee0a0" strokeWidth="2.5" strokeLinecap="round" />
      {/* SMA */}
      {activeIndicators.has('SMA') && smaY !== null && (
        <line x1="0" y1={smaY} x2="1000" y2={smaY} stroke="#adc6ff" strokeWidth="1.5" strokeDasharray="8 6" />
      )}
      {/* EMA */}
      {activeIndicators.has('EMA') && emaY !== null && (
        <line x1="0" y1={emaY} x2="1000" y2={emaY} stroke="#ffb3ad" strokeWidth="1.5" strokeDasharray="8 6" />
      )}
      {/* RSI – shown as a horizontal threshold reference */}
      {activeIndicators.has('RSI') && rsiY !== null && (
        <line x1="0" y1={rsiY} x2="1000" y2={rsiY} stroke="#f9c74f" strokeWidth="1.5" strokeDasharray="4 8" />
      )}
    </svg>
  );
}

/* ─── Risk Gauge ─── */
function RiskGauge({ score }: { score: number }) {
  // score 0-1. Map 0→left(red), 0.5→mid(yellow), 1→right(green)
  const clamped = Math.max(0, Math.min(1, score));
  const angle = -90 + clamped * 180; // -90° (left) → +90° (right)

  const label = clamped >= 0.6 ? 'LOW' : clamped <= 0.4 ? 'HIGH' : 'MEDIUM';
  const color = clamped >= 0.6 ? '#4edea3' : clamped <= 0.4 ? '#ffb3ad' : '#f9c74f';

  // needle: pivot at (50,50), length ~38
  const rad = (angle * Math.PI) / 180;
  const nx = 50 + 38 * Math.cos(rad);
  const ny = 50 + 38 * Math.sin(rad);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 100 60" className="w-full max-w-[200px]">
        {/* arc background */}
        <path d="M 10,50 A 40,40 0 0,1 90,50" fill="none" stroke="#2a2a2c" strokeWidth="8" strokeLinecap="round" />
        {/* colored arc fill based on score */}
        <path
          d={`M 10,50 A 40,40 0 0,1 ${90 * clamped + 10 * (1 - clamped)},${50 - 40 * Math.sin(Math.PI * clamped)}`}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          opacity="0.7"
        />
        {/* needle */}
        <line x1="50" y1="50" x2={nx.toFixed(1)} y2={ny.toFixed(1)} stroke={color} strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="50" cy="50" r="3" fill={color} />
      </svg>
      <p className="mt-1 text-2xl font-black" style={{ color }}>{label}</p>
      <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">Risk Level</p>
    </div>
  );
}

/* ─── Sentiment badge colour ─── */
function sentimentColor(s?: string | null) {
  if (!s) return 'bg-[var(--surface-high)] text-[var(--on-surface-variant)]';
  const lower = s.toLowerCase();
  if (lower === 'positive' || lower === 'bullish') return 'bg-secondary/10 text-secondary';
  if (lower === 'negative' || lower === 'bearish') return 'bg-tertiary/10 text-tertiary';
  return 'bg-[var(--surface-high)] text-[var(--on-surface-variant)]';
}

/* ─── TIME RANGES ─── */
const TIME_RANGES = [
  { label: '1H', value: '1h' },
  { label: '1D', value: '1d' },
  { label: '1W', value: '1w' },
  { label: '1M', value: '1m' },
  { label: '1Y', value: '1y' },
] as const;

type TimeRange = (typeof TIME_RANGES)[number]['value'];

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = String(params.symbol ?? 'NVDA').toUpperCase();

  const [details, setDetails] = useState<StockDetails | null>(null);
  const [sentiment, setSentiment] = useState<NewsWithSentiment | null>(null);
  const [combined, setCombined] = useState<CombinedIndicators | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>('1y');
  const [activeIndicators, setActiveIndicators] = useState<Set<string>>(new Set());
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState('');

  // initial load: sentiment, indicators, ribbon
  useEffect(() => {
    Promise.allSettled([
      newsService.withSentiment(symbol, 4),
      indicatorService.combined(symbol),
      marketService.getLiveRibbon(),
    ]).then(([sentimentResult, indicatorsResult, ribbonResult]) => {
      if (sentimentResult.status === 'fulfilled') setSentiment(sentimentResult.value);
      if (indicatorsResult.status === 'fulfilled') setCombined(indicatorsResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks);
    });
  }, [symbol]);

  // re-fetch details whenever symbol or timeRange changes
  useEffect(() => {
    setLoadingDetails(true);
    setError('');
    marketService
      .getStockDetails(symbol, timeRange)
      .then((data) => { setDetails(data); })
      .catch(() => setError('Failed to load stock data. Please try again.'))
      .finally(() => setLoadingDetails(false));
  }, [symbol, timeRange]);

  function toggleIndicator(name: string) {
    setActiveIndicators((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }

  const riskScore = sentiment?.sentiment_analysis?.sentiment_score ?? 0.5;

  return (
    <ProtectedScreen>
      <SentinelShell ribbon={ribbon}>
        {error ? (
          <div className="flex min-h-[40vh] items-center justify-center">
            <div className="text-center">
              <p className="text-lg font-bold text-tertiary">{error}</p>
              <button
                onClick={() => { setTimeRange('1y'); }}
                className="mt-4 rounded-xl bg-[var(--surface-high)] px-4 py-2 text-sm text-white"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-12 gap-6">
            {/* ── LEFT: Chart section ── */}
            <section className="col-span-12 lg:col-span-8">
              <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h1 className="text-[44px] font-black tracking-[-0.08em] text-white leading-none">{symbol}</h1>
                  <p className="text-sm text-[var(--on-surface-variant)]">{symbol} live view</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-[40px] font-medium tracking-[-0.06em] text-white leading-none">
                    {loadingDetails ? '—' : formatCurrency(details?.current_price)}
                  </p>
                  <p className={(details?.day_change_percent ?? 0) >= 0 ? 'font-mono text-secondary' : 'font-mono text-tertiary'}>
                    {formatCurrency(details?.day_change)} {formatPercent(details?.day_change_percent)}
                  </p>
                </div>
              </div>

              <SurfaceCard className="p-4">
                {/* Range + Indicator controls */}
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  {/* Time Range */}
                  <div className="flex gap-1 rounded-xl bg-[var(--surface-lowest)] p-1">
                    {TIME_RANGES.map((r) => (
                      <button
                        key={r.value}
                        onClick={() => setTimeRange(r.value)}
                        className={
                          r.value === timeRange
                            ? 'rounded-lg bg-[var(--surface-highest)] px-3 py-1.5 text-xs font-black text-white'
                            : 'rounded-lg px-3 py-1.5 text-xs font-black text-[var(--on-surface-variant)] hover:text-white'
                        }
                      >
                        {r.label}
                      </button>
                    ))}
                  </div>
                  {/* Indicators */}
                  <div className="flex gap-2">
                    {['SMA', 'EMA', 'RSI'].map((ind) => (
                      <button
                        key={ind}
                        onClick={() => toggleIndicator(ind)}
                        className={
                          activeIndicators.has(ind)
                            ? 'rounded-xl bg-[var(--primary)]/20 border border-[var(--primary)]/40 px-3 py-1.5 text-xs font-black text-[var(--primary)]'
                            : 'rounded-xl bg-[var(--surface-high)] px-3 py-1.5 text-xs font-black text-[var(--on-surface-variant)] hover:text-white'
                        }
                      >
                        {ind}
                      </button>
                    ))}
                  </div>
                </div>

                {loadingDetails ? (
                  <div className="flex h-[320px] items-center justify-center rounded-2xl bg-[var(--surface-lowest)]">
                    <p className="text-sm text-[var(--on-surface-variant)]">Loading chart…</p>
                  </div>
                ) : (
                  <StockChart
                    data={details?.historical_data ?? []}
                    indicators={combined}
                    activeIndicators={activeIndicators}
                  />
                )}

                {/* Indicator legend */}
                {activeIndicators.size > 0 && (
                  <div className="mt-3 flex gap-4 text-[10px] font-black uppercase tracking-[0.15em]">
                    {activeIndicators.has('SMA') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#adc6ff]" />SMA {combined?.sma?.sma?.toFixed(2)}</span>}
                    {activeIndicators.has('EMA') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#ffb3ad]" />EMA {combined?.ema?.ema?.toFixed(2)}</span>}
                    {activeIndicators.has('RSI') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#f9c74f]" />RSI {combined?.rsi?.rsi?.toFixed(1)}</span>}
                  </div>
                )}
              </SurfaceCard>

              {/* News articles */}
              {sentiment?.articles && sentiment.articles.length > 0 && (
                <div className="mt-6 grid gap-4 md:grid-cols-2">
                  {sentiment.articles.map((article) => (
                    <SurfaceCard key={article.url} className="p-4">
                      <div className="mb-3 flex items-center justify-between gap-2">
                        <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.15em] ${sentimentColor(article.sentiment)}`}>
                          {article.sentiment ?? 'Neutral'}
                        </span>
                        <span className="text-[10px] text-[var(--on-surface-variant)]">{article.source}</span>
                      </div>
                      <a href={article.url} target="_blank" rel="noreferrer">
                        <p className="text-sm font-semibold text-white hover:text-[var(--primary)] transition-colors">{article.title}</p>
                      </a>
                      {article.summary && (
                        <p className="mt-2 text-xs leading-6 text-[var(--on-surface-variant)]">{article.summary}</p>
                      )}
                    </SurfaceCard>
                  ))}
                </div>
              )}
            </section>

            {/* ── RIGHT: Sidebar ── */}
            <aside className="col-span-12 space-y-6 lg:col-span-4">
              {/* Risk Gauge */}
              <SurfaceCard className="p-6 text-center">
                <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Sentinel AI Analysis</p>
                <RiskGauge score={riskScore} />
                <p className="mt-4 text-sm leading-7 text-[var(--on-surface-variant)]">
                  {sentiment?.sentiment_analysis?.recommendation ?? 'Live analysis pending.'}
                </p>
              </SurfaceCard>

              {/* Execution Panel */}
              <SurfaceCard className="p-6">
                <h3 className="mb-4 text-lg font-bold text-white">Execution Panel</h3>
                <div className="mb-4 grid grid-cols-2 gap-2">
                  <Link
                    href="/trade-history"
                    className="rounded-xl border border-secondary/30 bg-secondary/10 py-2 text-center text-sm font-bold text-secondary"
                  >
                    Buy
                  </Link>
                  <Link
                    href="/trade-history"
                    className="rounded-xl border border-tertiary/30 bg-tertiary/10 py-2 text-center text-sm font-bold text-tertiary"
                  >
                    Sell
                  </Link>
                </div>
                <p className="text-xs text-[var(--on-surface-variant)]">Use Quick Trade in the header for instant order placement.</p>
              </SurfaceCard>

              {/* Market Vital Signs */}
              <SurfaceCard className="p-6">
                <h3 className="mb-4 text-lg font-bold text-white">Market Vital Signs</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Market Cap</p>
                    <p className="font-mono text-white">{details?.market_cap ?? 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">P/E Ratio</p>
                    <p className="font-mono text-white">{details?.pe_ratio?.toFixed(2) ?? 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Day High</p>
                    <p className="font-mono text-secondary">{formatCurrency(details?.high)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Day Low</p>
                    <p className="font-mono text-tertiary">{formatCurrency(details?.low)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Open</p>
                    <p className="font-mono text-white">{formatCurrency(details?.open)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Volume</p>
                    <p className="font-mono text-white">{formatCompactNumber(details?.volume)}</p>
                  </div>
                  {combined && (
                    <>
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">SMA</p>
                        <p className="font-mono text-[#adc6ff]">{combined.sma?.sma?.toFixed(2) ?? 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">EMA</p>
                        <p className="font-mono text-[#ffb3ad]">{combined.ema?.ema?.toFixed(2) ?? 'N/A'}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">RSI</p>
                        <p className="font-mono text-[#f9c74f]">{combined.rsi?.rsi?.toFixed(1) ?? 'N/A'}</p>
                      </div>
                    </>
                  )}
                </div>
              </SurfaceCard>
            </aside>
          </div>
        )}
      </SentinelShell>
    </ProtectedScreen>
  );
}
