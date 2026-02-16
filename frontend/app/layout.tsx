"use client";

import "./globals.css";
import Link from "next/link";
import { Inter } from "next/font/google";
import { ReactNode, useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { ProfileModal } from "@/components/ProfileModal";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function RootLayout({ children }: { children: ReactNode }) {
  const { token } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem("stocksentinel_token");
      if (stored) useAuthStore.setState({ token: stored });
    }
    setMounted(true);
  }, []);

  const isAuthenticated = mounted && !!token;

  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-slate-950 font-sans text-slate-100 antialiased">
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/95 backdrop-blur-md">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
              <Link
                href="/"
                className="text-lg font-semibold tracking-tight text-slate-100 transition hover:text-emerald-400"
              >
                <span className="text-emerald-500">Stock</span>Sentinel
              </Link>
              <nav className="flex items-center gap-6 text-sm">
                {isAuthenticated ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="text-slate-300 transition hover:text-emerald-400"
                    >
                      Dashboard
                    </Link>
                    <button
                      type="button"
                      onClick={() => setProfileOpen(true)}
                      className="text-slate-300 transition hover:text-emerald-400"
                    >
                      Profile
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      className="text-slate-300 transition hover:text-emerald-400"
                    >
                      Login
                    </Link>
                    <Link
                      href="/register"
                      className="text-slate-300 transition hover:text-emerald-400"
                    >
                      Register
                    </Link>
                  </>
                )}
              </nav>
            </div>
          </header>
          <main className="flex-1">
            {children}
          </main>
        </div>
        <ProfileModal isOpen={profileOpen} onClose={() => setProfileOpen(false)} />
      </body>
    </html>
  );
}

