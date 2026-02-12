"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";

type PortfolioPosition = {
  ticker: string;
  quantity: number;
  average_price: number;
};

export default function PortfolioPage() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);

  useEffect(() => {
    // Placeholder: fetch positions from `/portfolio` once backend route exists.
    setPositions([]);
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
        <p className="mt-1 text-sm text-slate-400">
          Overview of your holdings and their sentiment-adjusted outlook.
        </p>
      </div>

      <Card className="space-y-4">
        {positions.length === 0 ? (
          <p className="text-sm text-slate-400">
            You don&apos;t have any positions yet. Once connected, holdings
            will appear here with sentiment and prediction overlays.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-800">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-3 py-2">Ticker</th>
                  <th className="px-3 py-2">Quantity</th>
                  <th className="px-3 py-2">Avg. Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950/40">
                {positions.map((p) => (
                  <tr key={p.ticker}>
                    <td className="px-3 py-2 font-medium">{p.ticker}</td>
                    <td className="px-3 py-2">{p.quantity}</td>
                    <td className="px-3 py-2">${p.average_price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

