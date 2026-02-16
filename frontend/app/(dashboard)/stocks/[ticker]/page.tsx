"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { useInterval } from "@/lib/useInterval";

type Quote = {
  ticker: string;
  price: number;
  change: number;
  percent_change: number;
  open: number;
  high: number;
  low: number;
  previous_close: number;
};

type PriceDataPoint = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type CandleData = {
  ticker: string;
  name: string | null;
  currency: string | null;
  period_days: number;
  data_points: PriceDataPoint[];
};

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function StockDetailsPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = (params?.ticker as string)?.toUpperCase() ?? "";

  const [quote, setQuote] = useState<Quote | null>(null);
  const [candleData, setCandleData] = useState<CandleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);

  const [portQuantity, setPortQuantity] = useState("");
  const [portPrice, setPortPrice] = useState("");
  const [portSubmitting, setPortSubmitting] = useState(false);
  const [portError, setPortError] = useState<string | null>(null);
  const [portSuccess, setPortSuccess] = useState(false);

  const fetchQuoteAndCandles = useCallback(async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    try {
      const [quoteRes, candleRes] = await Promise.all([
        api.get<Quote>(`/stock/${ticker}/quote`),
        api.get<CandleData>(`/stock/${ticker}`),
      ]);
      setQuote(quoteRes.data);
      setCandleData(candleRes.data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to load stock data.";
      setError(msg);
      setQuote(null);
      setCandleData(null);
    } finally {
      setLoading(false);
    }
  }, [ticker]);

  const fetchQuote = useCallback(async () => {
    if (!ticker) return;
    try {
      const { data } = await api.get<Quote>(`/stock/${ticker}/quote`);
      setQuote(data);
    } catch {
      // keep previous quote on transient failures
    }
  }, [ticker]);

  const fetchWatchlist = useCallback(async () => {
    try {
      const { data } = await api.get<{ tickers: string[] }>("/watchlist");
      const tickers = data?.tickers ?? [];
      setInWatchlist(tickers.map((t) => t.toUpperCase()).includes(ticker));
    } catch {
      setInWatchlist(false);
    }
  }, [ticker]);

  useEffect(() => {
    fetchQuoteAndCandles();
  }, [fetchQuoteAndCandles]);

  useInterval(() => {
    void fetchQuote();
  }, 10000);

  useEffect(() => {
    if (ticker) fetchWatchlist();
  }, [ticker, fetchWatchlist]);

  const handleAddToWatchlist = async () => {
    setWatchlistError(null);
    setWatchlistLoading(true);
    try {
      await api.post("/watchlist", { ticker });
      setInWatchlist(true);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to add to watchlist.";
      setWatchlistError(msg);
    } finally {
      setWatchlistLoading(false);
    }
  };

  const handleAddToPortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseFloat(portQuantity);
    const price = parseFloat(portPrice);
    if (!ticker || isNaN(qty) || qty <= 0 || isNaN(price) || price <= 0) {
      setPortError("Enter valid quantity and price.");
      return;
    }
    setPortError(null);
    setPortSuccess(false);
    setPortSubmitting(true);
    try {
      await api.post("/portfolio", { ticker, quantity: qty, price });
      setPortSuccess(true);
      setPortQuantity("");
      setPortPrice("");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to add to portfolio.";
      setPortError(msg);
    } finally {
      setPortSubmitting(false);
    }
  };

  if (!ticker) return null;

  const chartData =
    candleData?.data_points?.map((p) => ({
      date: formatDate(p.date),
      close: p.close,
    })) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{ticker}</h1>
          <p className="mt-1 text-sm text-slate-400">Stock details and actions</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          <span>Live · updating every 10s</span>
        </div>
      </div>

      {loading && !error && (
        <div className="space-y-4">
          <Card className="h-64 animate-pulse rounded-xl border-slate-800 bg-slate-900/40" />
          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="h-28 animate-pulse rounded-xl border-slate-800 bg-slate-900/40" />
            <Card className="h-28 animate-pulse rounded-xl border-slate-800 bg-slate-900/40" />
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && quote && (
        <>
          {/* Quote header */}
          <div className="flex flex-wrap items-baseline gap-3">
            <span className="text-3xl font-semibold tabular-nums">
              ${quote.price.toFixed(2)}
            </span>
            <span
              className={
                quote.percent_change >= 0
                  ? "text-emerald-400"
                  : "text-red-400"
              }
            >
              {quote.percent_change >= 0 ? "+" : ""}
              {quote.percent_change.toFixed(2)}%
            </span>
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <Card className="overflow-hidden">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
                30-day close price
              </p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      stroke="#475569"
                    />
                    <YAxis
                      domain={["auto", "auto"]}
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      stroke="#475569"
                      tickFormatter={(v) => `$${v.toFixed(0)}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#94a3b8" }}
                      formatter={(value: number) => [`$${value.toFixed(2)}`, "Close"]}
                      labelFormatter={(label) => label}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {/* Stock info card */}
          <Card className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Session & previous close
            </p>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-xs text-slate-500">Open</p>
                <p className="font-medium tabular-nums">${quote.open.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">High</p>
                <p className="font-medium tabular-nums">${quote.high.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Low</p>
                <p className="font-medium tabular-nums">${quote.low.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Previous close</p>
                <p className="font-medium tabular-nums">
                  ${quote.previous_close.toFixed(2)}
                </p>
              </div>
            </div>
          </Card>

          {/* Actions */}
          <div className="flex flex-wrap gap-4">
            <Card className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Watchlist
              </p>
              {inWatchlist ? (
                <p className="text-sm text-slate-400">Already in your watchlist</p>
              ) : (
                <>
                  <Button
                    onClick={handleAddToWatchlist}
                    disabled={watchlistLoading}
                  >
                    {watchlistLoading ? "Adding…" : "Add to Watchlist"}
                  </Button>
                  {watchlistError && (
                    <p className="text-xs text-red-400">{watchlistError}</p>
                  )}
                </>
              )}
            </Card>

            <Card className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Add to portfolio
              </p>
              <form
                onSubmit={handleAddToPortfolio}
                className="flex flex-wrap items-end gap-3"
              >
                <Input
                  label="Quantity"
                  type="number"
                  step="any"
                  min="0.0001"
                  placeholder="10"
                  value={portQuantity}
                  onChange={(e) => setPortQuantity(e.target.value)}
                  className="w-24"
                />
                <Input
                  label="Price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder={quote.price.toFixed(2)}
                  value={portPrice}
                  onChange={(e) => setPortPrice(e.target.value)}
                  className="w-28"
                />
                <Button type="submit" disabled={portSubmitting}>
                  {portSubmitting ? "Adding…" : "Add"}
                </Button>
              </form>
              {portError && (
                <p className="text-xs text-red-400">{portError}</p>
              )}
              {portSuccess && (
                <p className="text-xs text-emerald-400">Added to portfolio.</p>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
