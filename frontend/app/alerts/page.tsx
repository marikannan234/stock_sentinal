'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { alertService, marketService } from '@/lib/api-service';
import type { AlertItem, LiveQuote } from '@/lib/types';
import { formatDateLabel } from '@/lib/sentinel-utils';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [symbol, setSymbol] = useState('');
  const [target, setTarget] = useState('');
  const [condition, setCondition] = useState('>');

  async function loadAlerts() {
    const data = await alertService.list();
    setAlerts(data);
  }

  useEffect(() => {
    Promise.allSettled([loadAlerts(), marketService.getLiveRibbon()]).then(([_, ribbonResult]) => {
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!symbol || !target) return;
    await alertService.create({
      stock_symbol: symbol.toUpperCase(),
      condition,
      target_value: Number(target),
      alert_type: 'price',
    });
    setSymbol('');
    setTarget('');
    await loadAlerts();
  }

  async function toggleAlert(id: number, isActive: boolean) {
    await alertService.update(id, !isActive);
    await loadAlerts();
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Alerts" subtitle="Price-based sentinel triggers and monitoring." ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 p-6 lg:col-span-4">
            <h2 className="mb-6 text-xl font-bold text-white">Create Alert</h2>
            <form className="space-y-4" onSubmit={handleCreate}>
              <input value={symbol} onChange={(event) => setSymbol(event.target.value)} className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-4 text-white outline-none" placeholder="Ticker (AAPL)" />
              <div className="grid grid-cols-[120px_1fr] gap-3">
                <select value={condition} onChange={(event) => setCondition(event.target.value)} className="rounded-xl bg-[var(--surface-lowest)] px-4 py-4 text-white outline-none">
                  <option>{'>'}</option>
                  <option>{'<'}</option>
                  <option>{'>='}</option>
                  <option>{'<='}</option>
                </select>
                <input value={target} onChange={(event) => setTarget(event.target.value)} className="rounded-xl bg-[var(--surface-lowest)] px-4 py-4 text-white outline-none" placeholder="Target value" type="number" step="0.01" />
              </div>
              <button className="w-full rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-4 text-sm font-bold text-[var(--on-primary)]">Deploy Alert</button>
            </form>
          </SurfaceCard>
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="border-b border-white/5 px-6 py-5">
              <h2 className="text-xl font-bold text-white">Active Watch Grid</h2>
            </div>
            <div className="divide-y divide-white/5">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between px-6 py-5">
                  <div>
                    <p className="font-bold text-white">{alert.stock_symbol}</p>
                    <p className="text-xs text-[var(--on-surface-variant)]">{alert.condition} {alert.target_value} • {formatDateLabel(alert.created_at)}</p>
                  </div>
                  <button onClick={() => toggleAlert(alert.id, alert.is_active)} className={alert.is_active ? 'rounded-full bg-secondary/10 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-secondary' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-xs font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]'}>
                    {alert.is_active ? 'Live' : 'Paused'}
                  </button>
                </div>
              ))}
            </div>
          </SurfaceCard>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
