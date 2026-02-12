"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/dashboard", label: "Overview" },
  { href: "/portfolio", label: "Portfolio" },
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
      <aside className="hidden w-60 flex-col border-r border-slate-800 bg-sidebar/90 p-4 md:flex">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Navigation
        </p>
        <nav className="flex flex-1 flex-col gap-1 text-sm">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-3 py-2 ${
                  active
                    ? "bg-slate-800 text-slate-50"
                    : "text-slate-300 hover:bg-slate-900"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <Button
          variant="ghost"
          className="mt-4 justify-start text-xs text-slate-400"
          onClick={() => {
            logout();
            router.push("/login");
          }}
        >
          Logout
        </Button>
      </aside>
      <main className="flex-1 px-4 py-6 md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          {children}
        </div>
      </main>
    </div>
  );
}

