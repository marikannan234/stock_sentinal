'use client';

import { useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, profileService } from '@/lib/api-service';
import type { LiveQuote, UserProfile, UserSettings } from '@/lib/types';

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([profileService.getProfile(), profileService.getSettings(), marketService.getLiveRibbon()]).then(([profileResult, settingsResult, ribbonResult]) => {
      if (profileResult.status === 'fulfilled') setProfile(profileResult.value);
      if (settingsResult.status === 'fulfilled') setSettings(settingsResult.value);
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  async function saveSettings(nextSettings: Partial<UserSettings>) {
    const updated = await profileService.updateSettings(nextSettings);
    setSettings(updated);
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Settings" subtitle="Configure your Sentinel cockpit and security preferences." ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 space-y-6 lg:col-span-8">
            <SurfaceCard className="p-8">
              <h2 className="mb-6 text-2xl font-bold text-white">General Preferences</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                  <div>
                    <p className="font-bold text-white">Dark Mode</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Switch between obsidian and light themes.</p>
                  </div>
                  <button onClick={() => saveSettings({ dark_mode: !(settings?.dark_mode ?? true) })} className={(settings?.dark_mode ?? true) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-white'}>
                    {(settings?.dark_mode ?? true) ? 'On' : 'Off'}
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Preferred Currency</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Set the default currency for valuation.</p>
                  </div>
                  <select value={settings?.preferred_currency ?? 'USD'} onChange={(event) => saveSettings({ preferred_currency: event.target.value })} className="rounded-xl bg-[var(--surface-lowest)] px-4 py-3 text-sm text-white outline-none">
                    <option value="USD">$ USD</option>
                    <option value="EUR">€ EUR</option>
                    <option value="INR">₹ INR</option>
                  </select>
                </div>
              </div>
            </SurfaceCard>

            <SurfaceCard className="p-8">
              <h2 className="mb-6 text-2xl font-bold text-white">Notification Channels</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                  <div>
                    <p className="font-bold text-white">Email Notifications</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Receive weekly reports and market shifts via email.</p>
                  </div>
                  <button onClick={() => saveSettings({ email_notifications: !(settings?.email_notifications ?? true) })} className={(settings?.email_notifications ?? true) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-white'}>
                    {(settings?.email_notifications ?? true) ? 'On' : 'Off'}
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Two-Factor Auth</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Secure your account with an extra verification layer.</p>
                  </div>
                  <button onClick={() => saveSettings({ two_factor_enabled: !(settings?.two_factor_enabled ?? false) })} className={(settings?.two_factor_enabled ?? false) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-white'}>
                    {(settings?.two_factor_enabled ?? false) ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
              </div>
            </SurfaceCard>
          </div>

          <div className="col-span-12 space-y-6 lg:col-span-4">
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-xl font-bold text-white">Sentinel Guard</h3>
              <div className="rounded-2xl bg-[var(--surface-lowest)] p-5">
                <p className="text-sm font-bold text-white">Two-Factor Auth</p>
                <p className="mt-2 text-sm text-[var(--on-surface-variant)]">{settings?.two_factor_enabled ? 'Enabled and secured.' : 'Currently disabled.'}</p>
              </div>
            </SurfaceCard>
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-xl font-bold text-white">Operator</h3>
              <p className="text-lg font-bold text-white">{profile?.full_name || 'Sentinel User'}</p>
              <p className="text-sm text-[var(--on-surface-variant)]">{profile?.email}</p>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
