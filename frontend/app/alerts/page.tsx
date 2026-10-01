'use client';

import { FormEvent, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import {
  useAlertsQuery,
  useCreateAlertMutation,
  useDeleteAlertMutation,
  useSetAlertActiveMutation,
  type CreateAlertPayload,
} from '@/hooks/queries/use-alerts';
import { getErrorMessage } from '@/lib/api-service';
import type { AlertItem } from '@/lib/types';
import { formatDateLabel } from '@/lib/sentinel-utils';

// 'indicator' and 'combined' are form groups; the API type is picked below.
type AlertType = 'price' | 'percentage_change' | 'volume_spike' | 'crash' | 'custom' | 'indicator' | 'combined';
type PeriodField = 'sma_period' | 'ema_period' | 'rsi_period';

const ALERT_TYPES: { value: AlertType; label: string }[] = [
  { value: 'price', label: 'Price' },
  { value: 'percentage_change', label: '% Change' },
  { value: 'volume_spike', label: 'Volume Spike' },
  { value: 'crash', label: 'Crash' },
  { value: 'custom', label: 'Custom' },
  { value: 'indicator', label: 'Indicator' },
  { value: 'combined', label: 'Combined' },
];

const INDICATOR_TYPES: { value: string; label: string; period: PeriodField; defaultPeriod: string }[] = [
  { value: 'sma_above', label: 'Price above SMA', period: 'sma_period', defaultPeriod: '50' },
  { value: 'sma_below', label: 'Price below SMA', period: 'sma_period', defaultPeriod: '50' },
  { value: 'sma_crossover', label: 'Price crosses SMA', period: 'sma_period', defaultPeriod: '50' },
  { value: 'ema_above', label: 'Price above EMA', period: 'ema_period', defaultPeriod: '20' },
  { value: 'ema_below', label: 'Price below EMA', period: 'ema_period', defaultPeriod: '20' },
  { value: 'ema_crossover', label: 'Price crosses EMA', period: 'ema_period', defaultPeriod: '20' },
  { value: 'rsi_overbought', label: 'RSI above 70 (overbought)', period: 'rsi_period', defaultPeriod: '14' },
  { value: 'rsi_oversold', label: 'RSI below 30 (oversold)', period: 'rsi_period', defaultPeriod: '14' },
  { value: 'rsi_crossover', label: 'RSI crosses 30 / 70', period: 'rsi_period', defaultPeriod: '14' },
];

const COMBINED_TYPES = [
  { value: 'strong_buy_signal', label: 'Strong buy: price > SMA & EMA, RSI < 30' },
  { value: 'strong_sell_signal', label: 'Strong sell: price < SMA & EMA, RSI > 70' },
];

const PERIOD_LIMITS: Record<PeriodField, number> = { sma_period: 500, ema_period: 500, rsi_period: 100 };

function isValidPeriod(value: string, field: PeriodField) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 2 && n <= PERIOD_LIMITS[field];
}

function isPositiveNumber(value: string) {
  return value !== '' && !isNaN(Number(value)) && Number(value) > 0;
}

function describeAlert(alert: AlertItem): string {
  switch (alert.alert_type) {
    case 'price':
    case 'custom':
      return `${alert.condition ?? ''} ${alert.target_value ?? ''}`;
    case 'percentage_change':
      return `±${alert.target_value}% move`;
    case 'volume_spike':
      return `${alert.target_value}x avg volume`;
    case 'crash':
      return `-${alert.target_value}% drop`;
    case 'strong_buy_signal':
    case 'strong_sell_signal':
      return `SMA ${alert.sma_period} · EMA ${alert.ema_period} · RSI ${alert.rsi_period}`;
    default:
      if (alert.sma_period) return `SMA(${alert.sma_period})`;
      if (alert.ema_period) return `EMA(${alert.ema_period})`;
      if (alert.rsi_period) return `RSI(${alert.rsi_period})`;
      return '';
  }
}

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
  const alertsQuery = useAlertsQuery();
  const alerts = alertsQuery.data ?? [];
  const createAlert = useCreateAlertMutation();
  const setAlertActive = useSetAlertActiveMutation();
  const deleteAlertMutation = useDeleteAlertMutation();
  const listActionError = setAlertActive.error ?? deleteAlertMutation.error;

  // Form state
  const [symbol, setSymbol] = useState('');
  const [alertType, setAlertType] = useState<AlertType>('price');
  const [condition, setCondition] = useState('>');
  const [target, setTarget] = useState('');
  const [indicatorType, setIndicatorType] = useState(INDICATOR_TYPES[0].value);
  const [period, setPeriod] = useState(INDICATOR_TYPES[0].defaultPeriod);
  const [combinedType, setCombinedType] = useState(COMBINED_TYPES[0].value);
  const [smaPeriod, setSmaPeriod] = useState('50');
  const [emaPeriod, setEmaPeriod] = useState('20');
  const [rsiPeriod, setRsiPeriod] = useState('14');
  const [formError, setFormError] = useState('');

  const selectedIndicator = INDICATOR_TYPES.find((t) => t.value === indicatorType) ?? INDICATOR_TYPES[0];
  const formLoading = createAlert.isPending;

  // Validate form based on alert type
  function isFormValid() {
    if (!symbol.trim()) return false;
    if (alertType === 'indicator') {
      return isValidPeriod(period, selectedIndicator.period);
    }
    if (alertType === 'combined') {
      return isValidPeriod(smaPeriod, 'sma_period') && isValidPeriod(emaPeriod, 'ema_period') && isValidPeriod(rsiPeriod, 'rsi_period');
    }
    // price, custom, percentage_change, volume_spike, crash: a positive threshold
    return isPositiveNumber(target);
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isFormValid()) {
      setFormError('Please fill all required fields');
      return;
    }
    
    setFormError('');
    try {
      const payload: CreateAlertPayload = {
        stock_symbol: (symbol || "").toUpperCase(),
        alert_type: alertType,
      };

      if (alertType === 'indicator') {
        // Indicator alerts are defined by their period only (no price target)
        payload.alert_type = selectedIndicator.value;
        payload[selectedIndicator.period] = Number(period);
      } else if (alertType === 'combined') {
        payload.alert_type = combinedType;
        payload.sma_period = Number(smaPeriod);
        payload.ema_period = Number(emaPeriod);
        payload.rsi_period = Number(rsiPeriod);
      } else {
        payload.target_value = Number(target);
        // Only price and custom rules use a comparison condition
        if (alertType === 'price' || alertType === 'custom') {
          payload.condition = condition;
        }
      }

      await createAlert.mutateAsync(payload);
      setSymbol('');
      setTarget('');
      setAlertType('price');
      setCondition('>');
      setIndicatorType(INDICATOR_TYPES[0].value);
      setPeriod(INDICATOR_TYPES[0].defaultPeriod);
    } catch (err) {
      setFormError(getErrorMessage(err));
    }
  }

  function toggleAlert(id: number, isActive: boolean) {
    deleteAlertMutation.reset();
    setAlertActive.mutate({ id, isActive: !isActive });
  }

  function deleteAlert(id: number) {
    setAlertActive.reset();
    deleteAlertMutation.mutate(id);
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Alerts" subtitle="Price-based sentinel triggers and monitoring.">
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

              {/* Condition + Target — for price and custom rules */}
              {(alertType === 'price' || alertType === 'custom') && (
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

              {/* Indicator rule + period (no price target) */}
              {alertType === 'indicator' && (
                <div className="space-y-3">
                  <select
                    value={indicatorType}
                    onChange={(e) => {
                      const next = INDICATOR_TYPES.find((t) => t.value === e.target.value) ?? INDICATOR_TYPES[0];
                      if (next.period !== selectedIndicator.period) setPeriod(next.defaultPeriod);
                      setIndicatorType(next.value);
                    }}
                    className="w-full rounded-xl bg-[var(--surface-lowest)] px-3 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
                  >
                    {INDICATOR_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <input
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="w-full rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                    placeholder={`${selectedIndicator.period.split('_')[0].toUpperCase()} period in days (2-${PERIOD_LIMITS[selectedIndicator.period]})`}
                    type="number"
                    step="1"
                    min="2"
                    max={PERIOD_LIMITS[selectedIndicator.period]}
                  />
                </div>
              )}

              {/* Combined signal: all three periods */}
              {alertType === 'combined' && (
                <div className="space-y-3">
                  <select
                    value={combinedType}
                    onChange={(e) => setCombinedType(e.target.value)}
                    className="w-full rounded-xl bg-[var(--surface-lowest)] px-3 py-3 text-sm text-white outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
                  >
                    {COMBINED_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <div className="grid grid-cols-3 gap-2">
                    {([
                      ['SMA', smaPeriod, setSmaPeriod, 'sma_period'],
                      ['EMA', emaPeriod, setEmaPeriod, 'ema_period'],
                      ['RSI', rsiPeriod, setRsiPeriod, 'rsi_period'],
                    ] as const).map(([label, value, setValue, field]) => (
                      <input
                        key={field}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        aria-label={`${label} period`}
                        className="min-w-0 rounded-xl bg-[var(--surface-lowest)] px-3 py-3 text-sm text-white outline-none placeholder:text-[var(--on-surface-variant)] focus:ring-2 focus:ring-[var(--primary)]/40"
                        placeholder={`${label} period`}
                        type="number"
                        step="1"
                        min="2"
                        max={PERIOD_LIMITS[field]}
                      />
                    ))}
                  </div>
                </div>
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
              {listActionError ? (
                <p className="mt-1 text-xs text-tertiary">{getErrorMessage(listActionError, 'Could not update the alert. Please try again.')}</p>
              ) : null}
            </div>

            {alertsQuery.isPending ? (
              <p className="px-6 py-8 text-sm text-[var(--on-surface-variant)]">Loading alerts…</p>
            ) : alertsQuery.isError ? (
              <div className="flex items-center justify-between px-6 py-6">
                <p className="text-sm text-tertiary">Failed to load alerts. Please try again.</p>
                <button onClick={() => alertsQuery.refetch()} className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs text-white">Retry</button>
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
                            {alert.alert_type.split('_').join(' ')}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--on-surface-variant)]">
                          {describeAlert(alert) ? `${describeAlert(alert)} • ` : ''}
                          {formatDateLabel(alert.created_at)}
                          {!alert.is_active && alert.is_triggered && alert.triggered_at
                            ? ` • Fired ${formatDateLabel(alert.triggered_at)}`
                            : ''}
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
                        {alert.is_active ? 'Live' : alert.is_triggered ? 'Re-arm' : 'Paused'}
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
