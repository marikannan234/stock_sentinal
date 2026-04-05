'use client';

import type { ReactNode } from 'react';
import clsx from 'clsx';

export function SurfaceCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        'rounded-2xl border border-white/5 bg-[#201f22]/90 p-6 shadow-[0_20px_40px_-30px_rgba(0,0,0,0.9)] backdrop-blur-xl',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  helper,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  helper?: string;
  tone?: 'neutral' | 'positive' | 'negative' | 'primary';
}) {
  const toneClass = {
    neutral: 'text-white',
    positive: 'text-secondary',
    negative: 'text-tertiary',
    primary: 'text-primary',
  }[tone];

  return (
    <SurfaceCard className="relative overflow-hidden">
      <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/5 blur-2xl" />
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-on-surface-variant">{label}</p>
      <p className={clsx('mt-4 text-3xl font-black tracking-tight', toneClass)}>{value}</p>
      {helper ? <p className="mt-3 text-sm text-on-surface-variant">{helper}</p> : null}
    </SurfaceCard>
  );
}
