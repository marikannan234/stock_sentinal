'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { ReactNode } from 'react';
import { cn } from '@/lib/sentinel-utils';

type AuthMode = 'login' | 'register';

export function AuthShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isRegister = pathname.includes('/register');
  const mode: AuthMode = isRegister ? 'register' : 'login';

  const hero = isRegister
    ? {
        title: 'JOIN THE SENTINEL',
        body: 'Create your command center for markets, alerts, and portfolio control.',
        cta: 'Already provisioned?',
        href: '/login',
        hrefLabel: 'Sign In',
      }
    : {
        title: 'WELCOME BACK',
        body: 'Track markets, monitor alerts, and manage your portfolio with precision.',
        cta: 'New operator?',
        href: '/register',
        hrefLabel: 'Create Account',
      };

  return (
    <main className="flex min-h-screen items-center justify-center overflow-hidden px-6 py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(77,142,255,0.13),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(78,222,163,0.07),transparent_24%)]" />
      <div className="relative w-full max-w-6xl overflow-hidden rounded-[30px] border border-white/5 bg-[rgba(28,27,29,0.94)] shadow-[0_40px_110px_rgba(0,0,0,0.4)]">
        <div className="grid min-h-[680px] lg:grid-cols-2">
          <motion.div
            className="absolute inset-y-0 left-0 hidden w-1/2 border-r border-white/5 bg-[linear-gradient(180deg,rgba(35,35,38,0.98),rgba(27,27,29,0.98))] lg:block"
            animate={{ x: mode === 'register' ? '100%' : '0%' }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          />

          <section className={cn('relative z-10 hidden px-10 py-20 lg:flex lg:flex-col lg:justify-center', mode === 'register' ? 'order-2' : 'order-1')}>
            <motion.div
              key={`hero-${mode}`}
              initial={{ x: mode === 'register' ? 80 : -80, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: mode === 'register' ? -80 : 80, opacity: 0 }}
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="mx-auto max-w-md text-center"
            >
              <div className="mb-10 flex items-center justify-center gap-3 text-lg font-black uppercase tracking-[-0.04em] text-white">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-strong)] text-xs text-[var(--on-primary)]">S</span>
                Stock Sentinel
              </div>
              <h1 className="text-[54px] font-black leading-[0.95] tracking-[-0.08em] text-white">{hero.title}</h1>
              <p className="mt-6 text-[22px] leading-9 text-[var(--on-surface-variant)]">{hero.body}</p>
              <div className="mt-10">
                <p className="mb-4 text-sm uppercase tracking-[0.24em] text-[var(--on-surface-variant)]">{hero.cta}</p>
                <Link href={hero.href} className="inline-flex rounded-xl border border-white/15 px-8 py-4 text-sm font-black uppercase tracking-[0.22em] text-white">
                  {hero.hrefLabel}
                </Link>
              </div>
            </motion.div>
          </section>

          <section className={cn('relative z-10 flex items-center justify-center px-6 py-14 sm:px-10 lg:px-14', mode === 'register' ? 'order-1' : 'order-2')}>
            <div className="w-full max-w-md">
              <div className="mb-10 text-center lg:text-left">
                <p className="mb-3 text-[10px] font-black uppercase tracking-[0.28em] text-[var(--primary)]">Secure Session Layer</p>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`heading-${mode}`}
                    initial={{ x: mode === 'register' ? -48 : 48, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: mode === 'register' ? 48 : -48, opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <h2 className="text-[42px] font-black tracking-[-0.08em] text-white">{mode === 'register' ? 'CREATE ACCOUNT' : 'SIGN IN'}</h2>
                    <p className="mt-2 text-sm text-[var(--on-surface-variant)]">
                      {mode === 'register' ? 'Deploy your Stock Sentinel cockpit.' : 'Initialize your secure session.'}
                    </p>
                  </motion.div>
                </AnimatePresence>
              </div>

              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={pathname}
                  initial={{ x: mode === 'register' ? 90 : -90, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: mode === 'register' ? -90 : 90, opacity: 0 }}
                  transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
