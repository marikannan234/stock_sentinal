'use client';

import { useAuthStore } from '@/lib/auth';

/** True once the session is restored and a token exists; gates every authenticated query. */
export function useIsAuthenticated() {
  return useAuthStore((state) => state.isHydrated && Boolean(state.token));
}
