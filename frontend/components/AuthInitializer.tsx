'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/auth';

/**
 * AuthInitializer component
 * 
 * This component runs on app startup and hydrates the auth state
 * from localStorage. This ensures that users who refreshed the page
 * or closed/reopened the browser keep their logged-in state.
 */
export function AuthInitializer() {
  useEffect(() => {
    useAuthStore.getState().hydrate();
  }, []);

  return null;
}
