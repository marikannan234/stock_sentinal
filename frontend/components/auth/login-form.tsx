'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';

export function LoginForm() {
  const router = useRouter();
  const pathname = usePathname();
  const { login, token, loading, error, clearError } = useAuthStore();
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // 🚨 Only redirect if: (1) component mounted, (2) user has token, (3) NOT on auth pages
  useEffect(() => {
    if (!mounted) return;
    if (!token) return;
    if (pathname.includes('/login') || pathname.includes('/register')) return;
    
    // Safe to redirect to dashboard
    router.replace('/dashboard');
  }, [mounted, token, pathname, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    try {
      await login(emailOrPhone, password);
      router.replace('/dashboard');
    } catch {
      return;
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Email or Phone</label>
        <input value={emailOrPhone} onChange={(event) => setEmailOrPhone(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="name@sentinel.com or +919876543210" required />
      </div>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Password</label>
        <input value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="••••••••" type="password" required />
      </div>
      {error ? <p className="text-sm text-[var(--tertiary)]">{error}</p> : null}
      <button type="submit" disabled={loading} className="w-full rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-6 py-4 text-sm font-black uppercase tracking-[0.22em] text-[var(--on-primary)] shadow-[0_22px_50px_rgba(77,142,255,0.28)] transition-transform active:scale-[0.99]">
        {loading ? 'Initializing...' : 'Initialize'}
      </button>
      <div className="text-center text-sm text-[var(--on-surface-variant)] lg:hidden">
        Need access?{' '}
        <Link href="/register" className="font-bold text-white">
          Create Account
        </Link>
      </div>
    </form>
  );
}
