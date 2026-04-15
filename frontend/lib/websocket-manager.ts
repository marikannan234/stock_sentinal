/**
 * Global WebSocket Manager (Singleton)
 * PRODUCTION-GRADE with connection states and fallback delay
 * 
 * Ensures only ONE WebSocket connection exists globally
 * Features:
 * - ✅ Connection state tracking (CONNECTING, OPEN, CLOSED)
 * - ✅ Auto-reconnect with exponential backoff
 * - ✅ 3-second fallback delay before polling starts
 * - ✅ Heartbeat/ping-pong mechanism
 * - ✅ Structured logging with [WS] prefix
 * - Message routing by type
 * - Comprehensive error handling
 * - Proper cleanup on disconnect
 */

import { config, logger, monitor } from './config';
import { useMarketStore } from './store-v2';

// Connection states (critical fix)
export const WS_STATES = {
  CONNECTING: 'CONNECTING',
  OPEN: 'OPEN',
  CLOSED: 'CLOSED',
} as const;

const POLLING_FALLBACK_DELAY = 3000; // 3 seconds - prevent rapid reconnect loops

type MessageHandler = (data: any) => void | Promise<void>;
type ConnectListener = () => void | Promise<void>;
type DisconnectListener = () => void | Promise<void>;
type ErrorListener = (error: Error) => void;

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: number;
}

interface WebSocketStatus {
  state: typeof WS_STATES[keyof typeof WS_STATES];
  connected: boolean;
  connecting: boolean;
  reconnectCount: number;
  lastMessageTime: number;
}

// ═══════════════════════════════════════════════════════════════════════════

class GlobalWebSocketManager {
  private static instance: GlobalWebSocketManager | null = null;

  private ws: WebSocket | null = null;
  private url: string;
  private state: typeof WS_STATES[keyof typeof WS_STATES] = WS_STATES.CLOSED;
  private isConnecting = false;
  private isClosed = false;
  private reconnectCount = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private fallbackDelayTimer: NodeJS.Timeout | null = null;

  private messageHandlers = new Map<string, MessageHandler>();
  private connectListeners: ConnectListener[] = [];
  private disconnectListeners: DisconnectListener[] = [];
  private errorListeners: ErrorListener[] = [];

  private lastMessageTime = Date.now();

  /**
   * Private constructor - use getInstance() instead
   */
  private constructor(url: string) {
    this.url = url;
    logger.debug('[WS] Manager initialized', url);
  }

  /**
   * Get or create singleton instance
   */
  static getInstance(url?: string): GlobalWebSocketManager {
    if (!GlobalWebSocketManager.instance) {
      if (!url) {
        throw new Error('[WS] URL required for first initialization');
      }
      GlobalWebSocketManager.instance = new GlobalWebSocketManager(url);
    }
    return GlobalWebSocketManager.instance;
  }

  /**
   * Destroy singleton (for testing or cleanup)
   */
  static destroy() {
    if (GlobalWebSocketManager.instance) {
      GlobalWebSocketManager.instance.disconnect();
      GlobalWebSocketManager.instance = null;
    }
  }

  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      logger.debug('[WS] Already connected');
      return;
    }

    if (this.isConnecting) {
      logger.debug('[WS] Connection already in progress');
      return;
    }

    this.isConnecting = true;
    this.state = WS_STATES.CONNECTING;

    try {
      logger.info(`[WS] Connecting to ${this.url}`);
      this.ws = new WebSocket(this.url);

      // Setup event handlers
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onerror = (event) => this.handleError(event);
      this.ws.onclose = () => this.handleClose();

      // Wait for connection to open (max 10 seconds)
      await Promise.race([
        new Promise<void>((resolve) => {
          const checkConnection = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
              clearInterval(checkConnection);
              resolve();
            }
          }, 100);
          setTimeout(() => clearInterval(checkConnection), 10000);
        }),
      ]);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      console.error('[WS] Connection failed:', err);
      this.handleError(err as any);
    } finally {
      this.isConnecting = false;
    }
  }

  /**
   * Disconnect and cleanup
   */
  disconnect(): void {
    logger.info('[WS] Disconnecting');
    this.isClosed = true;
    this.state = WS_STATES.CLOSED;

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // ✅ CRITICAL: Clear fallback delay timer
    if (this.fallbackDelayTimer) {
      clearTimeout(this.fallbackDelayTimer);
      this.fallbackDelayTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.messageHandlers.clear();
    this.connectListeners = [];
    this.disconnectListeners = [];
    this.errorListeners = [];
  }

  /**
   * Send message to server
   */
  send(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Not connected, cannot send message');
      return false;
    }

    try {
      const payload = JSON.stringify(message);
      this.ws.send(payload);
      this.lastMessageTime = Date.now();
      logger.debug(`[WS] Sent: ${message.type}`);
      return true;
    } catch (error) {
      console.error('[WS] Failed to send message:', error);
      return false;
    }
  }

  /**
   * Register message handler for specific type
   */
  on(type: string, handler: MessageHandler): () => void {
    this.messageHandlers.set(type, handler);
    logger.debug('[WS] Registered handler for', type);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.delete(type);
      logger.debug('[WS] Unregistered handler for', type);
    };
  }

  /**
   * Register connection listener
   */
  onConnect(listener: ConnectListener): () => void {
    this.connectListeners.push(listener);
    return () => {
      const index = this.connectListeners.indexOf(listener);
      if (index > -1) this.connectListeners.splice(index, 1);
    };
  }

  /**
   * Register disconnection listener
   */
  onDisconnect(listener: DisconnectListener): () => void {
    this.disconnectListeners.push(listener);
    return () => {
      const index = this.disconnectListeners.indexOf(listener);
      if (index > -1) this.disconnectListeners.splice(index, 1);
    };
  }

  /**
   * Register error listener
   */
  onError(listener: ErrorListener): () => void {
    this.errorListeners.push(listener);
    return () => {
      const index = this.errorListeners.indexOf(listener);
      if (index > -1) this.errorListeners.splice(index, 1);
    };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === WS_STATES.OPEN && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection status with state
   */
  getStatus(): WebSocketStatus {
    return {
      state: this.state,
      connected: this.isConnected(),
      connecting: this.isConnecting,
      reconnectCount: this.reconnectCount,
      lastMessageTime: this.lastMessageTime,
    };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Private Event Handlers
  // ─────────────────────────────────────────────────────────────────────────

  private handleOpen = async () => {
    logger.info('[WS] Connected');
    this.state = WS_STATES.OPEN;
    this.reconnectCount = 0;

    // Update store
    useMarketStore.getState().setWebSocketConnected(true);

    // Start heartbeat
    this.setupHeartbeat();

    // Notify listeners
    for (const listener of this.connectListeners) {
      try {
        await listener();
      } catch (error) {
        logger.error('[WS] Connect listener error:', error);
      }
    }
  };

  private handleMessage = async (event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.lastMessageTime = Date.now();

      logger.debug('[WS] Received:', message.type);

      // Handle pong
      if (message.type === 'pong') {
        logger.debug('[WS] Pong received');
        return;
      }

      // Route to registered handler
      const handler = this.messageHandlers.get(message.type);
      if (handler) {
        await handler(message.data);
      } else {
        logger.warn('[WS] No handler for message type:', message.type);
      }
    } catch (error) {
      logger.error('[WS] Failed to parse message:', error);
      monitor.trackError(error as Error, 'WebSocket.handleMessage');
    }
  };

  private handleError = (event: Event | Error) => {
    const error = event instanceof Error 
      ? event 
      : new Error('[WS] Connection error');
    
    logger.error('[WS] Error:', error);
    monitor.trackError(error, 'WebSocket.handleError');

    // Notify listeners
    for (const listener of this.errorListeners) {
      try {
        listener(error);
      } catch (err) {
        logger.error('[WS] Error listener failed:', err);
      }
    }
  };

  private handleClose = async () => {
    logger.info('[WS] Disconnected');
    this.state = WS_STATES.CLOSED;

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    // ✅ CRITICAL FIX: Don't immediately switch to polling
    // Add 3-second delay before fallback polling starts
    // This prevents rapid reconnect loops
    logger.info('[WS] Waiting 3 seconds before polling fallback...');
    
    // Keep WS marked as disconnected, but don't notify yet
    if (this.fallbackDelayTimer) {
      clearTimeout(this.fallbackDelayTimer);
    }

    if (!this.isClosed) {
      // Schedule the notification of disconnect after delay
      this.fallbackDelayTimer = setTimeout(() => {
        if (this.fallbackDelayTimer) {
          clearTimeout(this.fallbackDelayTimer);
          this.fallbackDelayTimer = null;
        }
        useMarketStore.getState().setWebSocketConnected(false);
      }, POLLING_FALLBACK_DELAY);
    } else {
      // If explicitly closed, don't wait
      useMarketStore.getState().setWebSocketConnected(false);
    }

    // Notify listeners
    for (const listener of this.disconnectListeners) {
      try {
        await listener();
      } catch (error) {
        logger.error('[WS] Disconnect listener error:', error);
      }
    }

    // Attempt reconnect if not explicitly closed
    if (!this.isClosed) {
      this.scheduleReconnect();
    }
  };

  private setupHeartbeat = () => {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);

    // Send ping every 30 seconds
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'ping',
          timestamp: Date.now(),
        });
      }
    }, 30000);

    logger.debug('[WS] Heartbeat started');
  };

  private scheduleReconnect = () => {
    if (this.reconnectCount >= config.WS_RECONNECT_ATTEMPTS) {
      logger.error('[WS] Max reconnect attempts reached');
      monitor.trackError(
        new Error('WebSocket max reconnect attempts exceeded'),
        'WebSocket.scheduleReconnect'
      );
      return;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    const delay = config.WS_RECONNECT_DELAY * Math.pow(2, this.reconnectCount);
    this.reconnectCount++;

    logger.info(
      `[WS] Scheduling reconnect in ${delay}ms (attempt ${this.reconnectCount}/${config.WS_RECONNECT_ATTEMPTS})`
    );

    this.reconnectTimer = setTimeout(() => {
      if (!this.isClosed) {
        void this.connect();
      }
    }, delay);
  };
}

// ═══════════════════════════════════════════════════════════════════════════

/**
 * Export singleton instance getter
 */
export function getWebSocketManager(url?: string): GlobalWebSocketManager {
  return GlobalWebSocketManager.getInstance(url);
}

/**
 * Clean up WebSocket on page unload
 */
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    GlobalWebSocketManager.destroy();
  });
}
