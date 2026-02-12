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
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const { data } = await api.post("/auth/login", params.toString(), {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const token = data.access_token as string;
      if (typeof window !== "undefined") {
        window.localStorage.setItem("stocksentinel_token", token);
      }

      set({
        token,
        user: { email },
        loading: false,
      });
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ?? "Unable to login. Please try again.";
      set({ error: msg, loading: false });
    }
  },

  async register(email, password, fullName) {
    try {
      set({ loading: true, error: null });
      await api.post("/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      // Auto-login after registration
      await (useAuthStore.getState().login(email, password) as any);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ??
        "Unable to register. Please check your details.";
      set({ error: msg, loading: false });
    }
  },

  logout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("stocksentinel_token");
    }
    set({ user: null, token: null });
  },
}));

