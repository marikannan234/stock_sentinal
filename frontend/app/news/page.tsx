'use client';

import { useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, newsService } from '@/lib/api-service';
import type { LiveQuote, NewsArticle } from '@/lib/types';
import { formatRelativeTime } from '@/lib/sentinel-utils';

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([newsService.global(12), marketService.getLiveRibbon()]).then(([newsResult, ribbonResult]) => {
      if (newsResult.status === 'fulfilled') setArticles(newsResult.value.articles);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  return (
    <ProtectedScreen>
      <SentinelShell title="News Intelligence" subtitle="Live market briefings from the backend news feed." ribbon={ribbon}>
        <div className="grid gap-6 lg:grid-cols-2">
          {articles.map((article, index) => (
            <SurfaceCard key={`${article.url}-${index}`} className="overflow-hidden">
              <div className="p-6">
                <p className="mb-3 text-[10px] font-black uppercase tracking-[0.22em] text-[var(--primary)]">{article.source}</p>
                <h2 className="mb-3 text-2xl font-bold tracking-[-0.04em] text-white">{article.title}</h2>
                <p className="text-sm leading-7 text-[var(--on-surface-variant)]">{article.summary || 'Latest market briefing from the live feed.'}</p>
                <div className="mt-6 flex items-center justify-between">
                  <span className="text-xs uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">{formatRelativeTime(article.published_at)}</span>
                  <a href={article.url} target="_blank" rel="noreferrer" className="text-xs font-black uppercase tracking-[0.18em] text-[var(--primary)]">
                    Read Source
                  </a>
                </div>
              </div>
            </SurfaceCard>
          ))}
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
