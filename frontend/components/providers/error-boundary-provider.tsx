/**
 * Global Error Boundary Provider
 * Catches errors from entire application with graceful fallback UI
 * Features:
 * - Catches component render errors
 * - Shows user-friendly error UI
 * - Logs to monitoring system
 * - Retry capability
 * - Persists error state recovery
 */

'use client';

import React, { ReactNode } from 'react';
import { config, logger, monitor } from '@/lib/config';

interface ErrorBoundaryProviderProps {
  children: ReactNode;
}

interface ErrorState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorCount: number;
  lastErrorTime: number;
}

class ErrorBoundaryProvider extends React.Component<
  ErrorBoundaryProviderProps,
  ErrorState
> {
  constructor(props: ErrorBoundaryProviderProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      lastErrorTime: 0,
    };

    // Track unhandled promise rejections
    this.setupGlobalErrorHandlers();
  }

  /**
   * Setup global error handlers for unhandled rejections
   */
  private setupGlobalErrorHandlers() {
    if (typeof window !== 'undefined') {
      window.addEventListener('unhandledrejection', (event) => {
        logger.error('[ErrorBoundary] Unhandled rejection:', event.reason);
        monitor.trackError(
          event.reason instanceof Error 
            ? event.reason 
            : new Error(String(event.reason)),
          'unhandledRejection'
        );
      });

      window.addEventListener('error', (event) => {
        logger.error('[ErrorBoundary] Uncaught error:', event.error);
        monitor.trackError(
          event.error instanceof Error 
            ? event.error 
            : new Error(event.message),
          'uncaughtError'
        );
      });
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const now = Date.now();
    const timeSinceLastError = now - this.state.lastErrorTime;

    // Determine if this is a recurring error
    const isRecurringError = 
      this.state.error?.message === error.message && 
      timeSinceLastError < 1000;

    // Increment counter
    const newErrorCount = isRecurringError 
      ? this.state.errorCount + 1 
      : 1;

    // Log error
    logger.error('[ErrorBoundary] Caught error:', error);
    logger.debug('[ErrorBoundary] Component stack:', errorInfo.componentStack);

    // Track in monitoring
    monitor.trackError(error, 'ErrorBoundary');

    // Update state
    this.setState({
      error,
      errorInfo,
      errorCount: newErrorCount,
      lastErrorTime: now,
    });

    // If error count exceeds threshold, show critical error
    if (newErrorCount > 3) {
      logger.error('[ErrorBoundary] Too many errors, may need page reload');
      monitor.trackError(
        new Error('Critical error threshold exceeded'),
        'ErrorBoundary.criticalThreshold'
      );
    }
  }

  /**
   * Reset error state
   */
  private resetError = () => {
    logger.info('[ErrorBoundary] Resetting error state');
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      lastErrorTime: 0,
    });
  };

  /**
   * Reload page
   */
  private reloadPage = () => {
    logger.info('[ErrorBoundary] Reloading page');
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      const isDevelopment = 
        typeof process !== 'undefined' && 
        process.env.NODE_ENV === 'development';

      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
            backgroundColor: '#f3f4f6',
            padding: '20px',
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          <div
            style={{
              maxWidth: '500px',
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '32px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              textAlign: 'center',
            }}
          >
            {/* Error Icon */}
            <div
              style={{
                fontSize: '48px',
                marginBottom: '16px',
              }}
            >
              ⚠️
            </div>

            {/* Heading */}
            <h1
              style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '8px',
              }}
            >
              Something went wrong
            </h1>

            {/* Error message */}
            <p
              style={{
                fontSize: '14px',
                color: '#6b7280',
                marginBottom: '24px',
                lineHeight: '1.5',
              }}
            >
              We encountered an unexpected error. Our team has been notified.
              Please try the options below.
            </p>

            {/* Development error details */}
            {isDevelopment && this.state.error && (
              <div
                style={{
                  backgroundColor: '#fee2e2',
                  border: '1px solid #fecaca',
                  borderRadius: '6px',
                  padding: '12px',
                  marginBottom: '24px',
                  textAlign: 'left',
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              >
                <p
                  style={{
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    color: '#991b1b',
                    margin: '0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  <strong>Error:</strong> {this.state.error.message}
                  {'\n\n'}
                  <strong>Stack:</strong> {this.state.errorInfo?.componentStack}
                </p>
              </div>
            )}

            {/* Error count indicator */}
            {this.state.errorCount > 1 && (
              <p
                style={{
                  fontSize: '12px',
                  color: '#dc2626',
                  marginBottom: '24px',
                }}
              >
                Error count: {this.state.errorCount}
                {this.state.errorCount > 3 && 
                  ' (Page reload recommended)'}
              </p>
            )}

            {/* Action buttons */}
            <div
              style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'center',
              }}
            >
              <button
                onClick={this.resetError}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseOver={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#2563eb';
                }}
                onMouseOut={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#3b82f6';
                }}
              >
                Try Again
              </button>

              <button
                onClick={this.reloadPage}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseOver={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#4b5563';
                }}
                onMouseOut={(e) => {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#6b7280';
                }}
              >
                Reload Page
              </button>
            </div>

            {/* Support message */}
            <p
              style={{
                fontSize: '12px',
                color: '#9ca3af',
                marginTop: '24px',
                marginBottom: '0',
              }}
            >
              If the problem persists, please contact support.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundaryProvider;
