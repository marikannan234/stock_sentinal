"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";

type Quote = {
  ticker: string;
  price: number;
  percent_change: number;
};

type WatchlistItem = {
  ticker: string;
  current_price: number;
  percent_change: number;
};

export default function DashboardPage() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [addTicker, setAddTicker] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const fetchWatchlist = async () => {
    try {
      const { data } = await api.get<{ tickers: string[] }>("/watchlist");
      const tickers = data?.tickers ?? [];
      if (tickers.length === 0) {
        setWatchlist([]);
        return;
      }
      const withQuotes: WatchlistItem[] = await Promise.all(
        tickers.map(async (t) => {
          try {
            const { data: quote } = await api.get<Quote>(`/stock/${t}/quote`);
            return {
              ticker: t,
              current_price: quote?.price ?? 0,
              percent_change: quote?.percent_change ?? 0,
            };
          } catch {
            return { ticker: t, current_price: 0, percent_change: 0 };
          }
        })
      );
      setWatchlist(withQuotes);
    } catch {
      setWatchlist([]);
    } finally {
      setWatchlistLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAddTicker = async (e: React.FormEvent) => {
    e.preventDefault();
    const ticker = addTicker.trim().toUpperCase();
    if (!ticker) {
      setAddError("Enter a ticker.");
      return;
    }
    setAddError(null);
    setAddSubmitting(true);
    try {
      await api.post("/watchlist", { ticker });
      setAddTicker("");
      await fetchWatchlist();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to add ticker.";
      setAddError(msg);
    } finally {
      setAddSubmitting(false);
    }
  };

  const handleRemoveTicker = async (ticker: string) => {
    try {
      await api.delete(`/watchlist/${ticker}`);
      await fetchWatchlist();
    } catch {
      // ignore
    }
  };

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
          <h2 className="text-sm font-semibold">Watchlist</h2>
          <Link href="/portfolio" className="text-xs text-accent">
            View portfolio
          </Link>
        </div>
        <form onSubmit={handleAddTicker} className="flex items-end gap-2">
          <Input
            label="Add ticker"
            placeholder="e.g. AAPL"
            value={addTicker}
            onChange={(e) => setAddTicker(e.target.value)}
            className="w-32"
          />
          <Button type="submit" disabled={addSubmitting}>
            Add
          </Button>
        </form>
        {addError && <p className="text-xs text-red-400">{addError}</p>}
        {watchlistLoading ? (
          <p className="text-sm text-slate-400">Loading watchlist…</p>
        ) : watchlist.length === 0 ? (
          <p className="text-sm text-slate-400">
            No tickers in your watchlist. Add one above.
          </p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {watchlist.map((item) => (
              <div
                key={item.ticker}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2"
              >
                <div>
                  <p className="font-medium">{item.ticker}</p>
                  <p className="text-xs text-slate-400">
                    ${item.current_price.toFixed(2)}
                    <span
                      className={
                        item.percent_change >= 0
                          ? "ml-1 text-emerald-400"
                          : "ml-1 text-red-400"
                      }
                    >
                      {item.percent_change >= 0 ? "+" : ""}
                      {item.percent_change.toFixed(2)}%
                    </span>
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  className="text-xs text-slate-400 hover:text-red-400"
                  onClick={() => handleRemoveTicker(item.ticker)}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
