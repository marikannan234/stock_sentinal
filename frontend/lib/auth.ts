"use client";

import { create } from "zustand";
import { authService, getErrorMessage } from "./api-service";
import type { UserProfile } from "./types";

type AuthState = {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  isHydrated: boolean;
  login: (emailOrPhone: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string, whatsappPhone?: string) => Promise<void>;
  refreshUser: () => Promise<void>;
  logout: () => void;
  clearError: () => void;
  hydrate: () => Promise<void>;
};

const TOKEN_KEY = "stocksentinel_token";

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  error: null,
  isHydrated: false,

  async hydrate() {
    if (typeof window === "undefined") {
      set({ isHydrated: true });
      return;
    }

    const token = window.localStorage.getItem(TOKEN_KEY);
    set({ token, isHydrated: true });

    if (token) {
      try {
        await get().refreshUser();
      } catch {
        get().logout();
      }
    }
  },

  async refreshUser() {
    try {
      const user = await authService.me();
      set({ user, error: null });
    } catch (error) {
      const message = getErrorMessage(error, "Unable to load your profile.");
      set({ error: message });
      throw error;
    }
  },

  async login(emailOrPhone, password) {
    try {
      set({ loading: true, error: null });
      const { access_token } = await authService.login(emailOrPhone, password);

      if (typeof window !== "undefined") {
        window.localStorage.setItem(TOKEN_KEY, access_token);
      }

      set({ token: access_token });
      await get().refreshUser();
      set({ loading: false, error: null });
    } catch (error) {
      set({
        loading: false,
        error: getErrorMessage(error, "Unable to login. Please try again."),
      });
      throw error;
    }
  },

  async register(email, password, fullName, whatsappPhone) {
    try {
      set({ loading: true, error: null });
      await authService.register(email, password, fullName, whatsappPhone);
      await get().login(email, password);
      set({ loading: false, error: null });
    } catch (error) {
      set({
        loading: false,
        error: getErrorMessage(error, "Unable to register. Please check your details."),
      });
      throw error;
    }
  },

  logout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(TOKEN_KEY);
    }
    set({ user: null, token: null, error: null });
  },

  clearError() {
    set({ error: null });
  },
}));
