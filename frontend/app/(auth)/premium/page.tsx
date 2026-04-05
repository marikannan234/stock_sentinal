'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';

export default function PremiumAuthPage() {
  const router = useRouter();
  const { login, register, error: authError, loading } = useAuthStore();
  const [isSignIn, setIsSignIn] = useState(true);

  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(loginForm.email, loginForm.password);
      router.push('/dashboard');
    } catch (err) {
      // Error handled by auth store
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(registerForm.email, registerForm.password, registerForm.name);
      // After successful registration, switch to login
      setIsSignIn(true);
      setLoginForm({ email: registerForm.email, password: '' });
    } catch (err) {
      // Error handled by auth store
    }
  };

  return (
    <div className="dark bg-surface text-on-surface font-body overflow-x-hidden">
      {/* Animated Background Decor */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-primary/5 blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/5 blur-[100px]"></div>
      </div>

      <main className="relative z-10 flex min-h-screen items-center justify-center p-4 md:p-8">
        <div className="glass-panel w-full max-w-5xl min-h-[600px] rounded-2xl border border-white/5 shadow-2xl flex flex-col md:flex-row overflow-hidden">
          {/* Branding */}
          <div className="absolute top-8 right-8 z-[110] flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
              <span className="text-white text-xl">📈</span>
            </div>
            <span className="font-bold tracking-tighter text-white uppercase text-lg">Stock Sentinel</span>
          </div>

          {/* Login Form */}
          {isSignIn && (
            <div className="flex-1 flex flex-col justify-center px-8 md:px-16 pt-24 pb-12 md:py-0 w-full animate-in fade-in slide-in-from-right-1/2">
              <div className="max-w-sm mx-auto w-full space-y-8">
                <header>
                  <h2 className="text-3xl font-black text-white uppercase tracking-tight">Sign In</h2>
                  <p className="text-on-surface-variant text-sm mt-2">Initialize your secure session</p>
                </header>

                {authError && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                    {authError}
                  </div>
                )}

                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/60 ml-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      placeholder="name@sentinel.com"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                      className="w-full bg-surface-container border border-outline-variant/20 rounded-lg px-4 py-3 text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-on-surface-variant/30"
                      required
                      disabled={loading}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center px-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/60">
                        Password
                      </label>
                      <a className="text-[10px] text-primary hover:underline font-mono" href="#">
                        Forgot?
                      </a>
                    </div>
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                      className="w-full bg-surface-container border border-outline-variant/20 rounded-lg px-4 py-3 text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-on-surface-variant/30"
                      required
                      disabled={loading}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full primary-gradient text-white py-4 rounded-lg font-bold text-xs uppercase tracking-[0.2em] shadow-xl shadow-primary/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Initializing...' : 'Initialize Session'}
                  </button>
                </form>

                <div className="md:hidden text-center pt-4">
                  <label className="text-xs text-on-surface-variant cursor-pointer" onClick={() => setIsSignIn(false)}>
                    New to the platform?{' '}
                    <span className="text-primary font-bold">Register</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Register Form */}
          {!isSignIn && (
            <div className="flex-1 flex flex-col justify-center px-8 md:px-16 pt-24 pb-12 md:py-0 w-full animate-in fade-in slide-in-from-left-1/2">
              <div className="max-w-sm mx-auto w-full space-y-8">
                <header>
                  <h2 className="text-3xl font-black text-white uppercase tracking-tight">Register</h2>
                  <p className="text-on-surface-variant text-sm mt-2">Join the Sentinel Network</p>
                </header>

                {authError && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                    {authError}
                  </div>
                )}

                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/60 ml-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      placeholder="John Doe"
                      value={registerForm.name}
                      onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                      className="w-full bg-surface-container border border-outline-variant/20 rounded-lg px-4 py-3 text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-on-surface-variant/30"
                      required
                      disabled={loading}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/60 ml-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      placeholder="name@sentinel.com"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                      className="w-full bg-surface-container border border-outline-variant/20 rounded-lg px-4 py-3 text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-on-surface-variant/30"
                      required
                      disabled={loading}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/60 ml-1">
                      Secure Password
                    </label>
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      className="w-full bg-surface-container border border-outline-variant/20 rounded-lg px-4 py-3 text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-on-surface-variant/30"
                      required
                      disabled={loading}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full primary-gradient text-white py-4 rounded-lg font-bold text-xs uppercase tracking-[0.2em] shadow-xl shadow-primary/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Creating Profile...' : 'Create Sentinel Profile'}
                  </button>
                </form>

                <div className="md:hidden text-center pt-4">
                  <label className="text-xs text-on-surface-variant cursor-pointer" onClick={() => setIsSignIn(true)}>
                    Already have an account?{' '}
                    <span className="text-primary font-bold">Login</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Overlay Panel (Desktop Only) */}
          <div className="hidden md:flex flex-1 flex-col justify-center items-center px-12 bg-gradient-to-r from-surface-container-low to-surface text-center">
            {isSignIn ? (
              <div className="max-w-xs space-y-6">
                <h2 className="text-4xl font-black text-white uppercase tracking-tighter leading-none">
                  Create your account
                </h2>
                <p className="text-on-surface-variant text-lg leading-relaxed">
                  Start tracking stocks, alerts, and AI insights. Join the elite network today.
                </p>
                <button
                  onClick={() => setIsSignIn(false)}
                  className="border-2 border-white/20 hover:bg-white/5 text-white px-10 py-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all"
                >
                  Create Account
                </button>
              </div>
            ) : (
              <div className="max-w-xs space-y-6">
                <h2 className="text-4xl font-black text-white uppercase tracking-tighter leading-none">
                  Welcome Back
                </h2>
                <p className="text-on-surface-variant text-lg leading-relaxed">
                  Track markets, monitor alerts, and manage your portfolio with precision.
                </p>
                <button
                  onClick={() => setIsSignIn(true)}
                  className="border-2 border-white/20 hover:bg-white/5 text-white px-10 py-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all"
                >
                  Back to Login
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="absolute bottom-6 left-0 w-full flex flex-col md:flex-row justify-center items-center gap-4 md:gap-8 text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant/40">
        <a className="hover:text-primary transition-colors" href="#">
          Privacy Protocol
        </a>
        <a className="hover:text-primary transition-colors" href="#">
          Terms of Engagement
        </a>
        <span className="hidden md:inline text-outline-variant/30">|</span>
        <a className="hover:text-primary transition-colors flex items-center gap-1" href="#">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
          System Status: Online
        </a>
      </footer>

      <style jsx>{`
        .glass-panel {
          background: rgba(32, 31, 34, 0.6);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .primary-gradient {
          background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        }
      `}</style>
    </div>
  );
}
