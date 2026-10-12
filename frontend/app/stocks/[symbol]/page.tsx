'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState, useRef } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard, Skeleton } from '@/components/sentinel/primitives';
import { useStockDetailsQuery, useStockIndicatorsQuery, useStockSentimentQuery } from '@/hooks/queries/use-stock';
import type { CombinedIndicators, HistoricalPoint } from '@/lib/types';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

/* ─── Chart with optional indicator lines (No Flicker) ─── */
function StockChart({
  data,
  indicators,
  activeIndicators,
  chartType = 'line',
  onChartTypeChange,
}: {
  data: HistoricalPoint[];
  indicators: CombinedIndicators | null;
  activeIndicators: Set<string>;
  chartType?: 'line' | 'candlestick';
  onChartTypeChange?: (type: 'line' | 'candlestick') => void;
}) {
  // Use useRef instead of useState to avoid re-renders on hover
  const hoveredIndexRef = useRef<number | null>(null);
  const [, forceUpdate] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  if (!data.length)
    return (
      <div className="flex h-[320px] items-center justify-center rounded-2xl bg-[var(--surface-lowest)]">
        <p className="text-sm text-[var(--on-surface-variant)]">No chart data available.</p>
      </div>
    );

  const closes = data.map((p) => p.close);
  const highs = data.map((p) => p.high || p.close);
  const lows = data.map((p) => p.low || p.close);
  
  const minPrice = Math.min(...lows);
  const maxPrice = Math.max(...highs);
  const priceSpan = maxPrice - minPrice || 1;
  
  // SVG dimensions
  const X_MARGIN = 60;
  const Y_MARGIN = 40;
  const SVG_WIDTH = 1000;
  const SVG_HEIGHT = 320;
  const CHART_WIDTH = SVG_WIDTH - X_MARGIN - 20;
  const CHART_HEIGHT = SVG_HEIGHT - Y_MARGIN - 20;

  const toX = (index: number) => X_MARGIN + (index / Math.max(data.length - 1, 1)) * CHART_WIDTH;
  const toY = (value: number) => Y_MARGIN + ((maxPrice - value) / priceSpan) * CHART_HEIGHT;

  // For line chart
  const path = closes.map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i)},${toY(v)}`).join(' ');
  const area = `${path} L${toX(data.length - 1)},${Y_MARGIN + CHART_HEIGHT} L${X_MARGIN},${Y_MARGIN + CHART_HEIGHT} Z`;

  // Indicator values
  const smaY = indicators?.sma?.sma != null ? toY(indicators.sma.sma) : null;
  const emaY = indicators?.ema?.ema != null ? toY(indicators.ema.ema) : null;
  const rsiY = indicators?.rsi?.rsi != null ? Y_MARGIN + ((100 - indicators.rsi.rsi) / 100) * CHART_HEIGHT : null;

  // Get hovered candle data
  const hoveredIndex = hoveredIndexRef.current;
  const hoveredData = hoveredIndex != null && data[hoveredIndex] ? data[hoveredIndex] : null;
  const priceChange = hoveredData && data[0] ? hoveredData.close - data[0].close : null;
  const priceChangePercent = hoveredData && data[0] ? ((hoveredData.close - data[0].close) / data[0].close) * 100 : null;

  // Debounced hover handler to prevent flicker
  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * SVG_WIDTH;
    
    // Only calc index if within chart area
    if (x >= X_MARGIN && x <= SVG_WIDTH - 20) {
      const newIndex = Math.round(((x - X_MARGIN) / CHART_WIDTH) * (data.length - 1));
      const clamped = Math.max(0, Math.min(data.length - 1, newIndex));
      
      // Only force update if index changed
      if (clamped !== hoveredIndexRef.current) {
        hoveredIndexRef.current = clamped;
        forceUpdate(p => p + 1);
      }
    }
  }

  function handleMouseLeave() {
    if (hoveredIndexRef.current !== null) {
      hoveredIndexRef.current = null;
      forceUpdate(p => p + 1);
    }
  }

  return (
    <div className="space-y-4">
      {/* Chart Type Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => onChartTypeChange?.('line')}
          className={`px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
            chartType === 'line'
              ? 'bg-[var(--primary)]/20 text-[var(--primary)]'
              : 'bg-[var(--surface-high)] text-[var(--on-surface-variant)] hover:text-white'
          }`}
        >
          Line
        </button>
        <button
          onClick={() => onChartTypeChange?.('candlestick')}
          className={`px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
            chartType === 'candlestick'
              ? 'bg-[var(--primary)]/20 text-[var(--primary)]'
              : 'bg-[var(--surface-high)] text-[var(--on-surface-variant)] hover:text-white'
          }`}
        >
          Candlestick
        </button>
      </div>

      {/* Fixed-height details slot prevents the chart moving when the crosshair changes. */}
      <div
        className="min-h-[76px] rounded-xl border border-white/10 bg-[var(--surface-high)] px-4 py-3"
        aria-live="polite"
        aria-label={hoveredData ? "Selected chart point details" : "Move over the chart to inspect a point"}
      >
        {hoveredData ? (
          <div className="flex min-h-[48px] items-center justify-between gap-4 overflow-x-auto">
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Price</p>
              <p className="font-mono text-lg text-white">{formatCurrency(hoveredData.close)}</p>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Time</p>
              <p className="font-mono text-sm text-white">{hoveredData.timestamp}</p>
            </div>
            {priceChange !== null && priceChangePercent !== null && (
              <div className="min-w-0">
                <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Change</p>
                <p className={`font-mono text-lg ${priceChangePercent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                  {priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
                </p>
              </div>
            )}
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Volume</p>
              <p className="font-mono text-sm text-white">{formatCompactNumber(hoveredData.volume)}</p>
            </div>
          </div>
        ) : (
          <div className="flex min-h-[48px] items-center text-sm text-[var(--on-surface-variant)]">
            Move over the chart to inspect price, date, change and volume.
          </div>
        )}
      </div>

      <svg 
        className="h-[320px] w-full rounded-2xl bg-[rgba(12,22,28,0.65)] cursor-crosshair border border-white/5" 
        preserveAspectRatio="none" 
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          <linearGradient id="chartGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#3ee0a0" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#3ee0a0" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Y-Axis */}
        <line x1={X_MARGIN - 1} y1={Y_MARGIN} x2={X_MARGIN - 1} y2={Y_MARGIN + CHART_HEIGHT} stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
        
        {/* X-Axis */}
        <line x1={X_MARGIN} y1={Y_MARGIN + CHART_HEIGHT + 1} x2={SVG_WIDTH - 20} y2={Y_MARGIN + CHART_HEIGHT + 1} stroke="rgba(255,255,255,0.1)" strokeWidth="1" />

        {/* Y-Axis Price Labels and Grid Lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = Y_MARGIN + ratio * CHART_HEIGHT;
          const price = maxPrice - ratio * priceSpan;
          return (
            <g key={`y-${ratio}`}>
              <line x1={X_MARGIN - 5} y1={y} x2={SVG_WIDTH - 20} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="1" strokeDasharray="4 8" />
              <text x={X_MARGIN - 12} y={y + 3} textAnchor="end" fontSize="10" fill="rgba(255,255,255,0.4)" fontFamily="monospace">
                {formatCurrency(price)}
              </text>
            </g>
          );
        })}

        {/* X-Axis Time Labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const index = Math.floor(ratio * (data.length - 1));
          const x = toX(index);
          const date = new Date(data[index].timestamp);
          const timeStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          return (
            <text key={`x-${ratio}`} x={x} y={Y_MARGIN + CHART_HEIGHT + 18} textAnchor="middle" fontSize="10" fill="rgba(255,255,255,0.4)" fontFamily="monospace">
              {timeStr}
            </text>
          );
        })}

        {/* Min/Max price indicators */}
        <text x={SVG_WIDTH - 18} y={Y_MARGIN - 5} textAnchor="end" fontSize="9" fill="rgba(76,237,163,0.6)" fontFamily="monospace" fontWeight="bold">
          {formatCurrency(maxPrice)}
        </text>
        <text x={SVG_WIDTH - 18} y={Y_MARGIN + CHART_HEIGHT + 15} textAnchor="end" fontSize="9" fill="rgba(255,179,173,0.6)" fontFamily="monospace" fontWeight="bold">
          {formatCurrency(minPrice)}
        </text>

        {chartType === 'candlestick' ? (
          <>
            {/* Candlestick rendering */}
            {data.map((point, index) => {
              const x = toX(index);
              const open = point.open || point.close;
              const close = point.close;
              const high = point.high || Math.max(open, close);
              const low = point.low || Math.min(open, close);

              const yOpen = toY(open);
              const yClose = toY(close);
              const yHigh = toY(high);
              const yLow = toY(low);

              const isUp = close >= open;
              const color = isUp ? '#4edea3' : '#ffb3ad';
              const wickWidth = 0.8;
              const bodyWidth = 6;

              return (
                <g key={`candle-${index}`}>
                  {/* Wick (high-low line) */}
                  <line
                    x1={x}
                    y1={yHigh}
                    x2={x}
                    y2={yLow}
                    stroke={color}
                    strokeWidth={wickWidth}
                    opacity={hoveredIndex === index ? '1' : '0.6'}
                  />
                  {/* Body (open-close rectangle) */}
                  <rect
                    x={x - bodyWidth / 2}
                    y={Math.min(yOpen, yClose)}
                    width={bodyWidth}
                    height={Math.max(Math.abs(yClose - yOpen), 1)}
                    fill={color}
                    opacity={hoveredIndex === index ? 1 : isUp ? 0.8 : 0.7}
                  />
                  {/* Hover highlight */}
                  {hoveredIndex === index && (
                    <circle cx={x} cy={toY(close)} r="3" fill={color} opacity="0.5" />
                  )}
                </g>
              );
            })}
          </>
        ) : (
          <>
            {/* Line chart rendering */}
            <path d={area} fill="url(#chartGrad)" />
            <path d={path} fill="none" stroke="#3ee0a0" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            {/* Hover indicator */}
            {hoveredIndex !== null && (
              <circle cx={toX(hoveredIndex)} cy={toY(closes[hoveredIndex])} r="3.5" fill="#3ee0a0" opacity="0.8" />
            )}
          </>
        )}

        {/* SMA – Blue line */}
        {activeIndicators.has('SMA') && smaY !== null && (
          <line x1={X_MARGIN} y1={smaY} x2={SVG_WIDTH - 20} y2={smaY} stroke="#adc6ff" strokeWidth="2" strokeDasharray="8 6" opacity="0.8" />
        )}
        
        {/* EMA – Orange line */}
        {activeIndicators.has('EMA') && emaY !== null && (
          <line x1={X_MARGIN} y1={emaY} x2={SVG_WIDTH - 20} y2={emaY} stroke="#ffb3ad" strokeWidth="2" strokeDasharray="8 6" opacity="0.8" />
        )}
        
        {/* RSI – Purple line (inverted: 0 at bottom, 100 at top) */}
        {activeIndicators.has('RSI') && rsiY !== null && (
          <line x1={X_MARGIN} y1={rsiY} x2={SVG_WIDTH - 20} y2={rsiY} stroke="#f9c74f" strokeWidth="2" strokeDasharray="4 8" opacity="0.8" />
        )}
      </svg>
    </div>
  );
}

/* ─── Historical volatility risk gauge ─── */
function RiskGauge({ data }: { data: HistoricalPoint[] }) {
  // Estimate annualized volatility from the observed close-to-close returns.
  // Normalize by elapsed calendar time so weekly/monthly chart ranges do not
  // get treated as if every bar represented one trading day.
  const observations = data
    .filter((point) => Number.isFinite(point.close) && point.close > 0 && Number.isFinite(Date.parse(point.timestamp)))
    .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));

  const returns: number[] = [];
  const intervals: number[] = [];
  for (let index = 1; index < observations.length; index += 1) {
    const previous = observations[index - 1];
    const current = observations[index];
    const elapsedDays = (Date.parse(current.timestamp) - Date.parse(previous.timestamp)) / 86400000;
    if (elapsedDays <= 0) continue;
    returns.push(Math.log(current.close / previous.close));
    intervals.push(elapsedDays);
  }

  if (returns.length < 5) {
    return (
      <div className="flex min-h-[180px] flex-col items-center justify-center text-center">
        <p className="text-lg font-black text-[var(--on-surface-variant)]">Not enough data</p>
        <p className="mt-2 max-w-[220px] text-xs text-[var(--on-surface-variant)]">
          At least six valid closing prices are needed to estimate historical volatility.
        </p>
      </div>
    );
  }

  const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (returns.length - 1);
  const averageIntervalDays = intervals.reduce((sum, value) => sum + value, 0) / intervals.length;
  const annualizedVolatility = Math.sqrt(Math.max(variance, 0)) * Math.sqrt(252 / Math.max(averageIntervalDays, 1));
  const volatilityPercent = annualizedVolatility * 100;
  const riskPercent = Math.max(0, Math.min(100, (volatilityPercent / 80) * 100));

  const riskLabel = volatilityPercent < 20 ? "LOW" : volatilityPercent < 40 ? "MODERATE" : "HIGH";
  const riskColor = volatilityPercent < 20 ? "#4edea3" : volatilityPercent < 40 ? "#f9c74f" : "#ffb3ad";
  const needleAngle = -90 + (riskPercent / 100) * 180;
  const rad = (needleAngle * Math.PI) / 180;
  const centerX = 50;
  const centerY = 58;
  const needleLength = 34;
  const nx = centerX + needleLength * Math.cos(rad);
  const ny = centerY + needleLength * Math.sin(rad);
  const arcEndAngle = Math.PI - (riskPercent / 100) * Math.PI;
  const arcX = centerX + 38 * Math.cos(arcEndAngle);
  const arcY = centerY - 38 * Math.sin(arcEndAngle);
  const largeArc = riskPercent > 50 ? 1 : 0;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 100 70" className="w-full max-w-[220px]" role="img" aria-label={`Estimated annualized volatility ${volatilityPercent.toFixed(1)} percent, ${riskLabel} risk`}>
        <path d="M 12,58 A 38,38 0 0,1 88,58" fill="none" stroke="#2a2a2c" strokeWidth="8" strokeLinecap="round" />
        {riskPercent > 0 && (
          <path d={`M 12,58 A 38,38 0 ${largeArc} 1 ${arcX},${arcY}`} fill="none" stroke={riskColor} strokeWidth="8" strokeLinecap="round" opacity="0.9" />
        )}
        <line x1={centerX} y1={centerY} x2={nx} y2={ny} stroke={riskColor} strokeWidth="3" strokeLinecap="round" />
        <circle cx={centerX} cy={centerY} r="4" fill={riskColor} />
        <text x="12" y="69" fontSize="8" fill="rgba(255,255,255,0.45)">0%</text>
        <text x="88" y="69" fontSize="8" textAnchor="end" fill="rgba(255,255,255,0.45)">80%+</text>
      </svg>
      <div className="text-center">
        <p className="text-2xl font-black" style={{ color: riskColor }}>{riskLabel}</p>
        <p className="text-xs text-[var(--on-surface-variant)]">
          Estimated annualized volatility: {volatilityPercent.toFixed(1)}%
        </p>
        <p className="mt-1 max-w-[260px] text-[10px] leading-relaxed text-[var(--on-surface-variant)]">
          Based on historical close-to-close returns, not a prediction of future loss. Low: under 20%; moderate: 20–40%; high: 40% or more.
        </p>
      </div>
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
  const symbol = (String(params.symbol ?? 'NVDA') || "NVDA").toUpperCase();

  const [timeRange, setTimeRange] = useState<TimeRange>('1y');
  const [chartType, setChartType] = useState<'line' | 'candlestick'>('line');
  const [activeIndicators, setActiveIndicators] = useState<Set<string>>(new Set());

  // Keyed by symbol (and range), so data from a previous symbol is never shown.
  const detailsQuery = useStockDetailsQuery(symbol, timeRange);
  const details = detailsQuery.data;
  const combined = useStockIndicatorsQuery(symbol).data ?? null;
  const sentiment = useStockSentimentQuery(symbol).data;
  const loadingDetails = detailsQuery.isPending;
  const error = detailsQuery.isError ? 'Failed to load stock data. Please try again.' : '';

  function toggleIndicator(name: string) {
    setActiveIndicators((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }

  return (
    <ProtectedScreen>
      <SentinelShell>
        {error ? (
          <div className="flex min-h-[40vh] items-center justify-center">
            <div className="text-center">
              <p className="text-lg font-bold text-tertiary">{error}</p>
              <button
                onClick={() => detailsQuery.refetch()}
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
                  <p className="text-sm text-[var(--on-surface-variant)]">
                    {details?.source ?? 'Market data'} · {details?.quote_type === 'daily_bar' || details?.quote_type === 'daily_close' ? 'Daily bar · may be delayed' : 'Provider quote'}
                    {details?.price_as_of ? ` · Data as of ${new Date(details.price_as_of).toLocaleString()}` : ''}
                  </p>
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
                  <div className="flex h-80 items-center justify-center rounded-2xl bg-[var(--surface-lowest)] min-h-[320px]">
                    <div className="flex flex-col items-center gap-2">
                      <div className="relative inline-flex">
                        <div className="animate-spin">
                          <div className="h-8 w-8 rounded-full border-4 border-[var(--surface-high)] border-t-[var(--primary)]" />
                        </div>
                      </div>
                      <p className="text-sm text-[var(--on-surface-variant)]">Loading chart...</p>
                    </div>
                  </div>
                ) : (
                  <StockChart
                    data={details?.historical_data ?? []}
                    indicators={combined}
                    activeIndicators={activeIndicators}
                    chartType={chartType}
                    onChartTypeChange={setChartType}
                  />
                )}

                {/* Indicator legend */}
                {activeIndicators.size > 0 && (
                  <div className="mt-3 flex gap-4 text-[10px] font-black uppercase tracking-[0.15em] animate-fadeIn transition-all duration-300">
                    {activeIndicators.has('SMA') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#adc6ff]" />SMA {combined?.sma?.sma?.toFixed(2)}</span>}
                    {activeIndicators.has('EMA') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#ffb3ad]" />EMA {combined?.ema?.ema?.toFixed(2)}</span>}
                    {activeIndicators.has('RSI') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#f9c74f]" />RSI {combined?.rsi?.rsi?.toFixed(1)}</span>}
                  </div>
                )}
              </SurfaceCard>

              {/* News articles */}
              {sentiment?.articles && sentiment.articles.length > 0 && (
                <div className="mt-6 grid gap-4 md:grid-cols-2 animate-fadeIn transition-all duration-300">
                  {sentiment.articles.map((article) => (
                    <a key={article.url} href={article.url} target="_blank" rel="noreferrer" className="group">
                      <SurfaceCard className="h-full overflow-hidden p-0 transition-all duration-300 hover:border-white/30 hover:shadow-xl hover:-translate-y-1">
                        {/* Image Thumbnail */}
                        {article.image && (
                          <div className="relative h-40 bg-[var(--surface-lowest)] overflow-hidden">
                            <img
                              src={article.image}
                              alt={article.title}
                              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          </div>
                        )}
                        
                        <div className="p-4 space-y-3">
                          <div className="flex items-center justify-between gap-2">
                            <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.15em] ${sentimentColor(article.sentiment)}`}>
                              {article.sentiment ?? 'Neutral'}
                            </span>
                            <span className="text-[10px] text-[var(--on-surface-variant)]">{article.source}</span>
                          </div>
                          
                          <p className="text-sm font-semibold text-white group-hover:text-[var(--primary)] transition-colors line-clamp-2">{article.title}</p>
                          
                          {article.summary && (
                            <p className="text-xs leading-5 text-[var(--on-surface-variant)] line-clamp-2">{article.summary}</p>
                          )}
                          
                          {article.published_at && (
                            <p className="text-[10px] text-[var(--on-surface-variant)]">
                              {new Date(article.published_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </p>
                          )}
                        </div>
                      </SurfaceCard>
                    </a>
                  ))}
                </div>
              )}
            </section>

            {/* ── RIGHT: Sidebar ── */}
            <aside className="col-span-12 space-y-6 lg:col-span-4">
              {/* Risk Gauge (RSI-based) */}
              <SurfaceCard className="p-6 text-center">
                <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Market Risk Analysis</p>
                <RiskGauge data={details?.historical_data ?? []} />
                {sentiment?.sentiment_analysis?.recommendation && (
                  <p className="mt-4 text-sm leading-7 text-[var(--on-surface-variant)]">
                    {sentiment.sentiment_analysis.recommendation}
                  </p>
                )}
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
