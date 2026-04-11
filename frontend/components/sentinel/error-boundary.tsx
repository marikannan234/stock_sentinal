'use client';

import React, { ReactNode } from 'react';
import { SurfaceCard } from './primitives';
import { Icon } from './primitives';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  retry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback ? (
        this.props.fallback(this.state.error || new Error('Unknown error'), this.retry)
      ) : (
        <SurfaceCard className="m-6 flex flex-col items-center justify-center gap-4 rounded-2xl border border-tertiary/20 bg-[rgba(220,73,68,0.08)] p-8">
          <Icon name="error_outline" className="text-4xl text-tertiary" />
          <div className="text-center">
            <h2 className="mb-2 text-lg font-bold text-white">Unable to Load Content</h2>
            <p className="mb-4 text-sm text-[var(--on-surface-variant)]">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
          </div>
          <button
            onClick={this.retry}
            className="rounded-xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-6 py-2.5 text-sm font-bold text-[var(--on-primary)]"
          >
            Try Again
          </button>
        </SurfaceCard>
      );
    }

    return this.props.children;
  }
}
