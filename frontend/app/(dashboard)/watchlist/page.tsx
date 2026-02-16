"use client";

import { useCallback, useEffect, useState } from "react";
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

function WatchlistSkeleton() {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="h-[72px] animate-pulse rounded-xl border border-slate-800 bg-slate-800/40"
        />
      ))}
    </div>
  );
}

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [addTicker, setAddTicker] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const fetchWatchlist = useCallback(async () => {
    try {
      const { data } = await api.get<{ tickers: string[] }>("/watchlist");
      const tickers = data?.tickers ?? [];
      if (tickers.length === 0) {
        setWatchlist([]);
        return;
      }
      const quotes = await Promise.all(
        tickers.map((t) =>
          api.get<Quote>(`/stock/${t}/quote`).then(({ data: q }) => ({
            ticker: t,
            current_price: q?.price ?? 0,
            percent_change: q?.percent_change ?? 0,
          })),
        ),
      );
      setWatchlist(quotes);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) return;
      setWatchlist([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

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
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) return;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const msg =
        typeof detail === "string" &&
        (detail.includes("credential") || detail.includes("token") || detail.includes("unauthorized"))
          ? "Session expired. Please log in again."
          : (detail ?? "Failed to add ticker.");
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
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
          Watchlist
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Track stocks and monitor their performance.
        </p>
      </div>

      <Card className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
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
          <Link
            href="/dashboard"
            className="text-sm text-emerald-500 transition hover:text-emerald-400"
          >
            View overview
          </Link>
        </div>
        {addError && <p className="text-xs text-red-400">{addError}</p>}
        {loading ? (
          <WatchlistSkeleton />
        ) : watchlist.length === 0 ? (
          <p className="text-sm text-slate-400">
            No tickers in your watchlist. Add one above.
          </p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {watchlist.map((item) => (
              <div
                key={item.ticker}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3 transition hover:border-slate-700"
              >
                <div>
                  <Link
                    href={`/stocks/${item.ticker}`}
                    className="font-medium text-slate-100 hover:text-emerald-400"
                  >
                    {item.ticker}
                  </Link>
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
