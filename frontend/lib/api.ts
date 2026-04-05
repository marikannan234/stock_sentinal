import axios from 'axios';
import { useAuthStore } from './stores';

const API_BASE = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ============ STOCK API ============
export const stockApi = {
  search: (query: string) => apiClient.get(`/search`, { params: { q: query } }),
  getPrice: (symbol: string) => apiClient.get(`/stocks/${symbol}/price`),
  getNews: (symbol?: string) => apiClient.get(`/news`, { params: { symbol } }),
};

// ============ INDICATORS API ============
export const indicatorsApi = {
  sma: (symbol: string, period: number = 20) =>
    apiClient.get(`/indicators/sma`, { params: { symbol, period } }),
  ema: (symbol: string, period: number = 20) =>
    apiClient.get(`/indicators/ema`, { params: { symbol, period } }),
  rsi: (symbol: string, period: number = 14) =>
    apiClient.get(`/indicators/rsi`, { params: { symbol, period } }),
  combined: (symbol: string) => apiClient.get(`/indicators/combined`, { params: { symbol } }),
};

// ============ SENTIMENT API ============
export const sentimentApi = {
  get: (symbol: string) => apiClient.get(`/sentiment/${symbol}`),
  getNews: (symbol: string) => apiClient.get(`/sentiment/news/${symbol}`),
};

// ============ HISTORICAL DATA API ============
export const historicalApi = {
  get: (symbol: string, days: number = 365) =>
    apiClient.get(`/historical`, { params: { symbol, days } }),
};
