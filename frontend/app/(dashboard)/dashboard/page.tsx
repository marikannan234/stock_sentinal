"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Market overview
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          High-level snapshot of sentiment and predictions for your tracked
          symbols.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Portfolio value
          </p>
          <p className="mt-2 text-2xl font-semibold">$—</p>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Overall sentiment
          </p>
          <p className="mt-2 text-2xl font-semibold">Neutral</p>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Active alerts
          </p>
          <p className="mt-2 text-2xl font-semibold">0</p>
        </Card>
      </div>

      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Tracked stocks</h2>
          <Link href="/portfolio" className="text-xs text-accent">
            View portfolio
          </Link>
        </div>
        <p className="text-sm text-slate-400">
          Once connected, this section will show key sentiment and prediction
          metrics for symbols in your portfolio.
        </p>
      </Card>
    </div>
  );
}

