'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/sentinel-utils';

export function Icon({ name, className }: { name: string; className?: string }) {
  return <span className={cn('material-symbols-outlined', className)}>{name}</span>;
}

export function SurfaceCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('rounded-3xl border border-white/5 bg-[var(--surface-low)]', className)}>
      {children}
    </div>
  );
}

export function StatChip({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: ReactNode;
  tone?: 'positive' | 'negative' | 'neutral';
}) {
  const toneClass =
    tone === 'positive'
      ? 'text-secondary'
      : tone === 'negative'
        ? 'text-tertiary'
        : 'text-[var(--on-surface)]';

  return (
    <div className="rounded-2xl bg-black/15 px-4 py-4">
      <p className="mb-1 text-[11px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">{label}</p>
      <p className={cn('font-mono text-[28px] leading-none', toneClass)}>{value}</p>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn('animate-pulse rounded bg-gray-300/20', className)} />
  );
}
