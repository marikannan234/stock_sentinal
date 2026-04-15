/**
 * Production Configuration System
 * Centralizes all environment variables and application config
 * Supports dev, staging, and production environments
 */

interface AppConfig {
  API_BASE_URL: string;
  WS_BASE_URL: string;
  API_TIMEOUT: number;
  POLLING_INTERVAL: number;
  POLLING_ENABLED: boolean;
  WS_ENABLED: boolean;
  WS_RECONNECT_ATTEMPTS: number;
  WS_RECONNECT_DELAY: number;
  CACHE_TTL: number;
  MAX_RETRIES: number;
  RETRY_DELAY: number;
  ENABLE_LOGGING: boolean;
  ENABLE_MONITORING: boolean;
  STORAGE_PREFIX: string;
  SYNC_ACROSS_TABS: boolean;
  PAUSE_POLLING_ON_HIDDEN: boolean;
}

/**
 * Get configuration based on environment
 */
function getConfig(): AppConfig {
  const isProduction = process.env.NODE_ENV === 'production';
  const isDevelopment = process.env.NODE_ENV === 'development';

  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsBaseUrl =
    process.env.NEXT_PUBLIC_WS_URL ||
    (apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://'));

  return {
    // API Configuration
    API_BASE_URL: apiBaseUrl,
    WS_BASE_URL: wsBaseUrl,
    API_TIMEOUT: isDevelopment ? 30000 : isProduction ? 10000 : 15000,

    // Polling Configuration
    POLLING_INTERVAL: 5000, // 5 seconds
    POLLING_ENABLED: !isProduction, // Disabled in production if WS works
    WS_ENABLED: true,

    // WebSocket Configuration
    WS_RECONNECT_ATTEMPTS: 5,
    WS_RECONNECT_DELAY: 1000, // 1 second, will exponentially backoff

    // Caching Configuration
    CACHE_TTL: 300000, // 5 minutes
    MAX_RETRIES: isDevelopment ? 3 : 2,
    RETRY_DELAY: 1000,

    // Feature Flags
    ENABLE_LOGGING: isDevelopment,
    ENABLE_MONITORING: isProduction,
    STORAGE_PREFIX: 'stocksentinel_',
    SYNC_ACROSS_TABS: true,
    PAUSE_POLLING_ON_HIDDEN: true,
  };
}

export const config = getConfig();

/**
 * Logger utility (respects config)
 */
export const logger = {
  debug: (...args: any[]) => {
    if (config.ENABLE_LOGGING) console.log('[DEBUG]', ...args);
  },
  info: (...args: any[]) => {
    if (config.ENABLE_LOGGING) console.log('[INFO]', ...args);
  },
  warn: (...args: any[]) => console.warn('[WARN]', ...args),
  error: (...args: any[]) => console.error('[ERROR]', ...args),
};

/**
 * Monitoring utility (sends to backend in production)
 */
export const monitor = {
  trackError: (error: Error, context: string) => {
    if (config.ENABLE_MONITORING) {
      logger.error(`[${context}]`, error);
      // In production, send to error tracking service
      // await fetch('/api/monitoring/error', { method: 'POST', body: JSON.stringify({ error, context, timestamp: Date.now() }) })
    }
  },
  trackPerformance: (metric: string, duration: number) => {
    if (config.ENABLE_MONITORING) {
      logger.debug(`Performance: ${metric} took ${duration}ms`);
    }
  },
};
