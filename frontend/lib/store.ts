'use client';

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

/**
 * Global market data store using Zustand
 * Shared across all components to prevent duplicate polling
 * Features:
 * - Single source of truth for market data
 * - Sidebar selector for efficient re-renders
 * - Timestamp tracking to prevent stale data override
 */

export interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
}

export interface MarketSummary {
  market_time: string;
  top_gainers: Array<{
    symbol: string;
    price: number;
    change_percent: number;
    volume: number;
  }>;
  top_losers: Array<{
    symbol: string;
    price: number;
    change_percent: number;
    volume: number;
  }>;
  most_active: Array<{
    symbol: string;
    price: number;
    change_percent: number;
    volume: number;
  }>;
}

export interface NewsArticle {
  title: string;
  source: string;
  url: string;
  summary?: string;
  image?: string;
  published_at?: string;
}

interface MarketState {
  // Live ribbon/movers
  ribbon: LiveQuote[];
  ribbonUpdatedAt: number;
  setRibbon: (data: LiveQuote[]) => void;

  // Market summary
  market: MarketSummary | null;
  marketUpdatedAt: number;
  setMarket: (data: MarketSummary | null) => void;

  // News
  news: NewsArticle[];
  newsUpdatedAt: number;
  setNews: (data: NewsArticle[]) => void;

  // Loading states (only on initial load)
  isRibbonLoading: boolean;
  setRibbonLoading: (loading: boolean) => void;

  isMarketLoading: boolean;
  setMarketLoading: (loading: boolean) => void;

  isNewsLoading: boolean;
  setNewsLoading: (loading: boolean) => void;

  // Polling control
  isPollingSuspended: boolean;
  suspendPolling: () => void;
  resumePolling: () => void;

  // Error tracking
  ribbonError: string | null;
  marketError: string | null;
  newsError: string | null;
  setRibbonError: (error: string | null) => void;
  setMarketError: (error: string | null) => void;
  setNewsError: (error: string | null) => void;

  // Reset all
  reset: () => void;
}

const initialState = {
  ribbon: [],
  ribbonUpdatedAt: 0,
  market: null,
  marketUpdatedAt: 0,
  news: [],
  newsUpdatedAt: 0,
  isRibbonLoading: true,
  isMarketLoading: true,
  isNewsLoading: true,
  isPollingSuspended: false,
  ribbonError: null,
  marketError: null,
  newsError: null,
};

export const useMarketStore = create<MarketState>()(
  subscribeWithSelector((set) => ({
    ...initialState,

    setRibbon: (data) =>
      set((state) => {
        // Prevent stale data from overriding fresh data
        if (Date.now() <= state.ribbonUpdatedAt) return state;
        return {
          ribbon: data,
          ribbonUpdatedAt: Date.now(),
          ribbonError: null,
        };
      }),

    setMarket: (data) =>
      set((state) => {
        if (Date.now() <= state.marketUpdatedAt) return state;
        return {
          market: data,
          marketUpdatedAt: Date.now(),
          marketError: null,
        };
      }),

    setNews: (data) =>
      set((state) => {
        if (Date.now() <= state.newsUpdatedAt) return state;
        return {
          news: data,
          newsUpdatedAt: Date.now(),
          newsError: null,
        };
      }),

    setRibbonLoading: (loading) => set({ isRibbonLoading: loading }),
    setMarketLoading: (loading) => set({ isMarketLoading: loading }),
    setNewsLoading: (loading) => set({ isNewsLoading: loading }),

    setRibbonError: (error) => set({ ribbonError: error }),
    setMarketError: (error) => set({ marketError: error }),
    setNewsError: (error) => set({ newsError: error }),

    suspendPolling: () => set({ isPollingSuspended: true }),
    resumePolling: () => set({ isPollingSuspended: false }),

    reset: () => set(initialState),
  })),
);

/**
 * Subscribe to specific market data without triggering re-renders
 * Usage: store.subscribe(
 *   (state) => state.ribbon,
 *   (ribbon) => { console.log('Ribbon updated') }
 * )
 */
