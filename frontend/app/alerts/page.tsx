'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { alertService, marketService, getErrorMessage } from '@/lib/api-service';
import type { AlertItem, LiveQuote } from '@/lib/types';
import { formatDateLabel } from '@/lib/sentinel-utils';

type AlertType = 'price' | 'percentage_change' | 'volume_spike' | 'crash';

const ALERT_TYPES: { value: AlertType; label: string }[] = [
  { value: 'price', label: 'Price' },
  { value: 'percentage_change', label: '% Change' },
  { value: 'volume_spike', label: 'Volume Spike' },
  { value: 'crash', label: 'Crash' },
];

function alertTypeBadgeClass(type: string) {
  switch (type) {
    case 'price': return 'bg-[var(--primary)]/10 text-[var(--primary)]';
    case 'percentage_change': return 'bg-secondary/10 text-secondary';
    case 'volume_spike': return 'bg-[#f9c74f]/10 text-[#f9c74f]';
    case 'crash': return 'bg-tertiary/10 text-tertiary';
    default: return 'bg-[var(--surface-high)] text-[var(--on-surface-variant)]';
  }
}

function getAlertTypeIcon(type: string): string {
  switch (type) {
    case 'price': return '💰';
    case 'percentage_change': return '📊';
    case 'volume_spike': return '⚡';
    case 'crash': return '⚠️';
    default: return '🔔';
  }
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);
  const [loadError, setLoadError] = useState('');

  // Form state
  const [symbol, setSymbol] = useState('');
  const [alertType, setAlertType] = useState<AlertType>('price');
  const [condition, setCondition] = useState('>');
  const [target, setTarget] = useState('');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  async function loadAlerts() {
    try {
      const data = await alertService.list();
      setAlerts(data);
      setLoadError('');
    } catch {
      setLoadError('Failed to load alerts. Please try again.');
    }
  }

  useEffect(() => {
    Promise.allSettled([loadAlerts(), marketService.getLiveRibbon()]).then(([_, ribbonResult]) => {
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks);
    });
  }, []);

  // Validate form based on alert type
  function isFormValid() {
    if (!symbol.trim()) return false;
    if (alertType === 'price') {
      return target !== '' && !isNaN(Number(target));
    }
    if (alertType === 'percentage_change') {
      return target !== '' && !isNaN(Number(target));
    }
    if (alertType === 'volume_spike') {
      return target !== '' && !isNaN(Number(target));
    }
    if (alertType === 'crash') {
      return target !== '' && !isNaN(Number(target));
    }
    return true;
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isFormValid()) {
      setFormError('Please fill all required fields');
      return;
    }
    
    setFormLoading(true);
    setFormError('');
    try {
      const payload: Parameters<typeof alertService.create>[0] = {
        stock_symbol: (symbol || "").toUpperCase(),
        alert_type: alertType,
        target_value: Number(target),
      };
      
      // Add condition only for price alerts
      if (alertType === 'price') {
        payload.condition = condition;
      }
      
      await alertService.create(payload);
      setSymbol('');
      setTarget('');
      setAlertType('price');
      setCondition('>');
      await loadAlerts();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function toggleAlert(id: number, isActive: boolean) {
    try {
      await alertService.update(id, !isActive);
      await loadAlerts();
    } catch {
      // ignore
    }
  }

  async function deleteAlert(id: number) {
    try {
      await alertService.remove(id);
      await loadAlerts();
    } catch {
      // ignore
    }
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Alerts" subtitle="Price-based sentinel triggers and monitoring." ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          {/* ── Create Alert Form ── */}
          <SurfaceCard className="col-span-12 p-6 lg:col-span-4">
            <h2 className="mb-5 text-lg font-bold text-white">Create Alert</h2>
            <form className="space-y-4" onSubmit={handleCreate}>
              {/* Symbol */}
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                placeholder="Ticker (e.g. AAPL)"
                required
              />

              {/* Alert Type */}
              <div>
                <p className="mb-2 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Alert Type</p>
                <div className="grid grid-cols-2 gap-2">
                  {ALERT_TYPES.map((t) => (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => setAlertType(t.value)}
                      className={`rounded-xl px-3 py-2 text-xs font-black uppercase tracking-[0.1em] transition-all ${
                        alertType === t.value
                          ? alertTypeBadgeClass(t.value) + ' border border-current/30'
                          : 'bg-[var(--surface-lowest)] text-[var(--on-surface-variant)] hover:text-white'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Condition + Target — for price type */}
              {alertType === 'price' && (
                <div className="flex gap-3 overflow-hidden">
                  <select
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    className="shrink-0 rounded-xl bg-[var(--surface-lowest)] px-3 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
                  >
                    <option value=">">{'>'}</option>
                    <option value="<">{'<'}</option>
                    <option value=">=">{'>='}</option>
                    <option value="<=">{'<='}</option>
                  </select>
                  <input
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    className="min-w-0 flex-1 rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                    placeholder="Target price"
                    type="number"
                    step="0.01"
                  />
                </div>
              )}

              {/* Percentage Change input */}
              {alertType === 'percentage_change' && (
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                  placeholder="% change (e.g. 5)"
                  type="number"
                  step="0.1"
                />
              )}

              {/* Volume Spike Multiplier input */}
              {alertType === 'volume_spike' && (
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                  placeholder="Volume multiplier (e.g. 2x = 200%)"
                  type="number"
                  step="0.1"
                  min="1"
                />
              )}

              {/* Crash Percentage input */}
              {alertType === 'crash' && (
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                  placeholder="% drop (e.g. 10)"
                  type="number"
                  step="0.1"
                />
              )}

              {formError && <p className="text-xs text-tertiary">{formError}</p>}

              <button
                type="submit"
                disabled={formLoading || !isFormValid()}
                className="w-full rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-3 text-sm font-bold text-[var(--on-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {formLoading ? 'Deploying…' : 'Deploy Alert'}
              </button>
            </form>
          </SurfaceCard>

          {/* ── Alert List ── */}
          <SurfaceCard className="col-span-12 overflow-hidden lg:col-span-8">
            <div className="border-b border-white/5 px-6 py-4">
              <h2 className="text-lg font-bold text-white">Active Watch Grid</h2>
            </div>

            {loadError ? (
              <div className="flex items-center justify-between px-6 py-6">
                <p className="text-sm text-tertiary">{loadError}</p>
                <button onClick={loadAlerts} className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs text-white">Retry</button>
              </div>
            ) : alerts.length === 0 ? (
              <p className="px-6 py-8 text-sm text-[var(--on-surface-variant)]">No alerts configured yet. Create one to get started.</p>
            ) : (
              <div className="divide-y divide-white/5">
                {alerts.map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between gap-4 px-6 py-4 hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <span className="text-xl mt-0.5 shrink-0">{getAlertTypeIcon(alert.alert_type)}</span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-bold text-white">{alert.stock_symbol}</p>
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.15em] ${alertTypeBadgeClass(alert.alert_type)}`}>
                            {alert.alert_type.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--on-surface-variant)]">
                          {alert.condition ? `${alert.condition} ${alert.target_value} • ` : ''}
                          {formatDateLabel(alert.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => toggleAlert(alert.id, alert.is_active)}
                        className={
                          alert.is_active
                            ? 'rounded-full bg-secondary/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-secondary hover:bg-secondary/20 transition-colors'
                            : 'rounded-full bg-[var(--surface-high)] px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--on-surface-variant)] hover:bg-[var(--surface-highest)] transition-colors'
                        }
                      >
                        {alert.is_active ? 'Live' : 'Paused'}
                      </button>
                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="rounded-full bg-tertiary/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-tertiary hover:bg-tertiary/20 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SurfaceCard>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
