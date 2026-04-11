'use client';

/**
 * Alert notification bootstrap component
 * Initializes WebSocket connection for real-time alert notifications
 * and sets up the toast notification system.
 * 
 * Should be placed in the root layout to ensure alerts work globally.
 */

import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAlertNotifications } from '@/hooks/useAlertNotifications';

export function AlertBootstrap() {
  // Initialize WebSocket connection
  useAlertNotifications();

  return (
    <>
      {/* Toast container for alert notifications */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        toastOptions={{
          // Default options
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
            fontSize: '14px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          },

          // Default options for specific types
          success: {
            duration: 5000,
            style: {
              background: '#10b981',
              color: '#fff',
            },
            icon: '🔔',
          },
          error: {
            duration: 4000,
            style: {
              background: '#ef4444',
              color: '#fff',
            },
            icon: '❌',
          },
          loading: {
            style: {
              background: '#3b82f6',
              color: '#fff',
            },
            icon: '⏳',
          },
        }}
      />
    </>
  );
}
