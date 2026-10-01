'use client';

import { useQuery } from '@tanstack/react-query';
import { newsService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import type { NewsArticle, NewsResponse } from '@/lib/types';
import { useIsAuthenticated } from './use-is-authenticated';

/** One fetch serves every consumer; the dashboard shows the first few articles. */
const GLOBAL_NEWS_LIMIT = 50;
/** The backend caches global news for 5 minutes. */
const NEWS_STALE_TIME_MS = 5 * 60_000;

const selectArticles = (response: NewsResponse): NewsArticle[] => response.articles ?? [];

/** Global market news (`GET /news` returns `{ articles, count }`). */
export function useGlobalNewsQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.news.global(),
    queryFn: () => newsService.global(GLOBAL_NEWS_LIMIT),
    select: selectArticles,
    enabled: isAuthenticated,
    staleTime: NEWS_STALE_TIME_MS,
  });
}
