'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState, useRef } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard, Skeleton } from '@/components/sentinel/primitives';
import { useStockDetailsQuery, useStockIndicatorsQuery, useStockSentimentQuery, useStockMLVolatilityQuery } from '@/hooks/queries/use-stock';
import type { HistoricalPoint } from '@/lib/types';
import { formatCompactNumber, formatCurrency, formatPercent } from '@/lib/sentinel-utils';

/* ─── Chart with optional indicator lines (No Flicker) ─── */
function StockChart({
  data,
  activeIndicators,
  chartType = 'line',
  onChartTypeChange,
}: {
  data: HistoricalPoint[];
  activeIndicators: Set<string>;
  chartType?: 'line' | 'candlestick';
  onChartTypeChange?: (type: 'line' | 'candlestick') => void;
}) {
  // Use useRef instead of useState to avoid re-renders on hover
  const hoveredIndexRef = useRef<number | null>(null);
  const [, forceUpdate] = useState(0);
  
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

  // Calculate indicator series from the same historical closes shown in this chart.
  // This avoids plotting a single latest indicator value as if it applied to every date.
  const smaSeries = closes.map((_, index) => {
    if (index < 19) return null;
    const window = closes.slice(index - 19, index + 1);
    return window.reduce((sum, value) => sum + value, 0) / window.length;
  });
  const emaSeries: number[] = [];
  const emaMultiplier = 2 / 13;
  closes.forEach((close, index) => {
    if (index === 0) emaSeries.push(close);
    else {
      const previous = emaSeries[index - 1] ?? close;
      emaSeries.push(close * emaMultiplier + previous * (1 - emaMultiplier));
    }
  });
  const rsiSeries: Array<number | null> = closes.map(() => null);
  if (closes.length > 14) {
    let averageGain = 0;
    let averageLoss = 0;
    for (let i = 1; i <= 14; i += 1) {
      const change = closes[i] - closes[i - 1];
      averageGain += Math.max(change, 0);
      averageLoss += Math.max(-change, 0);
    }
    averageGain /= 14;
    averageLoss /= 14;
    const calculateRsi = (gain: number, loss: number) =>
      loss === 0 ? (gain === 0 ? 50 : 100) : 100 - 100 / (1 + gain / loss);
    rsiSeries[14] = calculateRsi(averageGain, averageLoss);
    for (let i = 15; i < closes.length; i += 1) {
      const change = closes[i] - closes[i - 1];
      averageGain = (averageGain * 13 + Math.max(change, 0)) / 14;
      averageLoss = (averageLoss * 13 + Math.max(-change, 0)) / 14;
      rsiSeries[i] = calculateRsi(averageGain, averageLoss);
    }
  }
  const smaPath = smaSeries.map((value, index) => value == null ? '' : `${index === 0 || smaSeries[index - 1] == null ? 'M' : 'L'}${toX(index)},${toY(value)}`).filter(Boolean).join(' ');
  const emaPath = emaSeries.map((value, index) => `${index === 0 ? 'M' : 'L'}${toX(index)},${toY(value)}`).join(' ');
  const rsiPath = rsiSeries.map((value, index) => value == null ? '' : `${index === 14 || rsiSeries[index - 1] == null ? 'M' : 'L'}${toX(index)},${8 + ((100 - value) / 100) * 44}`).filter(Boolean).join(' ');
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

      {/* Keep a fixed-height tooltip slot so hover updates never move the chart. */}
      <div className="h-[76px] overflow-hidden rounded-xl border border-white/10 bg-[var(--surface-high)] px-4 py-3" aria-live="polite">
        {hoveredData ? (
          <div className="grid h-full grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Price</p>
              <p className="truncate font-mono text-lg text-white">{formatCurrency(hoveredData.close)}</p>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Time</p>
              <p className="truncate font-mono text-sm text-white">{hoveredData.timestamp}</p>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Change from start</p>
              <p className={`truncate font-mono text-lg ${(priceChangePercent ?? 0) >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                {priceChangePercent === null ? '—' : `${priceChangePercent >= 0 ? '+' : ''}${priceChangePercent.toFixed(2)}%`}
              </p>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase text-[var(--on-surface-variant)]">Volume</p>
              <p className="truncate font-mono text-sm text-white">{formatCompactNumber(hoveredData.volume)}</p>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center text-xs text-[var(--on-surface-variant)]">
            Hover over the chart to inspect a price point.
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

        {/* SMA 20 and EMA 12 are time-series overlays, not horizontal latest-value lines. */}
        {activeIndicators.has('SMA') && smaSeries.some((value) => value !== null) && (
          <path d={smaPath} fill="none" stroke="#adc6ff" strokeWidth="2" opacity="0.9" />
        )}
        {activeIndicators.has('EMA') && emaPath && (
          <path d={emaPath} fill="none" stroke="#ffb3ad" strokeWidth="2" opacity="0.9" />
        )}
      </svg>
      {activeIndicators.has('RSI') && (
        <div className="rounded-xl border border-white/5 bg-[rgba(12,22,28,0.65)] px-3 py-2">
          <div className="mb-1 flex items-center justify-between text-xs text-[var(--on-surface-variant)]">
            <span>RSI (14) · separate 0–100 scale</span>
            <span>{rsiSeries.at(-1) == null ? 'Not enough history' : `Latest ${(rsiSeries.at(-1) as number).toFixed(1)}`}</span>
          </div>
          <svg viewBox={`0 0 ${SVG_WIDTH} 60`} className="h-[76px] w-full" preserveAspectRatio="none" role="img" aria-label="Relative Strength Index over time, from 0 to 100">
            {[30, 50, 70].map((level) => {
              const y = 8 + ((100 - level) / 100) * 44;
              return <g key={level}><line x1={X_MARGIN} y1={y} x2={SVG_WIDTH - 20} y2={y} stroke="rgba(255,255,255,0.12)" strokeDasharray="4 5" /><text x={X_MARGIN - 10} y={y + 3} textAnchor="end" fontSize="10" fill="rgba(255,255,255,0.45)">{level}</text></g>;
            })}
            <path d={rsiPath} fill="none" stroke="#c4a7ff" strokeWidth="2.5" strokeLinejoin="round" />
          </svg>
          <p className="mt-1 text-[10px] text-[var(--on-surface-variant)]">Below 30 is commonly considered oversold; above 70 overbought. RSI is a momentum indicator, not a guarantee of reversals.</p>
        </div>
      )}
    </div>
  );
}

/* ─── Transparent historical risk snapshot (not an ML prediction) ─── */
function RiskGauge({ data }: { data: HistoricalPoint[] }) {
  const closes = data.map((point) => point.close).filter((price) => Number.isFinite(price) && price > 0);
  if (closes.length < 3) {
    return <p className="text-sm text-[var(--on-surface-variant)]">Not enough historical prices to estimate volatility and drawdown.</p>;
  }

  const returns = closes.slice(1).flatMap((price, index) => {
    const previous = closes[index];
    return previous > 0 ? [((price - previous) / previous) * 100] : [];
  });
  const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / returns.length;
  const volatilityPct = Math.sqrt(variance);
  let peak = closes[0];
  let maxDrawdownPct = 0;
  for (const price of closes) {
    peak = Math.max(peak, price);
    if (peak > 0) maxDrawdownPct = Math.max(maxDrawdownPct, ((peak - price) / peak) * 100);
  }

  // A simple, explainable heuristic score from the selected window's return volatility
  // and maximum peak-to-trough drawdown. It is not a probability or forecast.
  const riskScore = Math.round(Math.min(100, volatilityPct * 5 + maxDrawdownPct * 0.8));
  const riskLabel = riskScore < 30 ? 'LOW' : riskScore < 60 ? 'MODERATE' : 'HIGH';
  const riskColor = riskScore < 30 ? '#4edea3' : riskScore < 60 ? '#f9c74f' : '#ffb3ad';
  const needleAngle = -90 + (riskScore / 100) * 180;
  const rad = (needleAngle * Math.PI) / 180;
  const nx = 50 + 38 * Math.cos(rad);
  const ny = 58 + 38 * Math.sin(rad);

  return (
    <div className="flex flex-col items-center gap-3">
      <svg viewBox="0 0 100 70" className="w-full max-w-[220px]" role="img" aria-label={`Historical risk score ${riskScore} out of 100`}>
        <path d="M 12,58 A 38,38 0 0,1 88,58" fill="none" stroke="#2a2a2c" strokeWidth="8" strokeLinecap="round" />
        <path d={`M 12,58 A 38,38 0 0,1 ${50 + 38 * Math.cos(Math.PI - (riskScore / 100) * Math.PI)},${58 - 38 * Math.sin((riskScore / 100) * Math.PI)}`} fill="none" stroke={riskColor} strokeWidth="8" strokeLinecap="round" opacity="0.85" />
        <line x1="50" y1="58" x2={nx} y2={ny} stroke={riskColor} strokeWidth="3" strokeLinecap="round" />
        <circle cx="50" cy="58" r="4" fill={riskColor} />
        <text x="15" y="69" fontSize="8" fill="rgba(255,255,255,0.45)">LOW</text>
        <text x="50" y="69" fontSize="8" textAnchor="middle" fill="rgba(255,255,255,0.45)">MID</text>
        <text x="85" y="69" fontSize="8" textAnchor="end" fill="rgba(255,255,255,0.45)">HIGH</text>
      </svg>
      <div className="text-center">
        <p className="text-2xl font-black" style={{ color: riskColor }}>{riskLabel} · {riskScore}/100</p>
        <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--on-surface-variant)]">Historical risk heuristic</p>
      </div>
      <div className="grid w-full grid-cols-2 gap-3 text-left">
        <div className="rounded-xl bg-[var(--surface-lowest)] p-3">
          <p className="text-[10px] uppercase tracking-wide text-[var(--on-surface-variant)]">Return volatility</p>
          <p className="mt-1 font-mono text-white">{volatilityPct.toFixed(2)}%</p>
        </div>
        <div className="rounded-xl bg-[var(--surface-lowest)] p-3">
          <p className="text-[10px] uppercase tracking-wide text-[var(--on-surface-variant)]">Max drawdown</p>
          <p className="mt-1 font-mono text-white">-{maxDrawdownPct.toFixed(2)}%</p>
        </div>
      </div>
      <p className="text-xs leading-5 text-[var(--on-surface-variant)]">
        Based on price changes in the selected chart window. This is a transparent heuristic, not an ML model, loss probability, or investment recommendation.
      </p>
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
  const mlRiskQuery = useStockMLVolatilityQuery(symbol);
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
                    {activeIndicators.has('RSI') && <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-5 bg-[#c4a7ff]" />RSI {combined?.rsi?.rsi?.toFixed(1)}</span>}
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
              {/* Historical risk snapshot: volatility + drawdown, not RSI overbought/oversold. */}
              <SurfaceCard className="p-6 text-center">
                <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Market Risk Analysis</p>
                <RiskGauge data={details?.historical_data ?? []} />
                {sentiment?.sentiment_analysis?.recommendation && (
                  <p className="mt-4 text-sm leading-7 text-[var(--on-surface-variant)]">
                    {sentiment.sentiment_analysis.recommendation}
                  </p>
                )}
              </SurfaceCard>

              {/* Evaluated ML volatility estimate */}
              <SurfaceCard className="p-6">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-bold text-white">ML Volatility Outlook</h3>
                    <p className="mt-1 text-xs text-[var(--on-surface-variant)]">Next 5 trading sessions · Random Forest</p>
                  </div>
                  <span className="rounded-full border border-[var(--primary)]/30 bg-[var(--primary)]/10 px-2 py-1 text-[10px] font-bold uppercase text-[var(--primary)]">Beta</span>
                </div>
                {mlRiskQuery.isPending ? (
                  <div className="space-y-3" aria-label="Loading machine learning estimate">
                    <div className="h-8 w-32 animate-pulse rounded bg-[var(--surface-high)]" />
                    <div className="h-3 w-full animate-pulse rounded bg-[var(--surface-high)]" />
                    <div className="h-3 w-4/5 animate-pulse rounded bg-[var(--surface-high)]" />
                  </div>
                ) : mlRiskQuery.isError ? (
                  <div className="rounded-xl bg-[var(--surface-lowest)] p-3">
                    <p className="text-sm font-semibold text-white">Estimate unavailable</p>
                    <p className="mt-1 text-xs leading-5 text-[var(--on-surface-variant)]">
                      This model needs enough clean daily history. No prediction is shown when the data is insufficient.
                    </p>
                    <button onClick={() => mlRiskQuery.refetch()} className="mt-3 text-xs font-bold text-[var(--primary)]">Try again</button>
                  </div>
                ) : mlRiskQuery.data ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-3xl font-black text-white">{mlRiskQuery.data.predicted_volatility_percent.toFixed(2)}%</p>
                      <p className="mt-1 text-xs text-[var(--on-surface-variant)]">Estimated annualized volatility for the next 5 sessions</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-xl bg-[var(--surface-lowest)] p-3">
                        <p className="text-[10px] uppercase tracking-wide text-[var(--on-surface-variant)]">Model MAE</p>
                        <p className="mt-1 font-mono text-white">{mlRiskQuery.data.model_mae_percent.toFixed(2)} pp</p>
                      </div>
                      <div className="rounded-xl bg-[var(--surface-lowest)] p-3">
                        <p className="text-[10px] uppercase tracking-wide text-[var(--on-surface-variant)]">Baseline MAE</p>
                        <p className="mt-1 font-mono text-white">{mlRiskQuery.data.baseline_mae_percent.toFixed(2)} pp</p>
                      </div>
                    </div>
                    <p className={`text-xs font-semibold ${mlRiskQuery.data.model_beats_baseline ? 'text-secondary' : 'text-tertiary'}`}>
                      {mlRiskQuery.data.model_beats_baseline
                        ? 'Beat the simple baseline on the time-ordered holdout.'
                        : 'Did not beat the simple baseline on the holdout; treat this model as experimental.'}
                    </p>
                    <p className="text-xs leading-5 text-[var(--on-surface-variant)]">
                      Evaluated on {mlRiskQuery.data.holdout_observations} later observations · {mlRiskQuery.data.model_version}
                    </p>
                    <p className="text-[10px] leading-4 text-[var(--on-surface-variant)]">{mlRiskQuery.data.caveat}</p>
                  </div>
                ) : null}
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
