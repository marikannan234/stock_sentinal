/**
 * Hook for real-time alert WebSocket notifications.
 * Browser-only behavior is deferred until after mount.
 */

import { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';

export const useAlertNotifications = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval>>();
  const isConnectingRef = useRef(false);
  const connectRef = useRef<() => void>(() => {});
  const [isConnected, setIsConnected] = useState(false);

  connectRef.current = () => {
    if (typeof window === 'undefined') {
      return;
    }

    if (isConnectingRef.current) {
      console.log('Connection already in progress');
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('Closing existing CONNECTING WebSocket');
      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectingRef.current = true;

    try {
      let wsUrl = process.env.NEXT_PUBLIC_WS_URL;

      if (!wsUrl) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
      }

      wsUrl = `${wsUrl}/ws/alerts`;

      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);

      // CRITICAL: Add connection timeout (Issue #8)
      // If connection doesn't open within 10s, close and retry
      const connectionTimeoutRef = (typeof global !== 'undefined' ? global : window).setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.warn('WebSocket connection timeout, closing...');
          ws.close();
        }
      }, 10000);

      ws.onopen = () => {
        clearTimeout(connectionTimeoutRef);
        console.log('Connected to alert notifications');
        isConnectingRef.current = false;
        setIsConnected(true);
        wsRef.current = ws;

        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = undefined;
        }

        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            try {
              ws.send(JSON.stringify({ type: 'ping' }));
            } catch (err) {
              console.error('Failed to send heartbeat:', err);
            }
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'alert') {
            console.log('Alert received:', data);

            toast.success(data.message || 'Alert triggered!', {
              duration: 5000,
              position: 'top-right',
              icon: '!',
              style: {
                background: '#10b981',
                color: '#fff',
                fontSize: '14px',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              },
            });

            playAlertSound();
          } else if (data.type === 'pong') {
            console.log('Heartbeat pong received');
          }
        } catch (error) {
          console.error('Error parsing alert message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnectingRef.current = false;
        setIsConnected(false);

        // Clear heartbeat on error to prevent orphaned interval
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = undefined;
        }

        toast.error('Connection error with alert service', {
          duration: 3000,
          position: 'top-right',
          icon: '!',
        });
      };

      ws.onclose = () => {
        console.log('Disconnected from alert notifications');
        isConnectingRef.current = false;
        setIsConnected(false);

        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = undefined;
        }

        if (wsRef.current === ws) {
          wsRef.current = null;

          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect to alerts...');
            connectRef.current();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Error establishing WebSocket connection:', error);
      isConnectingRef.current = false;
      setIsConnected(false);

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        connectRef.current();
      }, 3000);
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    connectRef.current();

    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = undefined;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = undefined;
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      isConnectingRef.current = false;
      setIsConnected(false);
    };
  }, []);

  return {
    isConnected,
    connect: () => connectRef.current(),
    disconnect: () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = undefined;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = undefined;
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      isConnectingRef.current = false;
      setIsConnected(false);
    },
  };
};

const playAlertSound = () => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    const audioContext = new (window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    console.debug('Could not play alert sound:', error);
  }
};
