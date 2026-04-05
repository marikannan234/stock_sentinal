'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getErrorMessage, newsService } from '@/lib/api-service';
import { formatRelativeTime } from '@/lib/format';
import type { NewsArticle, NewsWithSentiment } from '@/lib/types';

export default function NewsPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [sentiment, setSentiment] = useState<NewsWithSentiment['sentiment_analysis'] | null>(null);

  async function loadGlobal() {
    try {
      setLoading(true);
      setError('');
      const data = await newsService.global(12);
      setArticles(data.articles);
      setSentiment(null);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load market news.'));
    } finally {
      setLoading(false);
    }
  }

  async function loadSymbolNews(event?: React.FormEvent) {
    event?.preventDefault();
    if (!symbol.trim()) return;

    try {
      setLoading(true);
      setError('');
      const data = await newsService.withSentiment(symbol.trim().toUpperCase(), 10);
      setArticles(data.articles);
      setSentiment(data.sentiment_analysis);
    } catch (err) {
      setError(getErrorMessage(err, `Unable to load news for ${symbol}.`));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadGlobal();
  }, []);

  return (
    <ProtectedShell>
      <AppShell
        currentPage="news"
        title="News"
        description="Global headlines and symbol-specific sentiment analysis from the live backend."
        actions={<Button variant="outline" onClick={() => void loadGlobal()}>Global Feed</Button>}
      >
        <SurfaceCard>
          <form className="flex flex-col gap-3 md:flex-row" onSubmit={loadSymbolNews}>
            <Input label="Analyze Symbol News" value={symbol} onChange={(event) => setSymbol(event.target.value)} className="md:flex-1" />
            <Button type="submit" className="md:self-end">Load Sentiment</Button>
          </form>
          {sentiment ? (
            <div className="mt-4 rounded-2xl bg-[#17161a] p-4">
              <p className="text-sm font-semibold text-white">{sentiment.sentiment_label}</p>
              <p className="mt-2 text-sm text-on-surface-variant">{sentiment.recommendation}</p>
              <p className="mt-2 text-xs text-on-surface-variant">Confidence {Math.round(sentiment.confidence * 100)}%</p>
            </div>
          ) : null}
        </SurfaceCard>
        {loading ? (
          <LoadingState label="Loading news..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadGlobal()} />
        ) : !articles.length ? (
          <EmptyState title="No news available" message="Try again in a few moments." />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
            {articles.map((article) => (
              <a
                key={article.url}
                href={article.url}
                target="_blank"
                rel="noreferrer"
                className="block"
              >
                <SurfaceCard className="h-full transition hover:border-primary/30">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-on-surface-variant">{article.source}</p>
                    <p className="text-xs text-on-surface-variant">{formatRelativeTime(article.published_at)}</p>
                  </div>
                  <h2 className="mt-4 text-lg font-bold text-white">{article.title}</h2>
                  <p className="mt-3 text-sm text-on-surface-variant">{article.summary || 'Open the article for the full details.'}</p>
                </SurfaceCard>
              </a>
            ))}
          </div>
        )}
      </AppShell>
    </ProtectedShell>
  );
}
