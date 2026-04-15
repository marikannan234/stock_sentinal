/**
 * Singleton WebSocket Manager for Alerts
 * Ensures only ONE global WebSocket instance exists
 * Prevents duplicate connections and reconnect loops
 */

type AlertMessage = {
  type: 'alert' | 'pong';
  message?: string;
  data?: unknown;
};

type WSManagerCallback = (message: AlertMessage) => void;

class AlertWSManager {
  private static instance: AlertWSManager | null = null;
  private ws: WebSocket | null = null;
  private url: string = '';
  private callbacks: Set<WSManagerCallback> = new Set();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private connectionAttempts = 0;
  private maxReconnectDelay = 30000; // 30 seconds

  private constructor() {
    this.url = this.buildWSUrl();
  }

  static getInstance(): AlertWSManager {
    if (!AlertWSManager.instance) {
      AlertWSManager.instance = new AlertWSManager();
    }
    return AlertWSManager.instance;
  }

  private buildWSUrl(): string {
    if (typeof window === 'undefined') return '';

    let wsUrl = process.env.NEXT_PUBLIC_WS_URL;

    if (!wsUrl) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    }

    return `${wsUrl}/ws/alerts`;
  }

  /**
   * Connect to WebSocket - safe to call multiple times
   */
  connect(): void {
    // Server-side check
    if (typeof window === 'undefined') return;

    // Already connected or connecting
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    if (this.isConnecting) return;

    // Close stale connection if in CONNECTING state
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.connectionAttempts = 0;
        this.setupHeartbeat();
        this.clearReconnectTimer();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: AlertMessage = JSON.parse(event.data);
          this.notifyCallbacks(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (event) => {
        console.error('WebSocket connection error:', event);
        this.isConnecting = false;
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.clearHeartbeat();

        // Only reconnect if this is the current connection
        if (this.ws) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect and cleanup
   */
  disconnect(): void {
    this.clearReconnectTimer();
    this.clearHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to alert messages
   */
  subscribe(callback: WSManagerCallback): () => void {
    this.callbacks.add(callback);

    // Trigger connect when first subscriber added
    if (this.callbacks.size === 1) {
      this.connect();
    }

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);

      // Disconnect if no more subscribers
      if (this.callbacks.size === 0) {
        this.disconnect();
      }
    };
  }

  /**
   * Notify all subscribers
   */
  private notifyCallbacks(message: AlertMessage): void {
    this.callbacks.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in alert callback:', error);
      }
    });
  }

  /**
   * Setup heartbeat/ping
   */
  private setupHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
          console.error('Failed to send heartbeat:', error);
        }
      }
    }, 30000); // 30 seconds
  }

  /**
   * Clear heartbeat interval
   */
  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    this.clearReconnectTimer();

    this.connectionAttempts += 1;
    // Exponential backoff: 3s, 6s, 12s, up to 30s max
    const delay = Math.min(3000 * Math.pow(2, this.connectionAttempts - 1), this.maxReconnectDelay);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Get connection status
   */
  getStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (this.isConnecting) return 'connecting';
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return 'connected';
    return 'disconnected';
  }
}

export default AlertWSManager;
