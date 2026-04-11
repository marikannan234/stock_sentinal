'use client';

/**
 * Alert notification bootstrap component.
 * Initializes alert WebSocket behavior only after the app mounts in the browser.
 */

import { useEffect, useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAlertNotifications } from '@/hooks/useAlertNotifications';

function AlertRuntime() {
  useAlertNotifications();

  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      gutter={8}
      toastOptions={{
        duration: 4000,
        style: {
          background: '#363636',
          color: '#fff',
          fontSize: '14px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
        },
        success: {
          duration: 5000,
          style: {
            background: '#10b981',
            color: '#fff',
          },
          icon: '!',
        },
        error: {
          duration: 4000,
          style: {
            background: '#ef4444',
            color: '#fff',
          },
          icon: 'x',
        },
        loading: {
          style: {
            background: '#3b82f6',
            color: '#fff',
          },
          icon: '...',
        },
      }}
    />
  );
}

export function AlertBootstrap() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted ? <AlertRuntime /> : null;
}
