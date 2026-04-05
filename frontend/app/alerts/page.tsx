'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { alertService, getErrorMessage } from '@/lib/api-service';
import { formatDateTime } from '@/lib/format';
import type { AlertItem } from '@/lib/types';

export default function AlertsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    stock_symbol: '',
    alert_type: 'price',
    condition: '>',
    target_value: '',
  });

  async function loadAlerts() {
    try {
      setLoading(true);
      setError('');
      setAlerts(await alertService.list());
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load alerts.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAlerts();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!form.stock_symbol.trim() || Number(form.target_value) <= 0) {
      showToast({ title: 'Invalid alert', description: 'Symbol and target value are required.', variant: 'error' });
      return;
    }

    try {
      setSubmitting(true);
      await alertService.create({
        stock_symbol: form.stock_symbol.trim().toUpperCase(),
        alert_type: form.alert_type,
        condition: form.alert_type === 'price' ? form.condition : undefined,
        target_value: Number(form.target_value),
      });
      showToast({ title: 'Alert created', description: 'Your alert is now active.', variant: 'success' });
      setForm({ stock_symbol: '', alert_type: 'price', condition: '>', target_value: '' });
      await loadAlerts();
    } catch (err) {
      showToast({ title: 'Unable to create alert', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleAlert(item: AlertItem) {
    try {
      await alertService.update(item.id, !item.is_active);
      showToast({ title: 'Alert updated', description: `${item.stock_symbol} alert was updated.`, variant: 'success' });
      await loadAlerts();
    } catch (err) {
      showToast({ title: 'Unable to update alert', description: getErrorMessage(err), variant: 'error' });
    }
  }

  async function deleteAlert(id: number) {
    try {
      await alertService.remove(id);
      showToast({ title: 'Alert deleted', description: 'The alert was removed.', variant: 'success' });
      await loadAlerts();
    } catch (err) {
      showToast({ title: 'Unable to delete alert', description: getErrorMessage(err), variant: 'error' });
    }
  }

  return (
    <ProtectedShell>
      <AppShell currentPage="alerts" title="Alerts" description="Manage real backend alerts for prices, crashes, and volume changes.">
        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <SurfaceCard>
            <h2 className="text-xl font-bold text-white">Create Alert</h2>
            <form className="mt-5 space-y-4" onSubmit={handleCreate}>
              <Input label="Symbol" value={form.stock_symbol} onChange={(event) => setForm((current) => ({ ...current, stock_symbol: event.target.value }))} />
              <Select
                label="Alert Type"
                value={form.alert_type}
                onChange={(event) => setForm((current) => ({ ...current, alert_type: event.target.value }))}
                options={[
                  { value: 'price', label: 'Price' },
                  { value: 'percentage_change', label: 'Percentage Change' },
                  { value: 'volume_spike', label: 'Volume Spike' },
                  { value: 'crash', label: 'Crash' },
                ]}
              />
              {form.alert_type === 'price' ? (
                <Select
                  label="Condition"
                  value={form.condition}
                  onChange={(event) => setForm((current) => ({ ...current, condition: event.target.value }))}
                  options={[
                    { value: '>', label: 'Greater than' },
                    { value: '<', label: 'Less than' },
                    { value: '>=', label: 'Greater than or equal' },
                    { value: '<=', label: 'Less than or equal' },
                  ]}
                />
              ) : null}
              <Input label="Target Value" type="number" min="0" step="0.01" value={form.target_value} onChange={(event) => setForm((current) => ({ ...current, target_value: event.target.value }))} />
              <Button type="submit" fullWidth isLoading={submitting}>Create Alert</Button>
            </form>
          </SurfaceCard>

          {loading ? (
            <LoadingState label="Loading alerts..." />
          ) : error ? (
            <ErrorState message={error} onRetry={() => void loadAlerts()} />
          ) : !alerts.length ? (
            <EmptyState title="No alerts yet" message="Create your first alert to start monitoring price action." />
          ) : (
            <SurfaceCard>
              <h2 className="text-xl font-bold text-white">Active Alerts</h2>
              <div className="mt-5 space-y-3">
                {alerts.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/5 bg-[#17161a] p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="font-semibold text-white">{item.stock_symbol}</p>
                        <p className="mt-1 text-sm text-on-surface-variant">
                          {item.alert_type} {item.condition ?? ''} {item.target_value ?? 'N/A'}
                        </p>
                        <p className="mt-1 text-xs text-on-surface-variant">Created {formatDateTime(item.created_at)}</p>
                      </div>
                      <div className="flex gap-3">
                        <Button variant="outline" onClick={() => void toggleAlert(item)}>
                          {item.is_active ? 'Disable' : 'Enable'}
                        </Button>
                        <Button variant="ghost" onClick={() => void deleteAlert(item.id)}>
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </SurfaceCard>
          )}
        </div>
      </AppShell>
    </ProtectedShell>
  );
}
