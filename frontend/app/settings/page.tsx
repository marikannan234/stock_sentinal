'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, profileService } from '@/lib/api-service';
import type { UserSettings } from '@/lib/types';

export default function SettingsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [settings, setSettings] = useState<UserSettings | null>(null);

  async function loadSettings() {
    try {
      setLoading(true);
      setError('');
      setSettings(await profileService.getSettings());
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load settings.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSettings();
  }, []);

  async function handleSave() {
    if (!settings) return;
    try {
      setSaving(true);
      const updated = await profileService.updateSettings({
        email_notifications: settings.email_notifications,
        dark_mode: settings.dark_mode,
        preferred_currency: settings.preferred_currency,
        two_factor_enabled: settings.two_factor_enabled,
      });
      setSettings(updated);
      showToast({ title: 'Settings saved', description: 'Your preferences were updated successfully.', variant: 'success' });
    } catch (err) {
      showToast({ title: 'Unable to save settings', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedShell>
      <AppShell currentPage="settings" title="Settings" description="User-level notification and preference controls backed by `/user/settings`.">
        {loading ? (
          <LoadingState label="Loading settings..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadSettings()} />
        ) : settings ? (
          <SurfaceCard className="max-w-3xl">
            <div className="grid gap-6">
              {[
                ['Email Notifications', settings.email_notifications, 'email_notifications'],
                ['Dark Mode', settings.dark_mode, 'dark_mode'],
                ['Two Factor Enabled', settings.two_factor_enabled, 'two_factor_enabled'],
              ].map(([label, value, key]) => (
                <label key={String(key)} className="flex items-center justify-between rounded-2xl bg-[#17161a] px-4 py-4">
                  <span className="text-sm font-medium text-white">{label}</span>
                  <input
                    type="checkbox"
                    checked={Boolean(value)}
                    onChange={(event) =>
                      setSettings((current) => current ? { ...current, [String(key)]: event.target.checked } : current)
                    }
                    className="h-5 w-5 rounded border-slate-700 bg-slate-900 text-emerald-500"
                  />
                </label>
              ))}
              <Select
                label="Preferred Currency"
                value={settings.preferred_currency}
                onChange={(event) => setSettings((current) => current ? { ...current, preferred_currency: event.target.value } : current)}
                options={[
                  { value: 'USD', label: 'USD' },
                  { value: 'EUR', label: 'EUR' },
                  { value: 'INR', label: 'INR' },
                  { value: 'GBP', label: 'GBP' },
                ]}
              />
              <Button onClick={() => void handleSave()} isLoading={saving}>Save Settings</Button>
            </div>
          </SurfaceCard>
        ) : null}
      </AppShell>
    </ProtectedShell>
  );
}
