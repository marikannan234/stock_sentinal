'use client';

import { useQuery } from '@tanstack/react-query';
import { marketService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import { useIsAuthenticated } from './use-is-authenticated';

/** Symbol lists change rarely; repeated searches for the same text reuse the result. */
const SEARCH_STALE_TIME_MS = 5 * 60_000;

/** Symbol suggestions for `query` (pass an already-debounced value). */
export function useSymbolSearchQuery(query: string) {
  const isAuthenticated = useIsAuthenticated();
  const trimmed = query.trim();
  return useQuery({
    queryKey: queryKeys.symbolSearch(trimmed),
    queryFn: () => marketService.search(trimmed),
    enabled: isAuthenticated && trimmed.length > 0,
    staleTime: SEARCH_STALE_TIME_MS,
  });
}
