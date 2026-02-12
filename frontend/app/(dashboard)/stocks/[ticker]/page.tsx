"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api-client";

type StockDetails = {
  ticker: string;
  name?: string;
};

export default function StockDetailsPage() {
  const params = useParams<{ ticker: string }>();
  const [stock, setStock] = useState<StockDetails | null>(null);

  useEffect(() => {
    async function fetchStock() {
      // Placeholder: wire this to a real backend endpoint later.
      try {
        const ticker = params.ticker;
        const { data } = await api.get(`/stocks/${ticker}`);
        setStock(data);
      } catch {
        setStock({
          ticker: params.ticker,
          name: undefined,
        });
      }
    }

    if (params?.ticker) {
      fetchStock();
    }
  }, [params]);

  if (!params?.ticker) return null;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {stock?.ticker ?? params.ticker}
        </h1>
        {stock?.name && (
          <p className="text-sm text-slate-400">{stock.name}</p>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Sentiment
          </p>
          <p className="text-sm text-slate-400">
            This panel will surface aggregated FinBERT sentiment over recent
            news headlines for this symbol.
          </p>
        </Card>
        <Card className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            5-day prediction
          </p>
          <p className="text-sm text-slate-400">
            This panel will show the next 5-day Prophet/LSTM forecast, once the
            prediction API is wired.
          </p>
        </Card>
      </div>
    </div>
  );
}

