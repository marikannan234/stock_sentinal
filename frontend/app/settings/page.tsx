'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, profileService, getErrorMessage } from '@/lib/api-service';
import type { LiveQuote, UserProfile, UserSettings } from '@/lib/types';

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  // Profile editing
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState('');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameError, setNameError] = useState('');
  const [nameSaved, setNameSaved] = useState(false);

  useEffect(() => {
    Promise.allSettled([profileService.getProfile(), profileService.getSettings(), marketService.getLiveRibbon()]).then(
      ([profileResult, settingsResult, ribbonResult]) => {
        if (profileResult.status === 'fulfilled') {
          setProfile(profileResult.value);
          setNameValue(profileResult.value.full_name ?? '');
        }
        if (settingsResult.status === 'fulfilled') setSettings(settingsResult.value);
        if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks);
      },
    );
  }, []);

  async function saveSettings(nextSettings: Partial<UserSettings>) {
    try {
      const updated = await profileService.updateSettings(nextSettings);
      setSettings(updated);
    } catch {
      // ignore
    }
  }

  async function saveName(e: FormEvent) {
    e.preventDefault();
    setNameLoading(true);
    setNameError('');
    setNameSaved(false);
    try {
      const updated = await profileService.updateProfile(nameValue);
      setProfile(updated);
      setEditingName(false);
      setNameSaved(true);
      setTimeout(() => setNameSaved(false), 2000);
    } catch (err) {
      setNameError(getErrorMessage(err));
    } finally {
      setNameLoading(false);
    }
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Settings" subtitle="Configure your Sentinel cockpit and security preferences." ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 space-y-6 lg:col-span-8">
            {/* Profile */}
            <SurfaceCard className="p-8">
              <h2 className="mb-5 text-xl font-bold text-white">Profile</h2>
              <div className="space-y-5">
                {/* Email (read-only) */}
                <div className="flex items-center justify-between border-b border-white/5 pb-5">
                  <div>
                    <p className="font-bold text-white">Email</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">{profile?.email ?? '—'}</p>
                  </div>
                  <span className="rounded-full bg-[var(--surface-high)] px-3 py-1 text-xs text-[var(--on-surface-variant)]">Verified</span>
                </div>

                {/* Full Name – editable */}
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 pr-4">
                    <p className="font-bold text-white">Full Name</p>
                    {editingName ? (
                      <form onSubmit={saveName} className="mt-2 flex gap-2">
                        <input
                          value={nameValue}
                          onChange={(e) => setNameValue(e.target.value)}
                          className="w-full max-w-xs rounded-xl bg-[var(--surface-lowest)] px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
                          placeholder="Your full name"
                        />
                        <button
                          type="submit"
                          disabled={nameLoading}
                          className="rounded-xl bg-[var(--primary)] px-4 py-2 text-xs font-bold text-[var(--on-primary)] disabled:opacity-60"
                        >
                          {nameLoading ? 'Saving…' : 'Save'}
                        </button>
                        <button
                          type="button"
                          onClick={() => { setEditingName(false); setNameValue(profile?.full_name ?? ''); setNameError(''); }}
                          className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs font-bold text-white"
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <p className="text-sm text-[var(--on-surface-variant)]">{profile?.full_name || 'Not set'}</p>
                    )}
                    {nameError && <p className="mt-1 text-xs text-tertiary">{nameError}</p>}
                    {nameSaved && <p className="mt-1 text-xs text-secondary">Name updated!</p>}
                  </div>
                  {!editingName && (
                    <button
                      onClick={() => setEditingName(true)}
                      className="rounded-xl bg-[var(--surface-high)] px-4 py-2 text-xs font-bold text-white hover:bg-[var(--surface-highest)] transition-colors"
                    >
                      Edit
                    </button>
                  )}
                </div>
              </div>
            </SurfaceCard>

            {/* General Preferences */}
            <SurfaceCard className="p-8">
              <h2 className="mb-5 text-xl font-bold text-white">General Preferences</h2>
              <div className="space-y-5">
                <div className="flex items-center justify-between border-b border-white/5 pb-5">
                  <div>
                    <p className="font-bold text-white">Dark Mode</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Switch between obsidian and light themes.</p>
                  </div>
                  <button
                    onClick={() => saveSettings({ dark_mode: !(settings?.dark_mode ?? true) })}
                    className={(settings?.dark_mode ?? true) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-sm text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-sm text-white'}
                  >
                    {(settings?.dark_mode ?? true) ? 'On' : 'Off'}
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Preferred Currency</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Set the default currency for valuation.</p>
                  </div>
                  <select
                    value={settings?.preferred_currency ?? 'USD'}
                    onChange={(e) => saveSettings({ preferred_currency: e.target.value })}
                    className="rounded-xl bg-[var(--surface-lowest)] px-4 py-2.5 text-sm text-white outline-none"
                  >
                    <option value="USD">$ USD</option>
                    <option value="EUR">€ EUR</option>
                    <option value="INR">₹ INR</option>
                  </select>
                </div>
              </div>
            </SurfaceCard>

            {/* Notification Channels */}
            <SurfaceCard className="p-8">
              <h2 className="mb-5 text-xl font-bold text-white">Notification Channels</h2>
              <div className="space-y-5">
                <div className="flex items-center justify-between border-b border-white/5 pb-5">
                  <div>
                    <p className="font-bold text-white">Email Notifications</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Receive weekly reports and market shifts via email.</p>
                  </div>
                  <button
                    onClick={() => saveSettings({ email_notifications: !(settings?.email_notifications ?? true) })}
                    className={(settings?.email_notifications ?? true) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-sm text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-sm text-white'}
                  >
                    {(settings?.email_notifications ?? true) ? 'On' : 'Off'}
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Two-Factor Auth</p>
                    <p className="text-sm text-[var(--on-surface-variant)]">Secure your account with an extra verification layer.</p>
                  </div>
                  <button
                    onClick={() => saveSettings({ two_factor_enabled: !(settings?.two_factor_enabled ?? false) })}
                    className={(settings?.two_factor_enabled ?? false) ? 'rounded-full bg-[var(--primary)] px-4 py-2 text-sm text-[var(--on-primary)]' : 'rounded-full bg-[var(--surface-high)] px-4 py-2 text-sm text-white'}
                  >
                    {(settings?.two_factor_enabled ?? false) ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
              </div>
            </SurfaceCard>
          </div>

          {/* Right Sidebar */}
          <div className="col-span-12 space-y-6 lg:col-span-4">
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-lg font-bold text-white">Sentinel Guard</h3>
              <div className="rounded-2xl bg-[var(--surface-lowest)] p-4">
                <p className="text-sm font-bold text-white">Two-Factor Auth</p>
                <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
                  {settings?.two_factor_enabled ? 'Enabled and secured.' : 'Currently disabled.'}
                </p>
              </div>
            </SurfaceCard>
            <SurfaceCard className="p-6">
              <h3 className="mb-4 text-lg font-bold text-white">Operator</h3>
              <p className="font-bold text-white">{profile?.full_name || 'Sentinel User'}</p>
              <p className="text-sm text-[var(--on-surface-variant)]">{profile?.email}</p>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
