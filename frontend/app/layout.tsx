"use client";

import "./globals.css";
import Link from "next/link";
import { ReactNode } from "react";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-slate-100">
        <div className="flex min-h-screen flex-col">
          <header className="border-b border-slate-800 bg-sidebar/80 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
              <Link href="/" className="text-lg font-semibold tracking-tight">
                <span className="text-accent">Stock</span>Sentinel
              </Link>
              <nav className="flex gap-4 text-sm text-slate-300">
                <Link href="/login">Login</Link>
                <Link href="/register">Register</Link>
              </nav>
            </div>
          </header>
          <main className="flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

