'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/auth';

export function SessionBootstrap() {
  useEffect(() => {
    useAuthStore.getState().hydrate();
  }, []);

  return null;
}
