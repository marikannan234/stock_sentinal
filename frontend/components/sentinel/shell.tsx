'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import type { AlertItem, LiveQuote, SymbolSearchItem } from '@/lib/types';
import { cn, formatCurrency, formatPercent } from '@/lib/sentinel-utils';
import { Icon } from './primitives';
import { alertService, marketService, tradeService } from '@/lib/api-service';

type NavItem = {
  href: string;
  label: string;
  icon: string;
};

const primaryNav: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { href: '/stocks/NVDA', label: 'Stocks', icon: 'show_chart' },
  { href: '/portfolio', label: 'Portfolio', icon: 'pie_chart' },
  { href: '/watchlist', label: 'Watchlist', icon: 'list_alt' },
  { href: '/trade-history', label: 'Trade History', icon: 'history' },
  { href: '/alerts', label: 'Alerts', icon: 'notifications_active' },
  { href: '/news', label: 'News', icon: 'article' },
  { href: '/support', label: 'Support', icon: 'help_outline' },
  { href: '/settings', label: 'Settings', icon: 'settings' },
];

/* ─────────────────────── Quick-Trade Modal ─────────────────────── */
function QuickTradeModal({ onClose }: { onClose: () => void }) {
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol || !quantity || !price) return;
    setLoading(true);
    setError('');
    try {
      await tradeService.create({
        symbol: symbol.toUpperCase(),
        quantity: Number(quantity),
        entry_price: Number(price),
        trade_type: side,
      });
      setToast(`${side.toUpperCase()} order placed for ${symbol.toUpperCase()}`);
      setTimeout(() => {
        setToast('');
        onClose();
      }, 1800);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Order failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-sm rounded-3xl border border-white/10 bg-[#1a1a1c] p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-black uppercase tracking-[0.08em] text-white">Quick Trade</h2>
          <button onClick={onClose} className="text-[var(--on-surface-variant)] hover:text-white"><Icon name="close" /></button>
        </div>
        {toast ? (
          <div className="rounded-2xl bg-secondary/10 px-4 py-4 text-center text-sm font-bold text-secondary">{toast}</div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setSide('buy')} className={cn('rounded-xl py-2.5 text-sm font-black uppercase tracking-[0.12em] transition-all', side === 'buy' ? 'bg-secondary/15 text-secondary border border-secondary/30' : 'bg-[var(--surface-lowest)] text-[var(--on-surface-variant)]')}>Buy</button>
              <button type="button" onClick={() => setSide('sell')} className={cn('rounded-xl py-2.5 text-sm font-black uppercase tracking-[0.12em] transition-all', side === 'sell' ? 'bg-tertiary/15 text-tertiary border border-tertiary/30' : 'bg-[var(--surface-lowest)] text-[var(--on-surface-variant)]')}>Sell</button>
            </div>
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-3 font-mono text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
              placeholder="Symbol (e.g. AAPL)"
              required
            />
            <input
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              type="number"
              min="0.001"
              step="0.001"
              className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-3 font-mono text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
              placeholder="Quantity"
              required
            />
            <input
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              type="number"
              min="0.01"
              step="0.01"
              className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-3 font-mono text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
              placeholder="Entry Price (USD)"
              required
            />
            {error && <p className="text-xs text-tertiary">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-4 py-3 text-sm font-black text-[var(--on-primary)] disabled:opacity-60"
            >
              {loading ? 'Placing…' : 'Place Order'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────── Alert Bell Modal ─────────────────────── */
function AlertBellModal({ alerts, onClose }: { alerts: AlertItem[]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[200] flex items-start justify-end pt-20 pr-6 bg-transparent" onClick={onClose}>
      <div
        className="w-80 max-h-[70vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#1a1a1c] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-white/5 bg-[#1a1a1c] px-5 py-4">
          <h3 className="text-sm font-black uppercase tracking-[0.12em] text-white">Alerts</h3>
          <span className="rounded-full bg-[var(--primary)]/20 px-2 py-0.5 text-[10px] font-black text-[var(--primary)]">
            {alerts.filter((a) => a.is_active).length} active
          </span>
        </div>
        {alerts.length === 0 ? (
          <p className="px-5 py-6 text-sm text-[var(--on-surface-variant)]">No alerts configured.</p>
        ) : (
          <div className="divide-y divide-white/5">
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="font-bold text-white text-sm">{alert.stock_symbol}</p>
                  <p className="text-[10px] text-[var(--on-surface-variant)]">
                    {alert.alert_type}{alert.condition ? ` ${alert.condition} ${alert.target_value}` : ''}
                  </p>
                </div>
                <span className={cn('rounded-full px-3 py-1 text-[10px] font-black uppercase', alert.is_active ? 'bg-secondary/10 text-secondary' : 'bg-[var(--surface-high)] text-[var(--on-surface-variant)]')}>
                  {alert.is_active ? 'Live' : 'Off'}
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="border-t border-white/5 px-5 py-3">
          <Link href="/alerts" onClick={onClose} className="block text-center text-xs font-black uppercase tracking-[0.12em] text-[var(--primary)]">
            Manage Alerts →
          </Link>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────── Search Dropdown ─────────────────────── */
function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SymbolSearchItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const search = useCallback((q: string) => {
    if (!q.trim()) { setResults([]); setOpen(false); return; }
    setLoading(true);
    marketService.search(q)
      .then((data) => { setResults(data.slice(0, 8)); setOpen(true); })
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, []);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(val), 300);
  }

  function handleSelect(ticker: string) {
    setQuery('');
    setResults([]);
    setOpen(false);
    router.push(`/stocks/${ticker}`);
  }

  // close on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  return (
    <div ref={wrapperRef} className="relative hidden items-center md:flex">
      <div className="flex items-center rounded-xl bg-[var(--surface-lowest)] px-4 py-2">
        <Icon name="search" className="mr-2 text-sm text-[var(--on-surface-variant)]" />
        <input
          value={query}
          onChange={handleChange}
          onFocus={() => query && setOpen(true)}
          className="w-56 bg-transparent text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] xl:w-72"
          placeholder="Search markets…"
        />
        {loading && <Icon name="progress_activity" className="animate-spin text-xs text-[var(--on-surface-variant)]" />}
      </div>
      {open && results.length > 0 && (
        <div className="absolute left-0 top-full mt-2 w-full rounded-2xl border border-white/10 bg-[#1c1c1e] shadow-2xl z-[300]">
          {results.map((item) => (
            <button
              key={item.ticker}
              onClick={() => handleSelect(item.ticker)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-[var(--surface-high)] first:rounded-t-2xl last:rounded-b-2xl"
            >
              <span className="font-mono text-sm font-bold text-white">{item.ticker}</span>
              {item.name && <span className="truncate text-xs text-[var(--on-surface-variant)]">{item.name}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────── Main Shell ─────────────────────── */
export function SentinelShell({
  children,
  title,
  subtitle,
  ribbon,
  headerActions,
  sidebarFooter,
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  ribbon?: LiveQuote[];
  headerActions?: ReactNode;
  sidebarFooter?: ReactNode;
}) {
  const pathname = usePathname();
  const [tradeOpen, setTradeOpen] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    alertService.list().then(setAlerts).catch(() => setAlerts([]));
  }, []);

  function handleLogout() {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('stocksentinel_token');
      window.location.href = '/login';
    }
  }

  const activeAlertCount = alerts.filter((a) => a.is_active).length;

  return (
    <div className="min-h-screen bg-[var(--surface)] text-[var(--on-surface)]">
      {/* ── Top Header ── */}
      <header className="fixed left-0 top-0 z-50 flex h-16 w-full items-center gap-4 border-b border-white/5 bg-[rgba(19,19,21,0.82)] px-6 shadow-[0_40px_40px_-15px_rgba(0,0,0,0.42)] backdrop-blur-xl">
        {/* App Name */}
        <Link href="/dashboard" className="shrink-0 text-xl font-black uppercase tracking-[-0.05em] text-white">
          Stock Sentinel
        </Link>

        {/* Live Ribbon — grows to fill available space, fades at edges */}
        {ribbon && ribbon.length > 0 && (
          <div className="ticker-wrap hidden flex-1 border-l border-white/10 pl-4 lg:block min-w-0">
            <div className="ticker-track gap-8 text-[10px] uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">
              {/* Two copies for seamless infinite loop (-50% translate) */}
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
        )}

        {/* Right-side actions — always at end */}
        <div className="ml-auto flex shrink-0 items-center gap-3">
          <SearchBar />

          {/* Quick Trade Button */}
          <button
            onClick={() => setTradeOpen(true)}
            className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-4 py-2 text-sm font-bold text-[var(--on-primary)] transition-transform active:scale-95"
          >
            Quick Trade
          </button>

          {/* Alert Bell */}
          <button
            onClick={() => setBellOpen((prev) => !prev)}
            className="relative text-[var(--on-surface-variant)] hover:text-white transition-colors"
          >
            <Icon name="notifications" className="text-[22px]" />
            {activeAlertCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-tertiary text-[9px] font-black text-white">
                {activeAlertCount > 9 ? '9+' : activeAlertCount}
              </span>
            )}
          </button>

          {/* Profile Icon */}
          <Link href="/settings" className="text-[var(--primary)] hover:opacity-80 transition-opacity">
            <Icon name="account_circle" className="text-[22px]" />
          </Link>
        </div>
      </header>

      {/* Modals */}
      {tradeOpen && <QuickTradeModal onClose={() => setTradeOpen(false)} />}
      {bellOpen && <AlertBellModal alerts={alerts} onClose={() => setBellOpen(false)} />}

      {/* ── Sidebar ── */}
      <aside className="fixed left-0 top-0 hidden h-screen w-56 flex-col bg-[var(--surface-low)] py-8 md:flex overflow-hidden">
        <div className="mb-8 mt-16 px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--surface-highest)]">
              <Icon name="shield_person" className="text-[18px] text-[var(--primary)]" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold text-white">The Sentinel</p>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">Pro Tier</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto space-y-1 px-3">
          {primaryNav.map((item) => {
            const active = pathname === item.href || (item.href.startsWith('/stocks/') && pathname.startsWith('/stocks/'));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300',
                  active
                    ? 'translate-x-1 border-r-2 border-[var(--primary)] bg-[var(--surface-bright)] font-bold text-white'
                    : 'text-[var(--on-surface-variant)] hover:bg-[var(--surface-high)] hover:text-white',
                )}
              >
                <Icon name={item.icon} className="text-[18px] shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="px-3 pb-4 space-y-2">
          {sidebarFooter}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--on-surface-variant)] transition-all hover:bg-tertiary/10 hover:text-tertiary"
          >
            <Icon name="logout" className="text-[18px] shrink-0" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="px-6 pb-24 pt-24 md:ml-56 lg:px-10">
        {(title || subtitle) && (
          <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              {title ? <h1 className="text-[36px] font-black tracking-[-0.06em] text-white">{title}</h1> : null}
              {subtitle ? <p className="max-w-2xl text-sm text-[var(--on-surface-variant)]">{subtitle}</p> : null}
            </div>
            {headerActions}
          </div>
        )}
        {children}
      </main>

      {/* ── Mobile Bottom Nav ── */}
      <nav className="fixed bottom-0 left-0 z-50 flex h-20 w-full items-center justify-around border-t border-white/5 bg-[rgba(28,27,29,0.92)] px-4 backdrop-blur-xl md:hidden">
        {primaryNav.slice(0, 5).map((item) => {
          const active = pathname === item.href || (item.href.startsWith('/stocks/') && pathname.startsWith('/stocks/'));
          return (
            <Link key={item.href} href={item.href} className={cn('flex flex-col items-center gap-1', active ? 'text-[var(--primary)]' : 'text-[var(--on-surface-variant)]')}>
              <Icon name={item.icon} className="text-[20px]" />
              <span className="text-[10px] font-bold">{item.label.split(' ')[0]}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
