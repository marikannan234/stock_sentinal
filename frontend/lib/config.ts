/**
 * Frontend configuration — the only module that reads environment variables.
 *
 * NEXT_PUBLIC_API_URL  API origin, e.g. https://api.example.com   (no /api)
 * NEXT_PUBLIC_WS_URL   WebSocket origin, e.g. wss://api.example.com (no /ws)
 *
 * NEXT_PUBLIC_* values are inlined at build time, so they must be referenced
 * literally (process.env.NEXT_PUBLIC_X) and changing them requires a rebuild.
 * next.config.mjs fails a production build when NEXT_PUBLIC_API_URL is unset.
 */

const DEV_API_URL = 'http://localhost:8000';

function toOrigin(name: string, value: string, protocols: string[]): string {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`${name} must be an absolute URL, got "${value}"`);
  }
  if (!protocols.includes(url.protocol)) {
    throw new Error(`${name} must use ${protocols.join(' or ')}, got "${value}"`);
  }
  if (url.pathname !== '/' || url.search || url.hash) {
    throw new Error(`${name} must be an origin only (no path such as /api or /ws), got "${value}"`);
  }
  return url.origin;
}

const apiOrigin = toOrigin(
  'NEXT_PUBLIC_API_URL',
  process.env.NEXT_PUBLIC_API_URL || DEV_API_URL,
  ['http:', 'https:'],
);

const wsOrigin = toOrigin(
  'NEXT_PUBLIC_WS_URL',
  process.env.NEXT_PUBLIC_WS_URL || apiOrigin.replace(/^http/, 'ws'),
  ['ws:', 'wss:'],
);

export const config = {
  /** REST base, e.g. https://api.example.com/api */
  API_BASE_URL: `${apiOrigin}/api`,
  /** WebSocket base, e.g. wss://api.example.com/ws */
  WS_BASE_URL: `${wsOrigin}/ws`,
  API_TIMEOUT_MS: 10_000,

  // Legacy values still read by lib/store-v2.ts; removed together with it.
  CACHE_TTL: 300_000,
  STORAGE_PREFIX: 'stocksentinel_',
  SYNC_ACROSS_TABS: true,
} as const;

/** Console logger; debug/info only print in development. */
const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
  debug: (...args: unknown[]) => {
    if (isDevelopment) console.log('[DEBUG]', ...args);
  },
  info: (...args: unknown[]) => {
    if (isDevelopment) console.log('[INFO]', ...args);
  },
  warn: (...args: unknown[]) => console.warn('[WARN]', ...args),
  error: (...args: unknown[]) => console.error('[ERROR]', ...args),
};
