"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";

type Quote = {
  ticker: string;
  price: number;
  percent_change: number;
};

const TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"] as const;

export function StockTickerRibbon() {
  const [quotes, setQuotes] = useState<Quote[]>([]);

  const loadQuotes = useCallback(async () => {
    try {
      const results = await Promise.all(
        TICKERS.map(async (t) => {
          try {
            const { data } = await api.get<Quote>(`/stock/${t}/quote`);
            return {
              ticker: t,
              price: data?.price ?? 0,
              percent_change: data?.percent_change ?? 0,
            };
          } catch {
            return { ticker: t, price: 0, percent_change: 0 };
          }
        }),
      );
      setQuotes(results);
    } catch {
      setQuotes([]);
    }
  }, []);

  useEffect(() => {
    void loadQuotes();
    const id = window.setInterval(() => {
      void loadQuotes();
    }, 15000);

    return () => {
      window.clearInterval(id);
    };
  }, [loadQuotes]);

  if (quotes.length === 0) {
    return (
      <div className="border-b border-slate-800 bg-slate-900/95 px-4 py-1 text-xs text-slate-500">
        <span className="opacity-80">Loading market snapshot…</span>
      </div>
    );
  }

  const items = [...quotes, ...quotes]; // duplicate for seamless scroll

  return (
    <div className="border-b border-slate-800 bg-slate-900/95">
      <div className="relative w-full overflow-hidden">
        <div className="flex min-w-full items-center gap-8 whitespace-nowrap ticker-marquee px-4 py-1.5 text-xs">
          {items.map((q, idx) => {
            const isUp = q.percent_change >= 0;
            return (
              <Link
                key={`${q.ticker}-${idx}`}
                href={`/stocks/${q.ticker}`}
                className="flex items-center gap-2 text-slate-200 hover:text-emerald-400"
              >
                <span className="font-semibold">{q.ticker}</span>
                <span className="tabular-nums text-slate-300">
                  ${q.price.toFixed(2)}
                </span>
                <span className={isUp ? "text-emerald-400" : "text-red-400"}>
                  {isUp ? "+" : ""}
                  {q.percent_change.toFixed(2)}%
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

