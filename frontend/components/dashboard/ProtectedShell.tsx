'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { useAuthStore } from '@/lib/auth';

export function ProtectedShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { token, isHydrated } = useAuthStore();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    if (!isHydrated) return;

    if (!token) {
      router.replace('/login');
      return;
    }

    setIsAuthorized(true);
  }, [token, isHydrated, router]);

  if (!isHydrated || !isAuthorized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#adc6ff] border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
