/**
 * TanStack Query keys. Every server-data query uses a key from here so that
 * mutations can invalidate by prefix (e.g. ['portfolio'] refreshes summary,
 * growth and holdings together).
 */
export const queryKeys = {
  market: {
    all: ['market'] as const,
    ribbon: () => ['market', 'ribbon'] as const,
    summary: () => ['market', 'summary'] as const,
  },
  portfolio: {
    all: ['portfolio'] as const,
    summary: () => ['portfolio', 'summary'] as const,
    holdings: () => ['portfolio', 'holdings'] as const,
    allocation: () => ['portfolio', 'allocation'] as const,
    growth: (range: string) => ['portfolio', 'growth', range] as const,
  },
  /** Executed trades; every trade invalidates this prefix. */
  trades: {
    all: ['trades'] as const,
    history: () => ['trades', 'history'] as const,
    historySummary: () => ['trades', 'history', 'summary'] as const,
  },
  symbolSearch: (query: string) => ['symbol-search', query] as const,
  news: {
    all: ['news'] as const,
    global: () => ['news', 'global'] as const,
    /** Symbol news with sentiment; outside ['stocks', symbol] because trades don't change it. */
    symbolSentiment: (symbol: string) => ['news', symbol, 'sentiment'] as const,
  },
  watchlist: {
    all: ['watchlist'] as const,
    list: () => ['watchlist', 'list'] as const,
  },
  /** The signed-in user's alert list; one entry shared by the Alerts page and the shell bell. */
  alerts: {
    all: ['alerts'] as const,
  },
  stocks: {
    /** Everything cached for one symbol, e.g. to invalidate after a trade. */
    bySymbol: (symbol: string) => ['stocks', symbol] as const,
    price: (symbol: string) => ['stocks', symbol, 'price'] as const,
    /** Quote, day stats and chart history for one range (GET /stocks/{symbol}?range=). */
    details: (symbol: string, range: string) => ['stocks', symbol, 'details', range] as const,
    indicators: (symbol: string) => ['stocks', symbol, 'indicators'] as const,
  },
};
