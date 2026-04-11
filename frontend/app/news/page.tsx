'use client';

import { useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard, Skeleton } from '@/components/sentinel/primitives';
import { marketService, newsService } from '@/lib/api-service';
import type { LiveQuote, NewsArticle } from '@/lib/types';
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

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([newsService.global(20), marketService.getLiveRibbon()]).then(([newsResult, ribbonResult]) => {
      if (newsResult.status === 'fulfilled') {
        setArticles(newsResult.value.articles);
      } else {
        setError('Failed to load news. Please try again.');
      }
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks);
      setLoading(false);
    });
  }, []);

  return (
    <ProtectedScreen>
      <SentinelShell title="News Intelligence" subtitle="Live market briefings from the backend news feed." ribbon={ribbon}>
        {error ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <p className="text-sm text-tertiary">{error}</p>
          </div>
        ) : loading ? (
          <div className="grid gap-5 lg:grid-cols-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
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
        ) : articles.length === 0 ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <p className="text-sm text-[var(--on-surface-variant)]">No news available.</p>
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            {articles.map((article, index) => (
              <SurfaceCard key={`${article.url}-${index}`} className="overflow-hidden hover:border-white/10 transition-colors">
                <div className="p-5">
                  {/* Source + Sentiment */}
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--primary)]">{article.source}</p>
                    {sentimentBadge(article.sentiment)}
                  </div>
                  {/* Title */}
                  <a href={article.url} target="_blank" rel="noreferrer" className="block">
                    <h2 className="mb-2 text-base font-bold leading-snug text-white hover:text-[var(--primary)] transition-colors">
                      {article.title}
                    </h2>
                  </a>
                  {/* Summary */}
                  {article.summary && (
                    <p className="mb-4 text-sm leading-6 text-[var(--on-surface-variant)] line-clamp-3">{article.summary}</p>
                  )}
                  {/* Footer */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--on-surface-variant)]">{formatRelativeTime(article.published_at)}</span>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-black uppercase tracking-[0.18em] text-[var(--primary)] hover:opacity-80"
                    >
                      Read →
                    </a>
                  </div>
                </div>
              </SurfaceCard>
            ))}
          </div>
        )}
      </SentinelShell>
    </ProtectedScreen>
  );
}
