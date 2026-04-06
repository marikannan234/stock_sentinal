'use client';

import { PortfolioAllocation, PortfolioGrowthPoint } from '@/lib/types';
import { cn, formatCurrency } from '@/lib/sentinel-utils';

const palette = ['#adc6ff', '#4edea3', '#ffb3ad', '#8c909f'];

function buildPath(points: PortfolioGrowthPoint[], width: number, height: number) {
  if (!points.length) return '';
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - ((point.value - min) / span) * (height - 20) - 10;
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
}

function buildArea(points: PortfolioGrowthPoint[], width: number, height: number) {
  if (!points.length) return '';
  const line = buildPath(points, width, height);
  return `${line} L ${width},${height} L 0,${height} Z`;
}

export function SentinelLineChart({
  points,
  accent = '#4edea3',
  compact = false,
}: {
  points: PortfolioGrowthPoint[];
  accent?: string;
  compact?: boolean;
}) {
  const width = 1000;
  const height = compact ? 280 : 320;
  const area = buildArea(points, width, height);
  const line = buildPath(points, width, height);
  const labels = points.filter((_, index) => index === 0 || index === points.length - 1 || index % Math.max(1, Math.floor(points.length / 4)) === 0);
  const peak = [...points].sort((a, b) => b.value - a.value)[0];

  return (
    <div className={cn('relative w-full', compact ? 'h-[300px]' : 'h-[360px]')}>
      <svg className="h-full w-full" preserveAspectRatio="none" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id={`gradient-${accent.replace('#', '')}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={accent} stopOpacity="0.18" />
            <stop offset="100%" stopColor={accent} stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1={height * 0.2} x2={width} y2={height * 0.2} stroke="rgba(255,255,255,0.05)" strokeDasharray="6 10" />
        <line x1="0" y1={height * 0.5} x2={width} y2={height * 0.5} stroke="rgba(255,255,255,0.05)" strokeDasharray="6 10" />
        <line x1="0" y1={height * 0.8} x2={width} y2={height * 0.8} stroke="rgba(255,255,255,0.05)" strokeDasharray="6 10" />
        {area ? <path d={area} fill={`url(#gradient-${accent.replace('#', '')})`} /> : null}
        {line ? <path d={line} fill="none" stroke={accent} strokeLinecap="round" strokeWidth="3.5" /> : null}
      </svg>
      {peak ? (
        <div className="absolute right-[18%] top-12 rounded-2xl border border-white/10 bg-[rgba(53,52,55,0.48)] px-4 py-3 shadow-2xl backdrop-blur-xl">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Peak</p>
          <p className="font-mono text-[18px] font-medium text-white">{formatCurrency(peak.value)}</p>
        </div>
      ) : null}
      <div className="mt-6 flex justify-between px-2">
        {labels.slice(0, 5).map((label) => (
          <span key={label.date} className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">
            {new Date(label.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        ))}
      </div>
    </div>
  );
}

export function AllocationDonut({
  items,
  totalValue,
}: {
  items: PortfolioAllocation[];
  totalValue: number;
}) {
  const radius = 15.9;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <div className="space-y-5">
      <div className="relative mx-auto flex h-52 w-52 items-center justify-center">
        <svg className="-rotate-90 h-full w-full" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r={radius} fill="transparent" stroke="#2a2a2c" strokeWidth="3.5" />
          {items.map((item, index) => {
            const dash = (item.percent / 100) * circumference;
            const currentOffset = offset;
            offset += dash;
            return (
              <circle
                key={item.category}
                cx="18"
                cy="18"
                r={radius}
                fill="transparent"
                stroke={palette[index % palette.length]}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-currentOffset}
                strokeWidth="3.5"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Total</span>
          <span className="text-[28px] font-black tracking-tight text-white">{formatCurrency(totalValue, true)}</span>
        </div>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={item.category} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: palette[index % palette.length] }} />
              <span className="text-xs text-[var(--on-surface-variant)]">{item.category}</span>
            </div>
            <span className="font-mono text-xs font-bold text-white">{item.percent.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
