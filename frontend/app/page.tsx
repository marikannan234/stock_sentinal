'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Activity,
  ArrowRight,
  BellRing,
  CheckCircle2,
  ChartNoAxesCombined,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';
import { useAuthStore } from '@/lib/auth';

const features = [
  {
    icon: ChartNoAxesCombined,
    title: 'A portfolio with context',
    description: 'See invested capital, priced market value, returns, allocation, and when a quote is missing—without pretending incomplete data is complete.',
    number: '01',
  },
  {
    icon: Activity,
    title: 'News signals, not noise',
    description: 'Review market headlines alongside a transparent sentiment summary. Follow the story behind the move instead of chasing a number.',
    number: '02',
  },
  {
    icon: BellRing,
    title: 'Alerts that respect your plan',
    description: 'Set price and indicator alerts for the stocks you follow, then keep your decisions consistent with your own thesis.',
    number: '03',
  },
  {
    icon: Target,
    title: 'Practice before you commit',
    description: 'Use paper trading to test entries and exits, review trade history, and learn from your process without placing real-money orders.',
    number: '04',
  },
];

export default function HomePage() {
  const router = useRouter();
  const { token, isHydrated } = useAuthStore();

  useEffect(() => {
    if (isHydrated && token) router.replace('/dashboard');
  }, [isHydrated, token, router]);

  if (!isHydrated || token) return null;

  return (
    <main className="min-h-screen overflow-hidden bg-[#080b12] text-white">
      <div className="pointer-events-none fixed inset-0" aria-hidden="true">
        <div className="absolute -top-56 left-[42%] h-[540px] w-[540px] rounded-full bg-blue-500/[0.12] blur-[130px]" />
        <div className="absolute right-[-180px] top-[520px] h-[420px] w-[420px] rounded-full bg-cyan-400/[0.06] blur-[120px]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:linear-gradient(to_bottom,black,transparent_75%)]" />
      </div>

      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
        <Link href="/" className="flex items-center gap-3" aria-label="StockSentinel home">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl border border-blue-300/20 bg-blue-400/10 text-blue-200">
            <ShieldCheck size={22} />
          </span>
          <span className="text-lg font-black tracking-tight">Stock<span className="text-blue-300">Sentinel</span></span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-400 md:flex">
          <a href="#features" className="transition hover:text-white">Platform</a>
          <a href="#workflow" className="transition hover:text-white">How it works</a>
          <a href="#trust" className="transition hover:text-white">Data & trust</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="hidden rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:text-white sm:inline-flex">
            Sign in
          </Link>
          <Link href="/register" className="inline-flex items-center gap-2 rounded-xl bg-blue-300 px-4 py-2.5 text-sm font-extrabold text-slate-950 shadow-[0_8px_30px_rgba(96,165,250,0.18)] transition hover:bg-blue-200">
            Get started <ArrowRight size={16} />
          </Link>
        </div>
      </header>

      <section className="relative z-10 mx-auto grid max-w-7xl items-center gap-14 px-5 pb-24 pt-12 sm:px-8 md:pt-20 lg:grid-cols-[1.02fr_0.98fr] lg:px-12 lg:pb-32 lg:pt-24">
        <div>
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-blue-300/20 bg-blue-300/[0.07] px-3.5 py-2 text-xs font-bold tracking-wide text-blue-200">
            <Sparkles size={14} />
            MARKET INTELLIGENCE FOR DISCIPLINED INVESTORS
          </div>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-6xl lg:text-[76px]">
            Trade your thesis.
            <span className="mt-2 block bg-gradient-to-r from-blue-200 via-cyan-200 to-slate-100 bg-clip-text text-transparent">Not your impulse.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-8 text-slate-400 sm:text-lg">
            Track the stocks you care about, understand the headlines around them, and practise your decisions before real money is on the line.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href="/register" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-blue-300 px-6 py-4 text-sm font-extrabold text-slate-950 transition hover:-translate-y-0.5 hover:bg-blue-200">
              Start paper trading <ArrowRight size={17} />
            </Link>
            <a href="#features" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.035] px-6 py-4 text-sm font-bold text-slate-200 transition hover:bg-white/[0.07]">
              Explore the platform
            </a>
          </div>
          <div className="mt-8 flex flex-wrap gap-x-5 gap-y-3 text-xs text-slate-500">
            <span className="inline-flex items-center gap-2"><CheckCircle2 size={15} className="text-emerald-300" /> Free account to get started</span>
            <span className="inline-flex items-center gap-2"><CheckCircle2 size={15} className="text-emerald-300" /> Paper trading only</span>
            <span className="inline-flex items-center gap-2"><CheckCircle2 size={15} className="text-emerald-300" /> No brokerage connection needed</span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-[600px]">
          <div className="absolute -inset-5 rounded-[36px] bg-blue-400/[0.08] blur-2xl" />
          <div className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0e1420]/95 shadow-[0_35px_120px_rgba(0,0,0,0.5)]">
            <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4 sm:px-7">
              <div className="flex items-center gap-2.5">
                <span className="h-2 w-2 rounded-full bg-emerald-300" />
                <span className="text-xs font-bold tracking-wide text-slate-300">YOUR INVESTOR WORKSPACE</span>
              </div>
              <span className="rounded-md border border-white/10 px-2 py-1 text-[9px] font-black tracking-[0.16em] text-slate-500">ILLUSTRATIVE PREVIEW</span>
            </div>
            <div className="p-5 sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs text-slate-500">Portfolio overview</p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">$24,680<span className="text-xl text-slate-500">.40</span></p>
                  <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-bold text-emerald-300"><TrendingUp size={14} /> Sample portfolio view</p>
                </div>
                <div className="rounded-2xl border border-blue-300/15 bg-blue-300/[0.08] p-3 text-blue-200"><Activity size={22} /></div>
              </div>
              <div className="mt-7 rounded-2xl border border-white/[0.07] bg-[#0a0f18] p-4">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300">Portfolio trend</span>
                  <span className="text-[10px] text-slate-600">Sample data</span>
                </div>
                <svg viewBox="0 0 520 120" className="h-28 w-full" role="img" aria-label="Illustrative portfolio trend chart">
                  <defs>
                    <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#7dd3fc" stopOpacity="0.25" />
                      <stop offset="100%" stopColor="#7dd3fc" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {[24, 54, 84, 114].map((y) => <line key={y} x1="0" x2="520" y1={y} y2={y} stroke="rgba(255,255,255,0.06)" />)}
                  <path d="M0,94 C30,88 34,68 64,76 S100,83 128,59 S170,72 197,49 S232,60 261,42 S300,52 330,31 S367,52 397,28 S440,39 467,17 S500,28 520,12 L520,120 L0,120 Z" fill="url(#trendFill)" />
                  <path d="M0,94 C30,88 34,68 64,76 S100,83 128,59 S170,72 197,49 S232,60 261,42 S300,52 330,31 S367,52 397,28 S440,39 467,17 S500,28 520,12" fill="none" stroke="#7dd3fc" strokeWidth="2.5" strokeLinecap="round" />
                </svg>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3">
                  <p className="text-[10px] text-slate-500">Watchlist</p><p className="mt-1 text-sm font-bold">Focused</p>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3">
                  <p className="text-[10px] text-slate-500">Market mood</p><p className="mt-1 text-sm font-bold text-cyan-200">Context</p>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3">
                  <p className="text-[10px] text-slate-500">Alerts</p><p className="mt-1 text-sm font-bold">Your rules</p>
                </div>
              </div>
            </div>
          </div>
          <p className="mt-3 text-center text-[10px] text-slate-600">Illustrative UI preview only — figures above are not live market data.</p>
        </div>
      </section>

      <section id="features" className="relative z-10 border-y border-white/[0.06] bg-white/[0.015]">
        <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-12 lg:py-24">
          <div className="max-w-2xl">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-blue-200">Built for better decisions</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">Everything in one place.<br /><span className="text-slate-500">Clarity over clutter.</span></h2>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: FeatureIcon, title, description, number }) => (
              <article key={number} className="group rounded-3xl border border-white/[0.07] bg-[#0b1019]/80 p-6 transition duration-300 hover:-translate-y-1 hover:border-blue-200/20 hover:bg-[#101827]">
                <div className="flex items-center justify-between">
                  <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-blue-200/15 bg-blue-200/[0.07] text-blue-200"><FeatureIcon size={20} /></span>
                  <span className="font-mono text-xs text-slate-700">{number}</span>
                </div>
                <h3 className="mt-7 text-base font-bold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-500">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="relative z-10 mx-auto grid max-w-7xl gap-12 px-5 py-20 sm:px-8 md:grid-cols-2 md:items-center lg:px-12 lg:py-28">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-blue-200">A calmer workflow</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">From ticker to<br />thoughtful decision.</h2>
          <p className="mt-5 max-w-lg text-sm leading-7 text-slate-400">StockSentinel is designed to keep your research, monitoring, and practice in a single loop—so a headline or a sudden price move is a prompt to investigate, not an instruction to trade.</p>
        </div>
        <div className="space-y-3">
          {[
            ['01', 'Build your watchlist', 'Keep the companies you are researching close at hand.'],
            ['02', 'Set your own signals', 'Create price or indicator alerts that match your plan.'],
            ['03', 'Review, practise, improve', 'Use paper trades and history to learn from your decisions.'],
          ].map(([number, title, description]) => (
            <div key={number} className="flex gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
              <span className="font-mono text-sm text-blue-200">{number}</span>
              <div><h3 className="text-sm font-bold">{title}</h3><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section id="trust" className="relative z-10 border-y border-white/[0.06] bg-[#0b1019]">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-12 sm:px-8 md:flex-row md:items-center md:justify-between lg:px-12">
          <div className="flex max-w-3xl gap-4">
            <ShieldCheck size={24} className="mt-1 shrink-0 text-blue-200" />
            <div>
              <h2 className="text-sm font-bold">Honest data. Clear boundaries.</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Market data availability and freshness depend on the provider and market session. Sentiment is a headline-based signal, not a guarantee. StockSentinel is for research and paper trading; it is not a broker and does not provide personalized investment advice.</p>
            </div>
          </div>
          <Link href="/register" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-extrabold text-slate-950 transition hover:bg-blue-100">Create your account <ArrowRight size={16} /></Link>
        </div>
      </section>

      <footer className="relative z-10 mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-xs text-slate-600 sm:px-8 md:flex-row md:items-center md:justify-between lg:px-12">
        <span>© {new Date().getFullYear()} StockSentinel</span>
        <span>Market research and paper trading for disciplined practice.</span>
        <div className="flex gap-4"><Link href="/login" className="transition hover:text-slate-300">Sign in</Link><Link href="/register" className="transition hover:text-slate-300">Get started</Link></div>
      </footer>
    </main>
  );
}
