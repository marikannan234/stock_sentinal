'use client';

import { useMemo } from 'react';
import { useAuthStore } from './auth';

export function useAuth() {
  const { user, token, loading, error, login, register, logout, refreshUser } = useAuthStore();

  return useMemo(
    () => ({
      user,
      token,
      loading,
      error,
      isAuthenticated: !!token,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, token, loading, error, login, register, logout, refreshUser],
  );
}

export function useRequireAuth() {
  const { token, isHydrated, loading } = useAuthStore();

  return useMemo(
    () => ({
      isAuthenticated: !!token,
      isReady: isHydrated && !loading,
    }),
    [token, isHydrated, loading],
  );
}
