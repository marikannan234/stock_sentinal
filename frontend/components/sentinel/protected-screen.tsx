'use client';

import { ReactNode, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';

export function ProtectedScreen({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, isHydrated, loading } = useAuthStore();

  useEffect(() => {
    if (isHydrated && !loading && !token && !pathname.includes('/login') && !pathname.includes('/register')) {
      router.replace('/login');
    }
  }, [isHydrated, loading, token, pathname, router]);

  if (!isHydrated || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] text-[var(--on-surface)]">
        <div className="rounded-2xl border border-white/5 bg-[var(--surface-low)] px-6 py-5 text-sm tracking-[0.24em] text-[var(--on-surface-variant)]">
          INITIALIZING TERMINAL
        </div>
      </div>
    );
  }

  if (!token) return null;
  return <>{children}</>;
}
