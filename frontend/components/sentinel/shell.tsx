'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { LiveQuote } from '@/lib/types';
import { cn, formatCurrency, formatPercent } from '@/lib/sentinel-utils';
import { Icon } from './primitives';

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

  return (
    <div className="min-h-screen bg-[var(--surface)] text-[var(--on-surface)]">
      <header className="fixed left-0 top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/5 bg-[rgba(19,19,21,0.82)] px-6 shadow-[0_40px_40px_-15px_rgba(0,0,0,0.42)] backdrop-blur-xl">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-xl font-black uppercase tracking-[-0.05em] text-white">
            Stock Sentinel
          </Link>
          {ribbon?.length ? (
            <div className="hidden min-w-[380px] overflow-hidden border-l border-white/10 pl-6 lg:block">
              <div className="ticker-track flex gap-6 text-[10px] uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">
                {[...ribbon, ...ribbon].slice(0, 12).map((quote, index) => (
                  <div key={`${quote.symbol}-${index}`} className="flex items-center gap-1.5 whitespace-nowrap font-mono">
                    <span className="font-bold text-white">{quote.symbol}</span>
                    <span className={quote.change_percent >= 0 ? 'text-secondary' : 'text-tertiary'}>
                      {formatCurrency(quote.price)} {formatPercent(quote.change_percent)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden items-center rounded-xl bg-[var(--surface-lowest)] px-4 py-2 md:flex">
            <Icon name="search" className="mr-2 text-sm text-[var(--on-surface-variant)]" />
            <input
              className="w-56 bg-transparent text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] xl:w-72"
              placeholder="Search markets..."
            />
          </div>
          <Link
            href="/stocks/NVDA"
            className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-4 py-2 text-sm font-bold text-[var(--on-primary)] transition-transform active:scale-95"
          >
            Quick Trade
          </Link>
          <Link href="/settings" className="text-[var(--primary)]">
            <Icon name="account_circle" className="text-[22px]" />
          </Link>
        </div>
      </header>

      <aside className="fixed left-0 top-0 hidden h-screen w-64 flex-col bg-[var(--surface-low)] py-8 md:flex">
        <div className="mb-10 mt-16 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--surface-highest)]">
              <Icon name="shield_person" className="text-[20px] text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">The Sentinel</p>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--on-surface-variant)]">Pro Tier</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {primaryNav.map((item) => {
            const active = pathname === item.href || (item.href.startsWith('/stocks/') && pathname.startsWith('/stocks/'));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300',
                  active
                    ? 'translate-x-1 border-r-2 border-[var(--primary)] bg-[var(--surface-bright)] font-bold text-white'
                    : 'text-[var(--on-surface-variant)] hover:bg-[var(--surface-high)] hover:text-white',
                )}
              >
                <Icon name={item.icon} className="text-[19px]" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="px-4 pb-6">
          <Link
            href="/stocks/NVDA"
            className="mb-4 flex w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-4 py-3 text-sm font-bold text-[var(--on-primary)] shadow-[0_20px_40px_rgba(77,142,255,0.18)]"
          >
            Quick Trade
          </Link>
          {sidebarFooter}
        </div>
      </aside>

      <main className="px-6 pb-24 pt-24 md:ml-64 lg:px-10">
        {(title || subtitle) && (
          <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              {title ? <h1 className="text-[44px] font-black tracking-[-0.06em] text-white">{title}</h1> : null}
              {subtitle ? <p className="max-w-2xl text-sm text-[var(--on-surface-variant)]">{subtitle}</p> : null}
            </div>
            {headerActions}
          </div>
        )}
        {children}
      </main>

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
