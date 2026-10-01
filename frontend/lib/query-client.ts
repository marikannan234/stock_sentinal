import { QueryClient, isServer } from '@tanstack/react-query';
import { isAxiosError } from 'axios';

/** Market data (ticker, market summary) refresh interval; matches the backend's 10 s cache. */
export const MARKET_REFETCH_INTERVAL_MS = 10_000;

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Data is reused across page navigations for a few seconds instead of
        // being refetched on every mount.
        staleTime: 5_000,
        // Retry network/5xx failures twice; a 4xx will not succeed on retry.
        retry: (failureCount, error) => {
          const status = isAxiosError(error) ? error.response?.status : undefined;
          if (status !== undefined && status >= 400 && status < 500) return false;
          return failureCount < 2;
        },
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

/**
 * One QueryClient per browser session (so logout can clear it) and a fresh one
 * per server render (so no data is shared between requests).
 */
export function getQueryClient() {
  if (isServer) return makeQueryClient();
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
}
