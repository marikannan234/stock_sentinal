'use client';

/**
 * Data fetching hooks for reusable, cacheable API calls
 * Prevents duplicate fetches and provides consistent loading states
 */

import { useEffect, useState, useRef } from 'react';
import { useMarketStore } from '@/lib/store';
import { marketService, portfolioService, newsService } from '@/lib/api-service';
import type { LiveQuote, MarketSummary, NewsArticle, PortfolioSummary } from '@/lib/types';

/**
 * Hook: useRibbonData
 * Reads ribbon from global store, optionally returns fresh cached data
 */
export function useRibbonData() {
  const ribbon = useMarketStore((state) => state.ribbon);
  const ribbonLoading = useMarketStore((state) => state.isRibbonLoading);
  const ribbonError = useMarketStore((state) => state.ribbonError);

  return { ribbon, ribbonLoading, ribbonError };
}

/**
 * Hook: useMarketData
 * Reads market from global store
 */
export function useMarketData() {
  const market = useMarketStore((state) => state.market);
  const marketLoading = useMarketStore((state) => state.isMarketLoading);
  const marketError = useMarketStore((state) => state.marketError);

  return { market, marketLoading, marketError };
}

/**
 * Hook: useNewsData
 * Reads cached news from store, with optional refetch capability
 */
export function useNewsData(limit: number = 10) {
  const news = useMarketStore((state) => state.news);
  const newsLoading = useMarketStore((state) => state.isNewsLoading);
  const newsError = useMarketStore((state) => state.newsError);
  const setNews = useMarketStore((state) => state.setNews);
  const [isRefetching, setIsRefetching] = useState(false);

  const refetch = async () => {
    setIsRefetching(true);
    try {
      const response = await newsService.global(limit);
      const freshNews = Array.isArray(response)
        ? response
        : [];
      setNews(freshNews);
    } catch (error) {
      console.warn('Failed to refetch news:', error);
    } finally {
      setIsRefetching(false);
    }
  };

  return { news, newsLoading, newsError, isRefetching, refetch };
}

/**
 * Hook: usePortfolioSummary
 * Fetches and caches portfolio data locally (not global)
 */
export function usePortfolioSummary() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<{ data: PortfolioSummary; timestamp: number } | null>(null);
  const CACHE_TTL = 5000; // 5 seconds

  const fetch = async (skipCache = false) => {
    // Check cache first
    if (!skipCache && cacheRef.current && Date.now() - cacheRef.current.timestamp < CACHE_TTL) {
      setSummary(cacheRef.current.data);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await portfolioService.summary();
      cacheRef.current = { data, timestamp: Date.now() };
      setSummary(data);
      setError(null);
    } catch (err) {
      console.warn('Failed to fetch portfolio summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio');
    } finally {
      setLoading(false);
    }
  };

  return { summary, loading, error, fetch };
}

/**
 * Hook: useCachedData
 * Generic hook for caching any data with TTL support
 */
export function useCachedData<T>(
  fetchFn: () => Promise<T>,
  options: {
    ttl?: number;
    initialData?: T;
    onError?: (error: Error) => void;
  } = {}
) {
  const { ttl = 5000, initialData, onError } = options;
  const [data, setData] = useState<T | null>(initialData ?? null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cacheRef = useRef<{ data: T; timestamp: number } | null>(null);

  const fetch = async (skipCache = false) => {
    // Check cache first
    if (!skipCache && cacheRef.current && Date.now() - cacheRef.current.timestamp < ttl) {
      setData(cacheRef.current.data);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const result = await fetchFn();
      cacheRef.current = { data: result, timestamp: Date.now() };
      setData(result);
      setError(null);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetch();
  }, []);

  return { data, loading, error, fetch };
}
