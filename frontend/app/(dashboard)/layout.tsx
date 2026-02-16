"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/SearchBar";

const navItems = [
  { href: "/dashboard", label: "Overview" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/watchlist", label: "Watchlist" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, logout } = useAuthStore();

  if (!token) {
    if (typeof window !== "undefined") {
      router.replace("/login");
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-56px)]">
      <aside className="hidden w-64 flex-col border-r border-slate-800/80 bg-slate-950/80 p-5 md:flex">
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
            onClick={() => {
              logout();
              router.push("/login");
            }}
          >
            Logout
          </Button>
        </div>
      </aside>
      <main className="flex-1 px-4 py-6 md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          <div className="flex items-center justify-between gap-4">
            <SearchBar />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

