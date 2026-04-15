/**
 * Clean custom hook for WebSocket alert notifications
 * Uses singleton manager to prevent duplicate connections
 * Only ONE place should use this: AlertBootstrap
 */

import { useEffect } from 'react';
import toast from 'react-hot-toast';
import AlertWSManager from '@/lib/ws-manager';

export function useAlertsWS(): void {
  useEffect(() => {
    // Server-side safety check
    if (typeof window === 'undefined') {
      return;
    }

    // Get singleton instance and subscribe
    const manager = AlertWSManager.getInstance();

    // Subscribe to alerts
    const unsubscribe = manager.subscribe((message) => {
      if (message.type === 'alert') {
        toast.success(message.message || 'Alert triggered!', {
          duration: 5000,
          position: 'top-right',
          style: {
            background: '#10b981',
            color: '#fff',
            fontSize: '14px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          },
        });

        // Play sound if available
        playAlertSound();
      }
    });

    // Cleanup: unsubscribe on unmount
    return () => {
      unsubscribe();
    };
  }, []); // Empty dependency array - only run once on mount
}

/**
 * Play alert sound notification
 */
function playAlertSound(): void {
  try {
    // Use Web Audio API if available
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Beep parameters
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    // Silently fail if audio not available
    console.debug('Alert sound not available:', error);
  }
}
