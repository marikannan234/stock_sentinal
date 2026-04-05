'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, profileService } from '@/lib/api-service';
import { useAuthStore } from '@/lib/auth';
import { formatDateTime } from '@/lib/format';
import type { UserProfile } from '@/lib/types';

export default function ProfilePage() {
  const { showToast } = useToast();
  const refreshUser = useAuthStore((state) => state.refreshUser);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [fullName, setFullName] = useState('');

  async function loadProfile() {
    try {
      setLoading(true);
      setError('');
      const data = await profileService.getProfile();
      setProfile(data);
      setFullName(data.full_name || '');
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load profile.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProfile();
  }, []);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    try {
      setSaving(true);
      const data = await profileService.updateProfile(fullName.trim());
      setProfile(data);
      await refreshUser();
      showToast({ title: 'Profile saved', description: 'Your profile changes were saved.', variant: 'success' });
    } catch (err) {
      showToast({ title: 'Unable to save profile', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedShell>
      <AppShell currentPage="profile" title="Profile" description="Review and update the account data returned by `/user/profile`.">
        {loading ? (
          <LoadingState label="Loading profile..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void loadProfile()} />
        ) : profile ? (
          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <SurfaceCard>
              <p className="text-sm text-on-surface-variant">Account Email</p>
              <p className="mt-2 text-2xl font-black text-white">{profile.email}</p>
              <div className="mt-6 space-y-3 text-sm text-on-surface-variant">
                <p>User ID: {profile.id}</p>
                <p>Status: {profile.is_active ? 'Active' : 'Inactive'}</p>
                <p>Created: {formatDateTime(profile.created_at)}</p>
                <p>Updated: {formatDateTime(profile.updated_at)}</p>
              </div>
            </SurfaceCard>
            <SurfaceCard>
              <h2 className="text-xl font-bold text-white">Edit Profile</h2>
              <form className="mt-5 space-y-4" onSubmit={handleSave}>
                <Input label="Full Name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
                <Input label="Email" value={profile.email} disabled />
                <Button type="submit" isLoading={saving}>Save Changes</Button>
              </form>
            </SurfaceCard>
          </div>
        ) : null}
      </AppShell>
    </ProtectedShell>
  );
}
