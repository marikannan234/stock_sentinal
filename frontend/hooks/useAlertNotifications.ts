/**
 * Hook for real-time alert WebSocket notifications
 * 
 * Usage:
 *   const { isConnected } = useAlertNotifications();
 *   // Automatically handles WebSocket connection and toast notifications
 */

import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';

export const useAlertNotifications = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();
  const isConnectingRef = useRef(false);

  // Connect function - stable reference using useRef to avoid dependency cycles
  const connectRef = useRef<() => void>(() => {});

  // Initialize connect function
  connectRef.current = () => {
    // Prevent multiple connection attempts - check if already connecting or connected
    if (isConnectingRef.current) {
      console.log('Connection already in progress');
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    // Close any existing connection in CONNECTING state
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('Closing existing CONNECTING WebSocket');
      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectingRef.current = true;

    try {
      // Use the dedicated WebSocket URL from environment, or construct it
      let wsUrl = process.env.NEXT_PUBLIC_WS_URL;
      
      if (!wsUrl) {
        // Fallback: construct from API URL by replacing http with ws
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
      }
      
      wsUrl = `${wsUrl}/ws/alerts`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✅ Connected to alert notifications');
        isConnectingRef.current = false;
        wsRef.current = ws;
        
        // Clear any pending reconnection attempts
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = undefined;
        }

        // Clear any existing heartbeat interval
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Send heartbeat every 30 seconds to keep connection alive
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
            console.log('🔔 Alert received:', data);

            // Show toast notification
            toast.success(data.message || 'Alert triggered!', {
              duration: 5000,
              position: 'top-right',
              icon: '🔔',
              style: {
                background: '#10b981',
                color: '#fff',
                fontSize: '14px',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              },
            });

            // You can also trigger a sound notification here
            playAlertSound();
          } else if (data.type === 'pong') {
            console.log('💓 Heartbeat pong received');
          }
        } catch (error) {
          console.error('Error parsing alert message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        isConnectingRef.current = false;

        // Show error toast
        toast.error('Connection error with alert service', {
          duration: 3000,
          position: 'top-right',
          icon: '⚠️',
        });
      };

      ws.onclose = () => {
        console.log('⛔ Disconnected from alert notifications');
        isConnectingRef.current = false;

        // Clear heartbeat interval
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = undefined;
        }

        // Only reconnect if we haven't been manually disconnected
        if (wsRef.current === ws) {
          wsRef.current = null;
          
          // Attempt to reconnect after 3 seconds
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Attempting to reconnect to alerts...');
            connectRef.current();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Error establishing WebSocket connection:', error);
      isConnectingRef.current = false;

      // Retry connection after 3 seconds
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(() => {
        connectRef.current();
      }, 3000);
    }
  };

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connectRef.current();

    return () => {
      // Cleanup on unmount
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
    };
  }, []);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
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
    },
  };
};

/**
 * Play a subtle alert sound
 * Optional: Remove or replace with your own sound
 */
const playAlertSound = () => {
  try {
    // Create a simple beep using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Set frequency and duration for a pleasant "ding"
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
