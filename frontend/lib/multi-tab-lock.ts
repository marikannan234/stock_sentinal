/**
 * Multi-Tab Lock System
 * Ensures only primary tab performs polling
 * Uses localStorage + BroadcastChannel for coordination
 * 
 * How it works:
 * 1. Each tab generates a unique ID
 * 2. First tab to write to localStorage becomes "primary"
 * 3. Other tabs detect primary and suppress polling
 * 4. If primary closes, lock expires and other tab takes over
 * 5. Uses BroadcastChannel for instant notifications
 */

import React from 'react';
import { config, logger } from './config';

const LOCK_KEY = 'stock-sentinel:tab-lock';
const LOCK_TTL = 5000; // 5 seconds
const CHECK_INTERVAL = 1000; // Check every 1 second

interface TabLock {
  tabId: string;
  timestamp: number;
}

class MultiTabLock {
  private tabId: string;
  private isPrimary = false;
  private checkInterval: NodeJS.Timeout | null = null;
  private broadcast: BroadcastChannel | null = null;
  private listeners: Set<(isPrimary: boolean) => void> = new Set();

  constructor() {
    // Generate unique tab ID
    this.tabId = `tab-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    logger.debug('[Lock] Tab ID:', this.tabId);

    // Initialize BroadcastChannel if available
    if (config.SYNC_ACROSS_TABS && typeof BroadcastChannel !== 'undefined') {
      try {
        this.broadcast = new BroadcastChannel('stock-sentinel:lock');
        this.broadcast.onmessage = (event) => this.handleBroadcast(event);
      } catch (error) {
        logger.warn('[Lock] BroadcastChannel unavailable:', error);
      }
    }

    // Start lock checking
    this.startLockCheck();

    // Cleanup on unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.cleanup());
    }
  }

  /**
   * Try to acquire or maintain lock
   */
  private startLockCheck() {
    this.checkInterval = setInterval(() => {
      try {
        const locked = this.checkLock();
        this.setPrimary(locked);
      } catch (error) {
        logger.error('[Lock] Check failed:', error);
      }
    }, CHECK_INTERVAL);
  }

  /**
   * Check if current tab has lock
   */
  private checkLock(): boolean {
    try {
      const stored = localStorage.getItem(LOCK_KEY);
      const now = Date.now();

      if (!stored) {
        // No lock exists, try to acquire it
        return this.tryAcquireLock();
      }

      const lock: TabLock = JSON.parse(stored);

      // Check if lock is expired
      if (now - lock.timestamp > LOCK_TTL) {
        logger.debug('[Lock] Previous lock expired, attempting to acquire');
        return this.tryAcquireLock();
      }

      // Check if we already hold the lock
      if (lock.tabId === this.tabId) {
        logger.debug('[Lock] Refreshing lock');
        this.writeLock();
        return true;
      }

      // Another tab has the lock
      logger.debug('[Lock] Another tab is primary:', lock.tabId);
      return false;
    } catch (error) {
      logger.error('[Lock] Parse error:', error);
      // On error, try to acquire lock
      return this.tryAcquireLock();
    }
  }

  /**
   * Try to acquire lock with verification (prevents race condition)
   * CRITICAL: Reads back what was written to ensure we got the lock
   */
  private tryAcquireLock(): boolean {
    try {
      this.writeLock();
      
      // CRITICAL RACE FIX: Verify we actually got the lock
      // Read back immediately to ensure another tab didn't overwrite us
      const stored = localStorage.getItem(LOCK_KEY);
      if (stored) {
        const lock: TabLock = JSON.parse(stored);
        // Only consider lock acquired if our tabId matches
        if (lock.tabId === this.tabId) {
          logger.debug('[Lock] Lock acquired successfully');
          return true;
        } else {
          logger.debug('[Lock] Lost race condition - another tab acquired lock');
          return false;
        }
      }
      return false;
    } catch (error) {
      logger.error('[Lock] Failed to acquire lock:', error);
      return false;
    }
  }

  /**
   * Write lock to localStorage
   */
  private writeLock() {
    try {
      const lock: TabLock = {
        tabId: this.tabId,
        timestamp: Date.now(),
      };
      localStorage.setItem(LOCK_KEY, JSON.stringify(lock));
    } catch (error) {
      logger.error('[Lock] Failed to write lock:', error);
    }
  }

  /**
   * Update primary status and notify listeners
   */
  private setPrimary(isPrimary: boolean) {
    if (this.isPrimary === isPrimary) return;

    this.isPrimary = isPrimary;
    logger.info('[Lock]', isPrimary ? 'PRIMARY TAB' : 'SECONDARY TAB');

    // Broadcast to other tabs
    if (this.broadcast) {
      this.broadcast.postMessage({
        type: 'lock-status-changed',
        isPrimary,
        tabId: this.tabId,
      });
    }

    // Notify listeners
    for (const listener of this.listeners) {
      listener(isPrimary);
    }
  }

  /**
   * Handle broadcast message from other tabs
   */
  private handleBroadcast = (event: MessageEvent) => {
    const { type, isPrimary, tabId } = event.data;

    if (type === 'lock-status-changed') {
      logger.debug('[Lock] Received status from tab:', tabId, isPrimary);
      // We might need to re-check our status
      setTimeout(() => {
        try {
          const locked = this.checkLock();
          this.setPrimary(locked);
        } catch (error) {
          logger.error('[Lock] Re-check failed:', error);
        }
      }, 100);
    }
  };

  /**
   * Listen for primary status changes
   */
  onPrimaryStatusChange(listener: (isPrimary: boolean) => void): () => void {
    this.listeners.add(listener);
    // Immediately call with current status
    listener(this.isPrimary);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Check primary status without callback
   */
  getIsPrimary(): boolean {
    return this.isPrimary;
  }

  /**
   * Get current tab ID
   */
  getTabId(): string {
    return this.tabId;
  }

  /**
   * Cleanup
   */
  cleanup() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.broadcast) {
      this.broadcast.close();
      this.broadcast = null;
    }

    this.listeners.clear();

    // Remove lock if we're primary
    if (this.isPrimary) {
      try {
        localStorage.removeItem(LOCK_KEY);
      } catch (error) {
        logger.debug('[Lock] Failed to clear lock:', error);
      }
    }

    logger.debug('[Lock] Cleaned up');
  }
}

// ═══════════════════════════════════════════════════════════════════════════

// Singleton instance
let instance: MultiTabLock | null = null;

/**
 * Get or create lock instance
 */
export function getTabLock(): MultiTabLock {
  if (!instance) {
    instance = new MultiTabLock();
  }
  return instance;
}

/**
 * Hook to use tab lock in React
 */
export function useTabLock(): boolean {
  const [isPrimary, setIsPrimary] = React.useState(false);

  React.useEffect(() => {
    const lock = getTabLock();
    return lock.onPrimaryStatusChange(setIsPrimary);
  }, []);

  return isPrimary;
}
