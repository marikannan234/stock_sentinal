'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/hooks';
import { Button } from '@/components/ui/button';
import { Card, GradientCard } from '@/components/ui/card';

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden px-6 py-20 md:py-32">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-2 lg:gap-8 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <h1 className="text-5xl md:text-6xl font-bold text-slate-100 leading-tight">
                  Professional Stock Trading
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-blue-400">
                    {' '}Made Easy
                  </span>
                </h1>
                <p className="text-xl text-slate-400 max-w-xl">
                  Advanced charts, real-time alerts, technical indicators, and portfolio management.
                  Everything you need to trade smarter.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                {isAuthenticated ? (
                  <>
                    <Button asChild size="lg">
                      <Link href="/dashboard">Open Dashboard</Link>
                    </Button>
                    <Button variant="outline" size="lg" asChild>
                      <Link href="/stocks/AAPL">View Charts</Link>
                    </Button>
                  </>
                ) : (
                  <>
                    <Button asChild size="lg">
                      <Link href="/login">Get Started</Link>
                    </Button>
                    <Button variant="outline" size="lg" asChild>
                      <Link href="/register">Create Account</Link>
                    </Button>
                  </>
                )}
              </div>

              {/* Stats */}
              <div className="flex gap-8 pt-4">
                <div>
                  <p className="text-3xl font-bold text-emerald-400">100+</p>
                  <p className="text-sm text-slate-400">Stocks Tracked</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-emerald-400">5+</p>
                  <p className="text-sm text-slate-400">Technical Indicators</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-emerald-400">24/7</p>
                  <p className="text-sm text-slate-400">Real-time Alerts</p>
                </div>
              </div>
            </div>

            {/* Hero Image/Demo */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 rounded-3xl blur-3xl"></div>
              <div className="relative bg-slate-900 border border-slate-700 rounded-3xl p-8 backdrop-blur-xl">
                <div className="space-y-3">
                  <div className="h-8 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-lg w-3/4"></div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="h-24 bg-slate-800 rounded-lg"></div>
                    <div className="h-24 bg-slate-800 rounded-lg"></div>
                  </div>
                  <div className="h-48 bg-slate-800 rounded-lg"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20 bg-slate-900/50">
        <div className="mx-auto max-w-7xl space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold text-slate-100">Powerful Features</h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Everything you need for professional stock trading in one platform
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            <GradientCard gradient="emerald">
              <h3 className="text-xl font-bold text-slate-100 mb-2">📊 Advanced Charts</h3>
              <p className="text-slate-400 text-sm">
                Interactive charts with SMA, EMA, RSI and combined technical indicators.
              </p>
            </GradientCard>

            <GradientCard gradient="blue">
              <h3 className="text-xl font-bold text-slate-100 mb-2">🔔 Smart Alerts</h3>
              <p className="text-slate-400 text-sm">
                Get real-time price alerts, indicator crossovers, and trading signals.
              </p>
            </GradientCard>

            <GradientCard gradient="amber">
              <h3 className="text-xl font-bold text-slate-100 mb-2">💼 Portfolio Management</h3>
              <p className="text-slate-400 text-sm">
                Track holdings, calculate P&L, and visualize your portfolio allocation.
              </p>
            </GradientCard>

            <GradientCard gradient="red">
              <h3 className="text-xl font-bold text-slate-100 mb-2">⭐ Watchlist</h3>
              <p className="text-slate-400 text-sm">
                Monitor multiple stocks with live price updates and instant notifications.
              </p>
            </GradientCard>

            <GradientCard gradient="blue">
              <h3 className="text-xl font-bold text-slate-100 mb-2">📰 Market News</h3>
              <p className="text-slate-400 text-sm">
                Stay informed with latest market news and sentiment analysis.
              </p>
            </GradientCard>

            <GradientCard gradient="emerald">
              <h3 className="text-xl font-bold text-slate-100 mb-2">📈 Signals</h3>
              <p className="text-slate-400 text-sm">
                Strong Buy, Buy, Sell signals based on combined technical analysis.
              </p>
            </GradientCard>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-4xl text-center space-y-8">
          <h2 className="text-4xl font-bold text-slate-100">Ready to Trade Smarter?</h2>
          <p className="text-xl text-slate-400">
            Join thousands of traders using Stock Sentinel for better decision-making.
          </p>
          <Button asChild size="lg">
            <Link href={isAuthenticated ? '/dashboard' : '/register'}>
              {isAuthenticated ? 'Go to Dashboard' : 'Start Trading Today'}
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}

