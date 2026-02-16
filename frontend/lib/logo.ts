const TICKER_DOMAINS: Record<string, string> = {
  AAPL: "apple.com",
  TSLA: "tesla.com",
  NVDA: "nvidia.com",
  MSFT: "microsoft.com",
  AMZN: "amazon.com",
};

export function getLogoUrl(ticker: string): string | null {
  const key = ticker.toUpperCase();
  const domain = TICKER_DOMAINS[key];
  if (!domain) return null;
  return `https://logo.clearbit.com/${domain}`;
}

