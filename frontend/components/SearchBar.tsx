"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Input } from "@/components/ui/input";

type SearchResult = {
  ticker: string;
  name?: string | null;
};

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const handle = window.setTimeout(async () => {
      try {
        const { data } = await api.get<SearchResult[]>("/search", {
          params: { q },
        });
        setResults(data ?? []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => {
      window.clearTimeout(handle);
    };
  }, [query]);

  const handleSelect = (ticker: string) => {
    setQuery("");
    setResults([]);
    router.push(`/stocks/${ticker}`);
  };

  const hasResults = results.length > 0;

  return (
    <div className="relative w-full max-w-md">
      <Input
        label="Search stocks"
        placeholder="Search by ticker or company…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {(hasResults || loading) && query.trim() && (
        <div className="absolute left-0 right-0 z-30 mt-1 rounded-xl border border-slate-800 bg-slate-950/95 text-sm shadow-xl backdrop-blur">
          <ul className="max-h-72 overflow-auto py-1">
            {loading && (
              <li className="px-3 py-2 text-xs text-slate-500">
                Searching…
              </li>
            )}
            {!loading &&
              results.map((item) => (
                <li key={item.ticker}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-xs text-slate-200 transition hover:bg-slate-800/70"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleSelect(item.ticker);
                    }}
                  >
                    <span className="font-semibold">{item.ticker}</span>
                    {item.name && (
                      <span className="ml-2 flex-1 truncate text-[11px] text-slate-400">
                        {item.name}
                      </span>
                    )}
                  </button>
                </li>
              ))}
            {!loading && !hasResults && (
              <li className="px-3 py-2 text-xs text-slate-500">
                No matches.
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

