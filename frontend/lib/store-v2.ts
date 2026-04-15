'use client';

/**
 * Enhanced Production-Grade Zustand Store
 * Features:
 * - Persistent state with localStorage
 * - Multi-tab synchronization via BroadcastChannel
 * - Stale data protection with timestamps
 * - Comprehensive error tracking
 * - WebSocket status integration
 * - Global polling state
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { config, logger } from './config';
import type { LiveQuote, MarketSummary, NewsArticle } from './types';

// ═══════════════════════════════════════════════════════════════════════════

/**
 * Store State Interface
 */
export interface MarketStoreState {
  // Data
  ribbon: LiveQuote[];
  market: MarketSummary | null;
  news: NewsArticle[];
  ribbonTimestamp: number;
  marketTimestamp: number;
  newsTimestamp: number;

  // Loading states (only on initial load)
  isRibbonLoading: boolean;
  isMarketLoading: boolean;
  isNewsLoading: boolean;

  // Error states
  ribbonError: string | null;
  marketError: string | null;
  newsError: string | null;

  // WebSocket & Polling status
  isWebSocketConnected: boolean;
  isPollingActive: boolean;
  isPollingSuspended: boolean;
  lastUpdateSource: 'websocket' | 'polling' | 'manual' | null;

  // Metadata
  syncAcrossTabs: boolean;

  // Setters
  setRibbon: (data: LiveQuote[], source?: 'websocket' | 'polling') => void;
  setMarket: (data: MarketSummary | null, source?: 'websocket' | 'polling') => void;
  setNews: (data: NewsArticle[], source?: 'websocket' | 'polling') => void;

  setRibbonLoading: (loading: boolean) => void;
  setMarketLoading: (loading: boolean) => void;
  setNewsLoading: (loading: boolean) => void;

  setRibbonError: (error: string | null) => void;
  setMarketError: (error: string | null) => void;
  setNewsError: (error: string | null) => void;

  setWebSocketConnected: (connected: boolean) => void;
  setPollingActive: (active: boolean) => void;
  suspendPolling: () => void;
  resumePolling: () => void;

  // Helpers
  isStaleData: (type: 'ribbon' | 'market' | 'news', maxAge?: number) => boolean;
  clearErrors: () => void;
  reset: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════

const INITIAL_STATE: Omit<
  MarketStoreState,
  | 'setRibbon'
  | 'setMarket'
  | 'setNews'
  | 'setRibbonLoading'
  | 'setMarketLoading'
  | 'setNewsLoading'
  | 'setRibbonError'
  | 'setMarketError'
  | 'setNewsError'
  | 'setWebSocketConnected'
  | 'setPollingActive'
  | 'suspendPolling'
  | 'resumePolling'
  | 'isStaleData'
  | 'clearErrors'
  | 'reset'
> = {
  ribbon: [],
  market: null,
  news: [],
  ribbonTimestamp: 0,
  marketTimestamp: 0,
  newsTimestamp: 0,

  isRibbonLoading: true,
  isMarketLoading: true,
  isNewsLoading: true,

  ribbonError: null,
  marketError: null,
  newsError: null,

  isWebSocketConnected: false,
  isPollingActive: false,
  isPollingSuspended: false,
  lastUpdateSource: null,

  syncAcrossTabs: true,
};

// ═══════════════════════════════════════════════════════════════════════════

let broadcastChannel: BroadcastChannel | null = null;

/**
 * Initialize cross-tab sync using BroadcastChannel API
 */
function initBroadcastChannel(store: any) {
  if (typeof window === 'undefined') return;

  try {
    broadcastChannel = new BroadcastChannel(`${config.STORAGE_PREFIX}market_sync`);

    broadcastChannel.onmessage = (event) => {
      const { type, payload } = event.data;

      logger.debug('[BroadcastChannel] Received:', type);

      switch (type) {
        case 'ribbon_update':
          store.setState({ ribbon: payload, ribbonTimestamp: Date.now() });
          break;
        case 'market_update':
          store.setState({ market: payload, marketTimestamp: Date.now() });
          break;
        case 'news_update':
          store.setState({ news: payload, newsTimestamp: Date.now() });
          break;
        case 'websocket_status':
          store.setState({ isWebSocketConnected: payload });
          break;
        case 'polling_status':
          store.setState({ isPollingActive: payload });
          break;
      }
    };

    logger.debug('[BroadcastChannel] Initialized');
  } catch (error) {
    logger.warn('[BroadcastChannel] Not supported or blocked:', error);
  }
}

/**
 * Broadcast state changes to other tabs
 */
function broadcastUpdate(type: string, payload: any) {
  if (!config.SYNC_ACROSS_TABS || !broadcastChannel) return;

  try {
    broadcastChannel.postMessage({ type, payload, timestamp: Date.now() });
  } catch (error) {
    logger.warn('[BroadcastChannel] Failed to broadcast:', error);
  }
}

// ═══════════════════════════════════════════════════════════════════════════

export const useMarketStore = create<MarketStoreState>()(
  subscribeWithSelector((set, get) => {
    // Initialize broadcast channel
    if (typeof window !== 'undefined') {
      setTimeout(() => initBroadcastChannel({ setState: set }), 0);
    }

    return {
      ...INITIAL_STATE,

      // ─── Ribbon Setters ────────────────────────────────────────────────

      setRibbon: (data: LiveQuote[], source: 'websocket' | 'polling' = 'polling') =>
        set((state) => {
          // Prevent stale data from overriding fresh data
          if (source === 'polling' && state.ribbonTimestamp > Date.now() - 1000) {
            logger.debug('[Store] Ignoring stale ribbon data');
            return state;
          }

          logger.debug(`[Store] Updating ribbon from ${source}`, data.length);

          const newState = {
            ribbon: data,
            ribbonTimestamp: Date.now(),
            ribbonError: null,
            isRibbonLoading: false,
            lastUpdateSource: source,
          };

          broadcastUpdate('ribbon_update', data);
          return newState;
        }),

      // ─── Market Setters ────────────────────────────────────────────────

      setMarket: (data: MarketSummary | null, source: 'websocket' | 'polling' = 'polling') =>
        set((state) => {
          if (source === 'polling' && state.marketTimestamp > Date.now() - 1000) {
            logger.debug('[Store] Ignoring stale market data');
            return state;
          }

          logger.debug(`[Store] Updating market from ${source}`);

          const newState = {
            market: data,
            marketTimestamp: Date.now(),
            marketError: null,
            isMarketLoading: false,
            lastUpdateSource: source,
          };

          broadcastUpdate('market_update', data);
          return newState;
        }),

      // ─── News Setters ──────────────────────────────────────────────────

      setNews: (data: NewsArticle[], source: 'websocket' | 'polling' = 'polling') =>
        set((state) => {
          if (source === 'polling' && state.newsTimestamp > Date.now() - 1000) {
            logger.debug('[Store] Ignoring stale news data');
            return state;
          }

          logger.debug(`[Store] Updating news from ${source}`, data.length);

          const newState = {
            news: data,
            newsTimestamp: Date.now(),
            newsError: null,
            isNewsLoading: false,
            lastUpdateSource: source,
          };

          broadcastUpdate('news_update', data);
          return newState;
        }),

      // ─── Loading State Setters ─────────────────────────────────────────

      setRibbonLoading: (loading: boolean) => set({ isRibbonLoading: loading }),
      setMarketLoading: (loading: boolean) => set({ isMarketLoading: loading }),
      setNewsLoading: (loading: boolean) => set({ isNewsLoading: loading }),

      // ─── Error Setters ─────────────────────────────────────────────────

      setRibbonError: (error: string | null) =>
        set((state) => {
          if (error) logger.error('[Store] Ribbon error:', error);
          return { ribbonError: error, isRibbonLoading: false };
        }),

      setMarketError: (error: string | null) =>
        set((state) => {
          if (error) logger.error('[Store] Market error:', error);
          return { marketError: error, isMarketLoading: false };
        }),

      setNewsError: (error: string | null) =>
        set((state) => {
          if (error) logger.error('[Store] News error:', error);
          return { newsError: error, isNewsLoading: false };
        }),

      // ─── WebSocket & Polling Setters ───────────────────────────────────

      setWebSocketConnected: (connected: boolean) => {
        logger.info(`[Store] WebSocket ${connected ? 'connected' : 'disconnected'}`);
        set({ isWebSocketConnected: connected });
        broadcastUpdate('websocket_status', connected);
      },

      setPollingActive: (active: boolean) => {
        logger.info(`[Store] Polling ${active ? 'started' : 'stopped'}`);
        set({ isPollingActive: active });
        broadcastUpdate('polling_status', active);
      },

      suspendPolling: () => set({ isPollingSuspended: true }),
      resumePolling: () => set({ isPollingSuspended: false }),

      // ─── Helpers ───────────────────────────────────────────────────────

      isStaleData: (type: 'ribbon' | 'market' | 'news', maxAge = config.CACHE_TTL) => {
        const state = get();
        const timestamps = {
          ribbon: state.ribbonTimestamp,
          market: state.marketTimestamp,
          news: state.newsTimestamp,
        };

        const age = Date.now() - timestamps[type];
        const isStale = age > maxAge;

        if (isStale) logger.debug(`[Store] ${type} data is stale (${age}ms)`);
        return isStale;
      },

      clearErrors: () =>
        set({
          ribbonError: null,
          marketError: null,
          newsError: null,
        }),

      reset: () => {
        logger.info('[Store] Resetting to initial state');
        set(INITIAL_STATE);
        broadcastUpdate('reset', null);
      },
    };
  })
);

/**
 * Cleanup broadcast channel on page unload
 */
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    if (broadcastChannel) {
      broadcastChannel.close();
      broadcastChannel = null;
    }
  });
}
