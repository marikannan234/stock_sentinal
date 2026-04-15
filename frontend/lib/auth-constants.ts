/**
 * Authorization constants and utilities
 * Ensures consistent token access across the application
 */

export const TOKEN_KEY = 'stocksentinel_token';

/**
 * Get stored auth token from localStorage
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Check if user has a valid auth token
 */
export function hasAuthToken(): boolean {
  return Boolean(getStoredToken());
}
