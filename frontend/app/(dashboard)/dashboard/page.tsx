"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { getLogoUrl } from "@/lib/logo";
import { useInterval } from "@/lib/useInterval";

type Quote = {
  ticker: string;
  price: number;
  percent_change: number;
};

type PortfolioSummary = {
  total_invested: number;
  current_value: number;
  total_pl: number;
  percent_pl: number;
};

type OverallSentiment = "bullish" | "neutral" | "bearish";

type SentimentResponse = {
  ticker: string;
  overall_sentiment: OverallSentiment;
  score: number;
  articles: Array<{
    title: string;
    sentiment: "positive" | "neutral" | "negative";
    score: number;
  }>;
};

type WatchlistItem = {
  ticker: string;
  current_price: number;
  percent_change: number;
  overall_sentiment?: OverallSentiment;
};

type PopularStock = {
  ticker: string;
  price: number;
  percent_change: number;
};

const POPULAR_TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"] as const;

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

export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [addTicker, setAddTicker] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const [popular, setPopular] = useState<PopularStock[]>([]);
  const [popularLoading, setPopularLoading] = useState(true);

  const money = (value: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value);

  const fetchSummary = useCallback(async () => {
    try {
      setSummaryError(null);
      const { data } = await api.get<PortfolioSummary>("/portfolio/summary");
      setSummary(data ?? null);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) return;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const msg =
        typeof detail === "string" &&
        (detail.includes("credential") || detail.includes("token") || detail.includes("unauthorized"))
          ? "Session expired. Please log in again."
          : (detail ?? "Failed to load portfolio summary.");
      setSummary(null);
      setSummaryError(msg);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  const fetchWatchlist = useCallback(async () => {
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
            const [quoteRes, sentimentRes] = await Promise.allSettled([
              api.get<Quote>(`/stock/${t}/quote`),
              api.get<SentimentResponse>(`/sentiment/${t}`),
            ]);

            const quote =
              quoteRes.status === "fulfilled" ? quoteRes.value.data : undefined;
            const sentiment =
              sentimentRes.status === "fulfilled"
                ? sentimentRes.value.data
                : undefined;
            return {
              ticker: t,
              current_price: quote?.price ?? 0,
              percent_change: quote?.percent_change ?? 0,
              overall_sentiment: sentiment?.overall_sentiment,
            };
          } catch {
            return { ticker: t, current_price: 0, percent_change: 0 };
          }
        }),
      );
      setWatchlist(withQuotes);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) return;
      setWatchlist([]);
    } finally {
      setWatchlistLoading(false);
    }
  }, []);

  const fetchPopular = useCallback(async () => {
    try {
      const items: PopularStock[] = await Promise.all(
        POPULAR_TICKERS.map(async (t) => {
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
      setPopular(items);
    } finally {
      setPopularLoading(false);
    }
  }, []);

  const sentimentBadge = (s?: OverallSentiment) => {
    const label = (s ?? "neutral").toUpperCase();
    const cls =
      s === "bullish"
        ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
        : s === "bearish"
          ? "bg-red-500/15 text-red-300 border-red-500/30"
          : "bg-slate-500/15 text-slate-300 border-slate-500/30";
    return (
      <span
        className={`ml-2 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}
      >
        {label}
      </span>
    );
  };

  useEffect(() => {
    fetchSummary();
    fetchWatchlist();
    fetchPopular();
  }, [fetchSummary, fetchWatchlist, fetchPopular]);

  useInterval(() => {
    void fetchSummary();
    void fetchWatchlist();
    void fetchPopular();
  }, 10000);

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
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
              Market overview
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              High-level snapshot of sentiment and predictions for your tracked
              symbols.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
            <span>Live · updating every 10s</span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Portfolio value
          </p>
          {summaryLoading ? (
            <div className="mt-2 h-7 w-32 animate-pulse rounded bg-slate-800/40" />
          ) : summaryError ? (
            <p className="mt-2 text-sm text-red-400">{summaryError}</p>
          ) : (
            <>
              <p className="mt-2 text-2xl font-semibold text-slate-100">
                {money(summary?.current_value ?? 0)}
              </p>
              <p
                className={`mt-1 text-xs ${
                  (summary?.total_pl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {(summary?.total_pl ?? 0) >= 0 ? "+" : ""}
                {money(summary?.total_pl ?? 0)} (
                {(summary?.percent_pl ?? 0) >= 0 ? "+" : ""}
                {(summary?.percent_pl ?? 0).toFixed(2)}%)
              </p>
            </>
          )}
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Overall sentiment
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">Neutral</p>
        </Card>
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Active alerts
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">0</p>
        </Card>
      </div>

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-100">Watchlist</h2>
          <Link href="/watchlist" className="text-xs text-emerald-500 hover:text-emerald-400">
            View watchlist
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
                  {sentimentBadge(item.overall_sentiment)}
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

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-100">Popular stocks</h2>
        </div>
        {popularLoading ? (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="h-[72px] animate-pulse rounded-xl border border-slate-800 bg-slate-900/40"
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {popular.map((stock) => {
              const logo = getLogoUrl(stock.ticker);
              const isUp = stock.percent_change >= 0;
              return (
                <Link
                  key={stock.ticker}
                  href={`/stocks/${stock.ticker}`}
                  className="group rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3 transition hover:border-emerald-500/60 hover:bg-slate-900"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      {logo && (
                        <span className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-slate-800 bg-slate-900/80">
                          <img
                            src={logo}
                            alt={`${stock.ticker} logo`}
                            className="h-6 w-6 object-contain"
                          />
                        </span>
                      )}
                      <div>
                        <p className="text-sm font-semibold text-slate-100">
                          {stock.ticker}
                        </p>
                        <p className="text-xs text-slate-400">
                          ${stock.price.toFixed(2)}
                          <span
                            className={
                              isUp ? "ml-1 text-emerald-400" : "ml-1 text-red-400"
                            }
                          >
                            {isUp ? "+" : ""}
                            {stock.percent_change.toFixed(2)}%
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
