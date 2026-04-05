import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// ============ AUTH STORE ============
interface AuthState {
  user: {
    id: string;
    email: string;
    name: string;
  } | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  setUser: (user: AuthState['user']) => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });
          const data = await response.json();
          set({
            user: { id: data.user_id, email: data.email, name: data.name },
            token: data.access_token,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },
      register: async (email: string, password: string, name: string) => {
        set({ isLoading: true });
        try {
          const response = await fetch('http://localhost:8000/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name }),
          });
          const data = await response.json();
          set({
            user: { id: data.user_id, email: data.email, name: data.name },
            token: data.access_token,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },
      logout: () => {
        set({ user: null, token: null });
        localStorage.removeItem('stocksentinel_auth');
      },
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
    }),
    {
      name: 'stocksentinel_auth',
    }
  )
);

// ============ WATCHLIST STORE ============
export interface WatchlistStock {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: string;
}

interface WatchlistState {
  stocks: WatchlistStock[];
  isLoading: boolean;
  addStock: (symbol: string) => Promise<void>;
  removeStock: (symbol: string) => void;
  updatePrices: (stocks: WatchlistStock[]) => void;
  fetchWatchlist: () => Promise<void>;
}

export const useWatchlistStore = create<WatchlistState>()(
  devtools((set) => ({
    stocks: [],
    isLoading: false,
    addStock: async (symbol: string) => {
      set({ isLoading: true });
      try {
        const response = await fetch(`http://localhost:8000/api/watchlist/${symbol}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        if (response.ok) {
          set((state) => ({
            stocks: [...state.stocks, { id: symbol, symbol, name: symbol, price: 0, change: 0, changePercent: 0, timestamp: new Date().toISOString() }],
            isLoading: false,
          }));
        }
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    removeStock: (symbol: string) => {
      set((state) => ({
        stocks: state.stocks.filter((s) => s.symbol !== symbol),
      }));
    },
    updatePrices: (stocks: WatchlistStock[]) => {
      set({ stocks });
    },
    fetchWatchlist: async () => {
      set({ isLoading: true });
      try {
        const response = await fetch('http://localhost:8000/api/watchlist', {
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        const data = await response.json();
        const safeStocks = Array.isArray(data) ? data : [];
        set({ stocks: safeStocks, isLoading: false });
      } catch (error) {
        set({ isLoading: false, stocks: [] });
        throw error;
      }
    },
  }))
);

// ============ ALERTS STORE ============
export interface Alert {
  id: string;
  symbol: string;
  type: 'PRICE' | 'SMA' | 'EMA' | 'RSI' | 'COMBINED';
  targetValue: number;
  condition: '>' | '<' | '=' | '!=' | '>=' | '<=';
  isActive: boolean;
  triggered: boolean;
  createdAt: string;
  triggeredAt?: string;
}

interface AlertsState {
  alerts: Alert[];
  isLoading: boolean;
  createAlert: (alert: Omit<Alert, 'id' | 'createdAt' | 'triggered'>) => Promise<void>;
  deleteAlert: (id: string) => Promise<void>;
  toggleAlert: (id: string) => Promise<void>;
  fetchAlerts: () => Promise<void>;
}

export const useAlertsStore = create<AlertsState>()(
  devtools((set) => ({
    alerts: [],
    isLoading: false,
    createAlert: async (alert) => {
      set({ isLoading: true });
      try {
        const response = await fetch('http://localhost:8000/api/alerts', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(alert),
        });
        const data = await response.json();
        set((state) => ({
          alerts: [...state.alerts, data],
          isLoading: false,
        }));
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    deleteAlert: async (id) => {
      try {
        await fetch(`http://localhost:8000/api/alerts/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        set((state) => ({
          alerts: state.alerts.filter((a) => a.id !== id),
        }));
      } catch (error) {
        throw error;
      }
    },
    toggleAlert: async (id) => {
      try {
        const response = await fetch(`http://localhost:8000/api/alerts/${id}/toggle`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        const data = await response.json();
        set((state) => ({
          alerts: state.alerts.map((a) => (a.id === id ? data : a)),
        }));
      } catch (error) {
        throw error;
      }
    },
    fetchAlerts: async () => {
      set({ isLoading: true });
      try {
        const response = await fetch('http://localhost:8000/api/alerts', {
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        const data = await response.json();
        const safeAlerts = Array.isArray(data) ? data : [];
        set({ alerts: safeAlerts, isLoading: false });
      } catch (error) {
        set({ isLoading: false, alerts: [] });
        throw error;
      }
    },
  }))
);

// ============ PORTFOLIO STORE ============
export interface PortfolioHolding {
  id: string;
  symbol: string;
  quantity: number;
  buyPrice: number;
  currentPrice: number;
  invested: number;
  currentValue: number;
  gainLoss: number;
  gainLossPercent: number;
}

interface PortfolioState {
  holdings: PortfolioHolding[];
  totalInvested: number;
  totalValue: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  dayChange: number;
  dayChangePercent: number;
  isLoading: boolean;
  addHolding: (symbol: string, quantity: number, buyPrice: number) => Promise<void>;
  removeHolding: (id: string) => Promise<void>;
  updateHolding: (id: string, quantity: number, buyPrice: number) => Promise<void>;
  fetchPortfolio: () => Promise<void>;
}

export const usePortfolioStore = create<PortfolioState>()(
  devtools((set) => ({
    holdings: [],
    totalInvested: 0,
    totalValue: 0,
    totalGainLoss: 0,
    totalGainLossPercent: 0,
    dayChange: 0,
    dayChangePercent: 0,
    isLoading: false,
    addHolding: async (symbol: string, quantity: number, buyPrice: number) => {
      set({ isLoading: true });
      try {
        const response = await fetch('http://localhost:8000/api/portfolio', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ symbol, quantity, buy_price: buyPrice }),
        });
        const data = await response.json();
        set((state) => ({
          holdings: [...state.holdings, data],
          isLoading: false,
        }));
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    removeHolding: async (id) => {
      try {
        await fetch(`http://localhost:8000/api/portfolio/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        set((state) => ({
          holdings: state.holdings.filter((h) => h.id !== id),
        }));
      } catch (error) {
        throw error;
      }
    },
    updateHolding: async (id, quantity, buyPrice) => {
      try {
        const response = await fetch(`http://localhost:8000/api/portfolio/${id}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ quantity, buy_price: buyPrice }),
        });
        const data = await response.json();
        set((state) => ({
          holdings: state.holdings.map((h) => (h.id === id ? data : h)),
        }));
      } catch (error) {
        throw error;
      }
    },
    fetchPortfolio: async () => {
      set({ isLoading: true });
      try {
        const response = await fetch('http://localhost:8000/api/portfolio', {
          headers: {
            'Authorization': `Bearer ${useAuthStore.getState().token}`,
          },
        });
        const data = await response.json();
        const safeHoldings = Array.isArray(data) ? data : [];
        const totalInvested = safeHoldings.reduce((sum: number, h: PortfolioHolding) => sum + h.invested, 0);
        const totalValue = safeHoldings.reduce((sum: number, h: PortfolioHolding) => sum + h.currentValue, 0);
        const totalGainLoss = totalValue - totalInvested;
        const totalGainLossPercent = totalInvested > 0 ? (totalGainLoss / totalInvested) * 100 : 0;

        set({
          holdings: safeHoldings,
          totalInvested,
          totalValue,
          totalGainLoss,
          totalGainLossPercent,
          isLoading: false,
        });
      } catch (error) {
        set({ isLoading: false, holdings: [] });
        throw error;
      }
    },
  }))
);

// ============ UI STORE ============
interface UIState {
  sidebarOpen: boolean;
  theme: 'dark' | 'light';
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'dark',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'stocksentinel_ui',
    }
  )
);
