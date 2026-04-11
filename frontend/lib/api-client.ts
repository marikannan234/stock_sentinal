import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Simple request deduplication cache to prevent multiple requests for the same URL
const requestCache = new Map<string, { timestamp: number; promise: Promise<any> }>();
const CACHE_TIME_MS = 2000; // Keep cache for 2 seconds to handle rapid tab switches

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: false,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("stocksentinel_token");
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = typeof error?.config?.url === "string" ? error.config.url : "";
    const skipRedirect =
      url.includes("/auth/login") ||
      url.includes("/auth/login-json") ||
      url.includes("/auth/forgot-password") ||
      url.includes("/indicators") ||
      url.includes("/news") ||
      url.includes("/stocks");
    if (
      typeof window !== "undefined" &&
      error?.response?.status === 401 &&
      !skipRedirect
    ) {
      window.localStorage.removeItem("stocksentinel_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// Add GET request deduplication for tab focus optimization
const originalGet = api.get.bind(api);
api.get = ((url: string, config?: any) => {
  // Only deduplicate GET requests
  const cacheKey = `${url}${JSON.stringify(config?.params || {})}`;
  const cached = requestCache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TIME_MS) {
    // Return cached promise if still fresh (prevents duplicate requests on tab focus)
    return cached.promise;
  }
  
  // Make new request and cache it
  const promise = originalGet(url, config);
  requestCache.set(cacheKey, { timestamp: Date.now(), promise });
  
  // Clean up old cache entries
  if (requestCache.size > 50) {
    const now = Date.now();
    for (const [key, value] of requestCache.entries()) {
      if (now - value.timestamp > CACHE_TIME_MS * 2) {
        requestCache.delete(key);
      }
    }
  }
  
  return promise;
}) as typeof api.get;

