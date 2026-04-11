'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';

export function RegisterForm() {
  const router = useRouter();
  const { register, token, loading, error, clearError } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [whatsappPhone, setWhatsappPhone] = useState('');

  useEffect(() => {
    if (token) router.replace('/dashboard');
  }, [token, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    try {
      await register(email, password, fullName, whatsappPhone);
      router.replace('/dashboard');
    } catch {
      return;
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Full Name</label>
        <input value={fullName} onChange={(event) => setFullName(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="Alex Vanguard" type="text" />
      </div>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Email Address</label>
        <input value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="name@sentinel.com" type="email" required />
      </div>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">WhatsApp Phone (Optional)</label>
        <input value={whatsappPhone} onChange={(event) => setWhatsappPhone(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="+919876543210" type="tel" />
      </div>
      <div>
        <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Password</label>
        <input value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-high)] px-4 py-4 text-white outline-none placeholder:text-[var(--on-surface-variant)]" placeholder="••••••••" type="password" required />
      </div>
      {error ? <p className="text-sm text-[var(--tertiary)]">{error}</p> : null}
      <button type="submit" disabled={loading} className="w-full rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-6 py-4 text-sm font-black uppercase tracking-[0.22em] text-[var(--on-primary)] shadow-[0_22px_50px_rgba(77,142,255,0.28)] transition-transform active:scale-[0.99]">
        {loading ? 'Provisioning...' : 'Create Access'}
      </button>
      <div className="text-center text-sm text-[var(--on-surface-variant)] lg:hidden">
        Already registered?{' '}
        <Link href="/login" className="font-bold text-white">
          Sign In
        </Link>
      </div>
    </form>
  );
}
