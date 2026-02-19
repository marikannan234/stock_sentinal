const LOGO_MAP: Record<string, string> = {
  AAPL: "apple.com",
  TSLA: "tesla.com",
  NVDA: "nvidia.com",
  MSFT: "microsoft.com",
  AMZN: "amazon.com",
};

export function getLogoUrl(ticker: string): string | null {
  const key = ticker.toUpperCase();
  const domain = LOGO_MAP[key];
  if (!domain) return null;
  return `https://logo.clearbit.com/${domain}`;
}

