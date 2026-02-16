"use client";

import { create } from "zustand";
import { api } from "./api-client";

type User = {
  email: string;
  full_name?: string | null;
};

type AuthState = {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token:
    typeof window !== "undefined"
      ? window.localStorage.getItem("stocksentinel_token")
      : null,
  loading: false,
  error: null,

  async login(email, password) {
    try {
      set({ loading: true, error: null });
      const { data } = await api.post("/auth/login-json", { email, password });

      const token = data.access_token as string;
      if (typeof window !== "undefined") {
        window.localStorage.setItem("stocksentinel_token", token);
      }

      set({
        token,
        user: { email },
        loading: false,
        error: null,
      });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string | { msg?: string }[] } }; message?: string };
      const d = e?.response?.data?.detail;
      let msg: string;
      if (d !== undefined && d !== null) {
        msg = Array.isArray(d)
          ? d.map((x) => (typeof x === "object" && x?.msg ? x.msg : String(x))).join(", ")
          : typeof d === "string"
            ? d
            : "Unable to login. Please try again.";
      } else {
        msg = e?.message === "Network Error"
          ? "Cannot reach server. Check that the backend is running and CORS is configured."
          : "Unable to login. Please try again.";
      }
      set({ error: msg, loading: false });
    }
  },

  async register(email, password, fullName) {
    try {
      set({ loading: true, error: null });
      const body: { email: string; password: string; full_name?: string } = { email, password };
      if (fullName && fullName.trim()) body.full_name = fullName.trim();
      await api.post("/auth/register", body);
      set({ loading: false, error: null });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string | { msg?: string }[] } }; message?: string };
      const d = e?.response?.data?.detail;
      let msg: string;
      if (d !== undefined && d !== null) {
        msg = Array.isArray(d)
          ? d.map((x) => (typeof x === "object" && x?.msg ? x.msg : String(x))).join(", ")
          : typeof d === "string"
            ? d
            : "Unable to register. Please check your details.";
      } else {
        msg = e?.message === "Network Error"
          ? "Cannot reach server. Check that the backend is running and CORS is configured."
          : "Unable to register. Please check your details.";
      }
      set({ error: msg, loading: false });
    }
  },

  logout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("stocksentinel_token");
    }
    set({ user: null, token: null, error: null });
  },

  clearError() {
    set({ error: null });
  },
}));

