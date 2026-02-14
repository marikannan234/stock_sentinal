"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";

type Holding = {
  ticker: string;
  quantity: number;
  average_price: number;
};

type HoldingWithQuote = Holding & {
  current_price: number;
  total_value: number;
  profit_loss: number;
};

type Quote = {
  ticker: string;
  price: number;
  change: number;
  percent_change: number;
};

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<HoldingWithQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [addTicker, setAddTicker] = useState("");
  const [addQuantity, setAddQuantity] = useState("");
  const [addPrice, setAddPrice] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const fetchPortfolio = async () => {
    try {
      setError(null);
      const { data: positions } = await api.get<Holding[]>("/portfolio");
      if (!positions || positions.length === 0) {
        setHoldings([]);
        return;
      }
      const withQuotes: HoldingWithQuote[] = await Promise.all(
        positions.map(async (p) => {
          try {
            const { data: quote } = await api.get<Quote>(`/stock/${p.ticker}/quote`);
            const current = quote?.price ?? p.average_price;
            const total = p.quantity * current;
            const pl = (current - p.average_price) * p.quantity;
            return {
              ...p,
              current_price: current,
              total_value: total,
              profit_loss: pl,
            };
          } catch {
            return {
              ...p,
              current_price: p.average_price,
              total_value: p.quantity * p.average_price,
              profit_loss: 0,
            };
          }
        })
      );
      setHoldings(withQuotes);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to load portfolio.";
      setError(msg);
      setHoldings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const ticker = addTicker.trim().toUpperCase();
    const qty = parseFloat(addQuantity);
    const price = parseFloat(addPrice);
    if (!ticker || isNaN(qty) || qty <= 0 || isNaN(price) || price <= 0) {
      setAddError("Please enter valid ticker, quantity, and price.");
      return;
    }
    setAddError(null);
    setAddSubmitting(true);
    try {
      await api.post("/portfolio", { ticker, quantity: qty, price });
      setAddTicker("");
      setAddQuantity("");
      setAddPrice("");
      await fetchPortfolio();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to add position.";
      setAddError(msg);
    } finally {
      setAddSubmitting(false);
    }
  };

  const handleRemove = async (ticker: string) => {
    try {
      await api.delete(`/portfolio/${ticker}`);
      await fetchPortfolio();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
        <p className="mt-1 text-sm text-slate-400">
          Overview of your holdings and current values.
        </p>
      </div>

      <Card className="space-y-4">
        <h2 className="text-sm font-semibold">Add position</h2>
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <Input
            label="Ticker"
            placeholder="e.g. AAPL"
            value={addTicker}
            onChange={(e) => setAddTicker(e.target.value)}
            className="w-24"
          />
          <Input
            label="Quantity"
            type="number"
            step="any"
            min="0.0001"
            placeholder="5"
            value={addQuantity}
            onChange={(e) => setAddQuantity(e.target.value)}
            className="w-24"
          />
          <Input
            label="Price"
            type="number"
            step="0.01"
            min="0"
            placeholder="180"
            value={addPrice}
            onChange={(e) => setAddPrice(e.target.value)}
            className="w-28"
          />
          <Button type="submit" disabled={addSubmitting}>
            Add
          </Button>
        </form>
        {addError && <p className="text-xs text-red-400">{addError}</p>}
      </Card>

      <Card className="space-y-4">
        {loading ? (
          <p className="text-sm text-slate-400">Loading portfolio…</p>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : holdings.length === 0 ? (
          <p className="text-sm text-slate-400">
            You don&apos;t have any positions yet. Add one above.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-800">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-3 py-2">Ticker</th>
                  <th className="px-3 py-2">Qty</th>
                  <th className="px-3 py-2">Avg Price</th>
                  <th className="px-3 py-2">Current Price</th>
                  <th className="px-3 py-2">Value</th>
                  <th className="px-3 py-2">P/L</th>
                  <th className="w-10 px-2 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950/40">
                {holdings.map((p) => (
                  <tr key={p.ticker}>
                    <td className="px-3 py-2 font-medium">{p.ticker}</td>
                    <td className="px-3 py-2">{p.quantity}</td>
                    <td className="px-3 py-2">${p.average_price.toFixed(2)}</td>
                    <td className="px-3 py-2">${p.current_price.toFixed(2)}</td>
                    <td className="px-3 py-2">${p.total_value.toFixed(2)}</td>
                    <td
                      className={`px-3 py-2 ${
                        p.profit_loss >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      ${p.profit_loss.toFixed(2)}
                    </td>
                    <td className="px-2 py-2">
                      <Button
                        type="button"
                        variant="ghost"
                        className="text-xs text-slate-400 hover:text-red-400"
                        onClick={() => handleRemove(p.ticker)}
                      >
                        Remove
                      </Button>
                    </td>
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
