'use client';

import { api } from './api-client';
import type {
  AlertItem,
  LiveQuote,
  LiveRibbon,
  MarketSummary,
  NewsResponse,
  NewsWithSentiment,
  PortfolioHolding,
  PortfolioSummary,
  PortfolioAllocationResponse,
  PortfolioGrowthPoint,
  StockDetails,
  SupportTicket,
  SymbolSearchItem,
  Trade,
  TradeHistoryItem,
  TradeHistorySummary,
  CombinedIndicators,
  UserProfile,
  UserSettings,
  WatchlistResponse,
} from './types';

type LoginResponse = {
  access_token: string;
  token_type?: string;
};

export function getErrorMessage(error: unknown, fallback = 'Something went wrong.') {
  const axiosError = error as {
    response?: { data?: { detail?: unknown; message?: string } };
    message?: string;
    code?: string;
  };

  // Axios network errors do not have a response object (backend down, CORS blocked, DNS issues).
  if (!axiosError?.response) {
    if (axiosError?.code === 'ECONNABORTED') {
      return 'Request timed out. Verify backend API is running and reachable.';
    }
    if (axiosError?.message?.toLowerCase().includes('network')) {
      return 'Network error: cannot reach API. Check backend status, API URL, and CORS settings.';
    }
  }

  const detail = axiosError?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'object' && item && 'msg' in item ? String((item as { msg?: string }).msg) : String(item)))
      .join(', ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  if (typeof axiosError?.response?.data?.message === 'string') {
    return axiosError.response.data.message;
  }
  if (axiosError?.message) {
    return axiosError.message;
  }
  return fallback;
}

export const authService = {
  async login(emailOrPhone: string, password: string) {
    const { data } = await api.post<LoginResponse>('/auth/login-json', {
      email: emailOrPhone.includes('@') ? emailOrPhone : null,
      phone: !emailOrPhone.includes('@') ? emailOrPhone : null,
      password,
    });
    return data;
  },
  async register(email: string, password: string, fullName?: string, whatsappPhone?: string) {
    const payload: { email: string; password: string; full_name?: string; whatsapp_phone?: string } = { email, password };
    if (fullName?.trim()) payload.full_name = fullName.trim();
    if (whatsappPhone?.trim()) payload.whatsapp_phone = whatsappPhone.trim();
    const { data } = await api.post<UserProfile>('/auth/register', payload);
    return data;
  },
  async me() {
    const { data } = await api.get<UserProfile>('/auth/me');
    return data;
  },
  async updateMe(fullName?: string) {
    const { data } = await api.patch<UserProfile>('/auth/me', { full_name: fullName?.trim() || null });
    return data;
  },
};

export const marketService = {
  async getLiveRibbon() {
    const { data } = await api.get<LiveRibbon>('/stocks/live/quotes');
    return data;
  },
  async getMarketSummary() {
    const { data } = await api.get<MarketSummary>('/stocks/market-summary/overview');
    return data;
  },
  async getStockDetails(symbol: string, timeRange: string) {
    const { data } = await api.get<StockDetails>(`/stocks/${symbol}`, { params: { range: timeRange } });
    return data;
  },
  async getStockPrice(symbol: string) {
    const { data } = await api.get<LiveQuote>(`/stocks/${symbol}/price`);
    return data;
  },
  async search(query: string) {
    const { data } = await api.get<SymbolSearchItem[]>('/search', { params: { q: query } });
    return data;
  },
};

export const indicatorService = {
  async combined(symbol: string) {
    const { data } = await api.get<CombinedIndicators>('/indicators/combined', { params: { symbol } });
    return data;
  },
};

export const newsService = {
  async global(limit = 12) {
    const { data } = await api.get<NewsResponse>('/news', { params: { limit } });
    return data;
  },
  async bySymbol(symbol: string, limit = 12) {
    const { data } = await api.get<NewsResponse>(`/news/${symbol}`, { params: { limit } });
    return data;
  },
  async withSentiment(symbol: string, limit = 12) {
    const { data } = await api.get<NewsWithSentiment>(`/news/${symbol}/sentiment`, { params: { limit } });
    return data;
  },
};

export const portfolioService = {
  async list() {
    const { data } = await api.get<PortfolioHolding[]>('/portfolio');
    return data;
  },
  async summary() {
    const { data } = await api.get<PortfolioSummary>('/portfolio/summary');
    return data;
  },
  async add(ticker: string, quantity: number, price: number) {
    const { data } = await api.post<PortfolioHolding[]>('/portfolio', { ticker, quantity, price });
    return data;
  },
  async allocation() {
    const { data } = await api.get<PortfolioAllocationResponse>('/portfolio/allocation');
    return data;
  },
  async growth(range: '1d' | '1w' | '1m' | '1y') {
    const { data } = await api.get<PortfolioGrowthPoint[]>('/portfolio/growth', { params: { range } });
    return data;
  },
  async remove(ticker: string) {
    const { data } = await api.delete<PortfolioHolding[]>(`/portfolio/${ticker}`);
    return data;
  },
};

export const watchlistService = {
  async list() {
    const { data } = await api.get<WatchlistResponse>('/watchlist');
    return data;
  },
  async add(ticker: string) {
    const { data } = await api.post<WatchlistResponse>('/watchlist', { ticker });
    return data;
  },
  async remove(ticker: string) {
    const { data } = await api.delete<WatchlistResponse>(`/watchlist/${ticker}`);
    return data;
  },
};

export const alertService = {
  async list() {
    const { data } = await api.get<AlertItem[]>('/alerts');
    return data;
  },
  async create(payload: {
    stock_symbol: string;
    condition?: string;
    target_value?: number;
    alert_type?: string;
    sma_period?: number;
    ema_period?: number;
    rsi_period?: number;
  }) {
    const { data } = await api.post<AlertItem>('/alerts', payload);
    return data;
  },
  async update(id: number, isActive: boolean) {
    const { data } = await api.patch<AlertItem>(`/alerts/${id}`, { is_active: isActive });
    return data;
  },
  async remove(id: number) {
    await api.delete(`/alerts/${id}`);
  },
};

export const profileService = {
  async getProfile() {
    const { data } = await api.get<UserProfile>('/user/profile');
    return data;
  },
  async updateProfile(fullName: string) {
    const { data } = await api.put<UserProfile>('/user/profile', { full_name: fullName || null });
    return data;
  },
  async getSettings() {
    const { data } = await api.get<UserSettings>('/user/settings');
    return data;
  },
  async updateSettings(payload: Partial<Omit<UserSettings, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) {
    const { data } = await api.put<UserSettings>('/user/settings', payload);
    return data;
  },
};

export const supportService = {
  async create(payload: { subject: string; message: string; priority: string }) {
    const { data } = await api.post<SupportTicket>('/support/ticket', payload);
    return data;
  },
  async list() {
    const { data } = await api.get<SupportTicket[]>('/support/tickets');
    return data;
  },
  async update(id: number, payload: { status?: string; response?: string; priority?: string }) {
    const { data } = await api.put<SupportTicket>(`/support/ticket/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    await api.delete(`/support/ticket/${id}`);
  },
};

export const tradeService = {
  async list(statusFilter?: string, symbolFilter?: string) {
    const { data } = await api.get<Trade[]>('/trade/', { params: { status_filter: statusFilter, symbol_filter: symbolFilter } });
    return data;
  },
  async create(payload: { symbol: string; quantity: number; entry_price: number; trade_type: string; notes?: string }) {
    const { data } = await api.post<Trade>('/trade/', payload);
    return data;
  },
  async update(id: number, payload: { current_price?: number; status?: string; notes?: string }) {
    const { data } = await api.put<Trade>(`/trade/${id}`, payload);
    return data;
  },
  async close(id: number, exitPrice: number) {
    const { data } = await api.post<TradeHistoryItem>(`/trade/${id}/close`, null, { params: { exit_price: exitPrice } });
    return data;
  },
  async history(symbolFilter?: string) {
    const { data } = await api.get<TradeHistoryItem[]>('/trade/history/list', { params: { symbol_filter: symbolFilter } });
    return data;
  },
  async historySummary() {
    const { data } = await api.get<TradeHistorySummary>('/trade/history/summary');
    return data;
  },
  async summary() {
    const { data } = await api.get<TradeHistorySummary>('/trade/summary/stats');
    return data;
  },
};
