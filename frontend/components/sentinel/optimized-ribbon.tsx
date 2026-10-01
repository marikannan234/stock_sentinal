'use client';

/**
 * OptimizedRibbon Component
 * Features:
 * - Reads the shared ticker query (cached across page changes, so no flicker)
 * - Smooth animation
 * - Responsive hiding on small screens
 */

import Link from 'next/link';
import { useRibbonQuery } from '@/hooks/queries/use-market';
import { formatCurrency, formatPercent } from '@/lib/sentinel-utils';
import { Icon } from '@/components/sentinel/primitives';

export function OptimizedRibbon() {
  const { data: ribbon } = useRibbonQuery();

  // Don't render if no data
  if (!ribbon || ribbon.length === 0) {
    return null;
  }

  return (
    <div className="ticker-wrap hidden flex-1 border-l border-white/10 pl-4 lg:block min-w-0">
      <div className="ticker-track gap-8 text-[10px] uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">
        {/* Two copies for seamless infinite loop */}
        {[...ribbon, ...ribbon].map((quote, index) => (
          <Link
            key={`${quote.symbol}-${index}`}
            href={`/stocks/${quote.symbol}`}
            className="flex items-center gap-1.5 whitespace-nowrap font-mono hover:opacity-80 transition-opacity"
          >
            <span className="font-bold text-white">{quote.symbol}</span>
            <span className={quote.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}>
              {formatCurrency(quote.price)} {formatPercent(quote.change_percent)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
