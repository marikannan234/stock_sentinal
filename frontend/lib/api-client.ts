import axios from "axios";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window === "undefined"
    ? "http://backend:8000/api"
    : "http://localhost:8000/api");

export const api = axios.create({
  baseURL,
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
      url.includes("/auth/forgot-password");
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

