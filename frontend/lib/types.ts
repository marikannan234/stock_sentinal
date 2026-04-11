export type UserProfile = {
  id: number;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type UserSettings = {
  id: number;
  user_id: number;
  email_notifications: boolean;
  dark_mode: boolean;
  preferred_currency: string;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type LiveQuote = {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
};

export type LiveRibbon = {
  stocks: LiveQuote[];
  total_count: number;
  timestamp: string;
};

export type MarketMover = {
  symbol: string;
  price: number;
  change_percent: number;
  volume: number;
  market_cap?: string | null;
};

export type MarketSummary = {
  market_time: string;
  top_gainers: MarketMover[];
  top_losers: MarketMover[];
  most_active: MarketMover[];
  market_status: string;
};

export type StockIndicatorSet = {
  sma_20?: number | null;
  sma_50?: number | null;
  sma_200?: number | null;
  ema_12?: number | null;
  ema_26?: number | null;
  rsi?: number | null;
  macd?: number | null;
  bollinger_upper?: number | null;
  bollinger_lower?: number | null;
  bollinger_middle?: number | null;
};

export type HistoricalPoint = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type StockDetails = {
  symbol: string;
  current_price: number;
  day_change: number;
  day_change_percent: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  market_cap?: string | null;
  dividend_yield?: number | null;
  pe_ratio?: number | null;
  indicators: StockIndicatorSet;
  historical_data: HistoricalPoint[];
  timestamp: string;
};

export type CombinedIndicators = {
  symbol: string;
  sma: { sma: number };
  ema: { ema: number };
  rsi: { rsi: number };
};

export type NewsArticle = {
  title: string;
  source: string;
  url: string;
  summary?: string | null;
  image?: string | null;
  published_at?: string | null;
  sentiment?: string;
  sentiment_score?: number;
  sentiment_confidence?: number;
};

export type NewsResponse = {
  articles: NewsArticle[];
  count: number;
};

export type NewsWithSentiment = {
  articles: NewsArticle[];
  sentiment_analysis: {
    sentiment_score: number;
    sentiment_label: string;
    recommendation: string;
    confidence: number;
    analysis_count: number;
  };
  count: number;
};

export type PortfolioHolding = {
  ticker: string;
  quantity: number;
  average_price: number;
  current_price?: number | null;
  current_value?: number | null;
  invested_amount?: number | null;
  pl_amount?: number | null;
  pl_percent?: number | null;
  day_change?: number | null;
  day_change_percent?: number | null;
  name?: string | null;
  asset_class?: string | null;
};

export type PortfolioSummary = {
  total_invested: number;
  current_value: number;
  total_pl: number;
  percent_pl: number;
  day_pl: number;
  day_percent: number;
  buying_power: number;
};

export type PortfolioAllocation = {
  category: string;
  value: number;
  percent: number;
};

export type PortfolioAllocationResponse = {
  total_value: number;
  allocations: PortfolioAllocation[];
};

export type PortfolioGrowthPoint = {
  date: string;
  value: number;
};

export type WatchlistResponse = {
  tickers: string[];
};

export type AlertItem = {
  id: number;
  user_id: number;
  stock_symbol: string;
  condition?: string | null;
  target_value?: number | null;
  alert_type: string;
  sma_period?: number | null;
  ema_period?: number | null;
  rsi_period?: number | null;
  is_active: boolean;
  created_at: string;
  triggered_at?: string | null;
  last_price?: number | null;
};

export type SupportTicket = {
  id: number;
  user_id: number;
  subject: string;
  message: string;
  status: string;
  priority: string;
  response?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
};

export type Trade = {
  id: number;
  user_id: number;
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  trade_type: string;
  status: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  executed_at?: string | null;
};

export type TradeHistoryItem = {
  id: number;
  user_id: number;
  trade_id?: number | null;
  symbol: string;
  quantity: number;
  entry_price: number;
  exit_price?: number | null;
  trade_type: string;
  profit_loss?: number | null;
  profit_loss_percent?: number | null;
  duration_minutes?: number | null;
  notes?: string | null;
  created_at: string;
  closed_at?: string | null;
};

export type TradeHistorySummary = {
  total_trades: number;
  win_rate: number;
  net_profit: number;
  avg_execution: number | null;
};

export type SymbolSearchItem = {
  ticker: string;
  name?: string | null;
};
