'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function LoginPage() {
  const router = useRouter();
  const { login, error: authError, loading } = useAuthStore();

  const [formData, setFormData] = useState({ email: '', password: '', rememberMe: false });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login(formData.email, formData.password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const displayError = error || authError;
  const isLoading = loading || isSubmitting;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="text-5xl mb-2">📈</div>
          <h1 className="text-3xl font-bold text-slate-100">Stock Sentinel</h1>
          <p className="text-slate-400 mt-2">Professional Trading Platform</p>
        </div>

        {/* Login Card */}
        <Card className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-100 text-center">Welcome Back</h2>

          {displayError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.rememberMe}
                onChange={(e) => setFormData({ ...formData, rememberMe: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
              />
              <span className="text-sm text-slate-400">Remember me</span>
            </label>

            <Button isLoading={isLoading} fullWidth type="submit">
              Sign In
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-slate-900 text-slate-400">New to Stock Sentinel?</span>
            </div>
          </div>

          <Button variant="outline" fullWidth asChild>
            <Link href="/register">Create Account</Link>
          </Button>
        </Card>

        {/* Features */}
        <div className="grid gap-4 text-center">
          <div className="text-sm text-slate-400">
            <span className="block text-2xl mb-1">🚀</span>
            Advanced Charts & Indicators
          </div>
          <div className="text-sm text-slate-400">
            <span className="block text-2xl mb-1">🔔</span>
            Real-time Price Alerts
          </div>
          <div className="text-sm text-slate-400">
            <span className="block text-2xl mb-1">💼</span>
            Portfolio Management
          </div>
        </div>
      </div>
    </div>
  );
}

