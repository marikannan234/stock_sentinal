'use client';

/**
 * Optimized News Page
 * Features:
 * - Uses cached news from global store
 * - Lazy loading with skeleton screens
 * - Infinite scroll / pagination
 * - Non-blocking loading
 * - Search and filter
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard, Skeleton, Icon } from '@/components/sentinel/primitives';
import { useNewsData } from '@/hooks/useDataFetch';
import type { NewsArticle } from '@/lib/types';
import { formatRelativeTime } from '@/lib/sentinel-utils';

function sentimentBadge(sentiment?: string | null) {
  if (!sentiment) return null;
  const s = sentiment.toLowerCase();
  const cls =
    s === 'positive' || s === 'bullish'
      ? 'bg-secondary/10 text-secondary'
      : s === 'negative' || s === 'bearish'
        ? 'bg-tertiary/10 text-tertiary'
        : 'bg-[var(--surface-high)] text-[var(--on-surface-variant)]';
  return (
    <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.15em] ${cls}`}>
      {sentiment}
    </span>
  );
}

const ARTICLES_PER_PAGE = 12;

export default function NewsPage() {
  const { news: cachedNews, newsLoading, isRefetching, refetch } = useNewsData(50);

  // Local pagination state
  const [displayedArticles, setDisplayedArticles] = useState<NewsArticle[]>([]);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter articles by search query (MUST be before loadMore)
  const filteredArticles = useMemo(() => {
    if (!searchQuery.trim()) return cachedNews;
    const query = searchQuery.toLowerCase();
    return cachedNews.filter(
      (article) =>
        article.title?.toLowerCase().includes(query) ||
        article.summary?.toLowerCase().includes(query) ||
        article.source?.toLowerCase().includes(query),
    );
  }, [cachedNews, searchQuery]);

  // Load more articles
  const loadMore = useCallback(() => {
    const startIdx = page * ARTICLES_PER_PAGE;
    const endIdx = startIdx + ARTICLES_PER_PAGE;
    const newArticles = filteredArticles.slice(0, endIdx);
    setDisplayedArticles(newArticles);
    setPage(page + 1);
  }, [page, filteredArticles]);

  // Initialize display on mount or when filters change
  useEffect(() => {
    setPage(1);
    const initialArticles = filteredArticles.slice(0, ARTICLES_PER_PAGE);
    setDisplayedArticles(initialArticles);
  }, [filteredArticles]);

  // Render skeleton cards
  const renderSkeletons = () => (
    <div className="grid gap-5 lg:grid-cols-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <SurfaceCard key={`skeleton-${i}`} className="overflow-hidden">
          <div className="p-5 space-y-3">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-5/6" />
            <Skeleton className="h-8 w-full" />
            <div className="flex justify-between pt-2">
              <Skeleton className="h-3 w-32" />
              <Skeleton className="h-3 w-12" />
            </div>
          </div>
        </SurfaceCard>
      ))}
    </div>
  );

  return (
    <ProtectedScreen>
      <SentinelShell title="News Intelligence" subtitle="Live market news with intelligent filtering.">
        {/* Search + Refetch */}
        <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search news…"
              className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-2.5 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
            />
          </div>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center gap-2 rounded-xl bg-[var(--surface-high)] px-4 py-2.5 text-sm font-medium text-white transition-all disabled:opacity-50"
          >
            <Icon name={isRefetching ? 'progress_activity' : 'refresh'} className={isRefetching ? 'animate-spin' : ''} />
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Loading State - Non-blocking skeleton */}
        {newsLoading && displayedArticles.length === 0 ? (
          renderSkeletons()
        ) : filteredArticles.length === 0 ? (
          <div className="flex min-h-[40vh] items-center justify-center">
            <div className="text-center">
              <div className="mb-3 text-3xl">🔍</div>
              <p className="text-sm text-[var(--on-surface-variant)]">
                {searchQuery ? 'No articles match your search.' : 'No news available.'}
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Articles Grid */}
            <div className="grid gap-5 lg:grid-cols-2">
              {displayedArticles.map((article, index) => (
                <SurfaceCard
                  key={`${article.url}-${index}`}
                  className="overflow-hidden hover:border-white/10 transition-colors flex flex-col"
                >
                  <div className="p-5 flex flex-col h-full">
                    {/* Source + Sentiment */}
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--primary)]">
                        {article.source}
                      </p>
                      {sentimentBadge(article.sentiment)}
                    </div>

                    {/* Title */}
                    <a href={article.url} target="_blank" rel="noreferrer" className="block flex-1">
                      <h2 className="mb-2 text-base font-bold leading-snug text-white hover:text-[var(--primary)] transition-colors">
                        {article.title}
                      </h2>
                    </a>

                    {/* Summary */}
                    {article.summary && (
                      <p className="mb-4 text-sm leading-6 text-[var(--on-surface-variant)] line-clamp-3">
                        {article.summary}
                      </p>
                    )}

                    {/* Footer */}
                    <div className="mt-auto flex items-center justify-between border-t border-white/5 pt-3">
                      <span className="text-xs text-[var(--on-surface-variant)]">
                        {formatRelativeTime(article.published_at)}
                      </span>
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-medium text-[var(--primary)] hover:underline"
                      >
                        Read →
                      </a>
                    </div>
                  </div>
                </SurfaceCard>
              ))}
            </div>

            {/* Load More Button */}
            {displayedArticles.length < filteredArticles.length && (
              <div className="mt-8 flex justify-center">
                <button
                  onClick={loadMore}
                  className="rounded-xl border border-white/10 px-6 py-3 text-sm font-semibold text-white transition-all hover:border-white/20 hover:bg-white/5 active:scale-95"
                >
                  Load More ({displayedArticles.length} of {filteredArticles.length})
                </button>
              </div>
            )}

            {/* No More Articles */}
            {displayedArticles.length >= filteredArticles.length && filteredArticles.length > 0 && (
              <div className="mt-8 text-center">
                <p className="text-sm text-[var(--on-surface-variant)]">
                  {filteredArticles.length} articles total
                </p>
              </div>
            )}
          </>
        )}
      </SentinelShell>
    </ProtectedScreen>
  );
}
