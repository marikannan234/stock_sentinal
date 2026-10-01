import axios from "axios";
import { config as appConfig } from "./config";

export const api = axios.create({
  baseURL: appConfig.API_BASE_URL,
  withCredentials: false,
  timeout: appConfig.API_TIMEOUT_MS,
});

// Ensure all requests have timeout protection
api.interceptors.request.use((config) => {
  if (!config.timeout) {
    config.timeout = appConfig.API_TIMEOUT_MS;
  }
  return config;
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
    
    // 🚨 PREVENT REDIRECT LOOP: Don't redirect to /login if already there
    const isAlreadyOnLoginPage = 
      typeof window !== "undefined" && 
      (window.location.pathname.includes("/login") || window.location.pathname.includes("/register"));
    
    if (
      typeof window !== "undefined" &&
      error?.response?.status === 401 &&
      !skipRedirect &&
      !isAlreadyOnLoginPage
    ) {
      window.localStorage.removeItem("stocksentinel_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
