"use client";

import Link from "next/link";
import { ReactNode, useState, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/SearchBar";
import { StockTickerRibbon } from "@/components/StockTickerRibbon";

const navItems = [
  { href: "/dashboard", label: "Overview" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/watchlist", label: "Watchlist" },
];

function HamburgerIcon({ open }: { open: boolean }) {
  return (
    <svg
      className="h-6 w-6"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      {open ? (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M6 18L18 6M6 6l12 12"
        />
      ) : (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M4 6h16M4 12h16M4 18h16"
        />
      )}
    </svg>
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, logout } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = useCallback(() => {
    logout();
    router.push("/login");
  }, [logout, router]);

  const handleNavClick = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);

  if (!token) {
    if (typeof window !== "undefined") {
      router.replace("/login");
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-56px)]">
      {/* Mobile menu button */}
      <button
        type="button"
        className="fixed left-4 top-20 z-50 rounded-lg border border-slate-800 bg-slate-900/95 p-2 text-slate-300 transition hover:bg-slate-800 md:hidden"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        aria-label="Toggle menu"
      >
        <HamburgerIcon open={mobileMenuOpen} />
      </button>

      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-full w-64 flex-col border-r border-slate-800/80 bg-slate-950/95 p-5 transition-transform md:relative md:flex md:translate-x-0 ${
          mobileMenuOpen ? "flex translate-x-0" : "-translate-x-full"
        }`}
      >
        <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Navigation
        </p>
        <nav className="flex flex-1 flex-col gap-1 text-sm">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleNavClick}
                className={`rounded-xl px-3 py-2.5 transition ${
                  active
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-slate-800 pt-4">
          <Button
            variant="ghost"
            className="w-full justify-start text-slate-400 hover:bg-slate-800/60 hover:text-red-400"
            onClick={handleLogout}
          >
            Logout
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 px-4 py-6 md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          <StockTickerRibbon />
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <SearchBar />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

