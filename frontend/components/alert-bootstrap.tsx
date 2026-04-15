'use client';

/**
 * Alert notification bootstrap component.
 * Initializes alert WebSocket behavior only after the app mounts in the browser.
 * 
 * IMPORTANT: This is the ONLY place WebSocket connections should be initialized.
 * All alert notifications are handled through the singleton WebSocket manager.
 */

import { useEffect, useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useAlertsWS } from '@/hooks/useAlertsWS';

function AlertRuntime() {
  // Initialize WebSocket subscription (runs only once on mount)
  useAlertsWS();

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
          icon: <CheckCircle size={20} className="text-white" />,
        },
        error: {
          duration: 4000,
          style: {
            background: '#ef4444',
            color: '#fff',
          },
          icon: <XCircle size={20} className="text-white" />,
        },
        loading: {
          style: {
            background: '#3b82f6',
            color: '#fff',
          },
          icon: <Loader2 size={20} className="text-white animate-spin" />,
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
