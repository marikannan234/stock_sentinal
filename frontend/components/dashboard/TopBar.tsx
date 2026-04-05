'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { marketService } from '@/lib/api-service';
import { useAuthStore } from '@/lib/auth';
import type { LiveQuote, SymbolSearchItem } from '@/lib/types';

export function TopBar() {
  const router = useRouter();
  const { user } = useAuthStore();

  const [quotes, setQuotes] = useState<LiveQuote[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SymbolSearchItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');

  useEffect(() => {
    let active = true;

    marketService
      .getLiveRibbon()
      .then((data) => {
        if (active) setQuotes(data.stocks.slice(0, 12));
      })
      .catch(() => {
        if (active) setQuotes([]);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearchError('');
      return;
    }

    let active = true;
    const timeout = window.setTimeout(async () => {
      try {
        setSearching(true);
        setSearchError('');
        const data = await marketService.search(query.trim());
        if (active) setResults(data);
      } catch {
        if (active) {
          setResults([]);
          setSearchError('Search is temporarily unavailable.');
        }
      } finally {
        if (active) setSearching(false);
      }
    }, 300);

    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [query]);

  const ribbon = useMemo(() => (quotes.length ? [...quotes, ...quotes] : []), [quotes]);

  return (
    <>
      <div className="fixed left-0 top-0 z-[60] flex h-10 w-full items-center overflow-hidden border-b border-outline-variant/10 bg-surface-container-lowest">
        <div className="ticker-marquee flex items-center gap-8 px-4">
          {ribbon.map((stock, idx) => (
            <Link
              key={`${stock.symbol}-${idx}`}
              href={`/stocks/${stock.symbol}`}
              className="flex shrink-0 items-center gap-2 hover:text-primary"
            >
              <span className="text-xs font-bold">{stock.symbol}</span>
              <span className="font-['Roboto_Mono'] text-sm">{stock.price.toFixed(2)}</span>
              <span className={`text-xs font-medium ${stock.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}`}>
                {stock.change_percent >= 0 ? '+' : ''}
                {stock.change_percent.toFixed(2)}%
              </span>
            </Link>
          ))}
        </div>
      </div>

      <nav className="fixed left-0 top-10 z-50 flex h-16 w-full items-center justify-between border-b border-white/5 bg-[#131315]/80 px-6 shadow-[0_40px_40px_-15px_rgba(0,0,0,0.4)] backdrop-blur-xl">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-xl font-black uppercase tracking-tighter text-white">
            Stock Sentinel
          </Link>
          <div className="relative hidden md:block">
            <div className="group flex items-center rounded-full border border-white/5 bg-surface-container-lowest px-4 py-1.5 focus-within:border-primary/50 transition-all">
              <span className="material-symbols-outlined text-sm text-on-surface-variant">search</span>
              <input
                className="w-64 border-none bg-transparent pl-2 text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none"
                placeholder="Search markets..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            {(query.trim() || searching || searchError) && (
              <div className="absolute mt-2 w-full overflow-hidden rounded-2xl border border-white/5 bg-[#1b1b1f] shadow-2xl">
                {searching ? <p className="px-4 py-3 text-sm text-on-surface-variant">Searching…</p> : null}
                {!searching && searchError ? <p className="px-4 py-3 text-sm text-tertiary">{searchError}</p> : null}
                {!searching && !searchError && results.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-on-surface-variant">No results found.</p>
                ) : null}
                {results.map((item) => (
                  <button
                    key={item.ticker}
                    onClick={() => {
                      setQuery('');
                      setResults([]);
                      router.push(`/stocks/${item.ticker}`);
                    }}
                    className="flex w-full items-start justify-between border-t border-white/5 px-4 py-3 text-left transition hover:bg-white/5"
                  >
                    <div>
                      <p className="text-sm font-semibold text-white">{item.ticker}</p>
                      <p className="text-xs text-on-surface-variant">{item.name || 'Unknown symbol'}</p>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant">north_east</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/support" className="material-symbols-outlined cursor-pointer text-[#c2c6d6] transition-colors duration-200 hover:text-white">
            notifications
          </Link>
          <Link
            href="/profile"
            className="flex items-center gap-2 rounded-full border border-white/5 bg-surface-container-high px-3 py-1 transition-all hover:bg-surface-bright"
          >
            <span className="material-symbols-outlined text-[#adc6ff]">account_circle</span>
            <span className="text-xs font-medium text-white">{user?.full_name || user?.email || 'The Sentinel'}</span>
          </Link>
        </div>
      </nav>
    </>
  );
}
