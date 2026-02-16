"use client";

import { FormEvent, useState, useEffect, useCallback } from "react";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth";

type UserData = { email: string; full_name?: string | null };

type ProfileModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { user: storeUser, token } = useAuthStore();
  const [user, setUser] = useState<UserData | null>(null);
  const [fullName, setFullName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingUser, setLoadingUser] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    if (!token) return;
    setLoadingUser(true);
    try {
      const { data } = await api.get<{ email: string; full_name?: string | null }>("/auth/me");
      setUser(data);
      setFullName(data?.full_name ?? "");
    } catch {
      setUser(storeUser ? { email: storeUser.email, full_name: storeUser.full_name } : null);
      setFullName(storeUser?.full_name ?? "");
    } finally {
      setLoadingUser(false);
    }
  }, [token, storeUser]);

  useEffect(() => {
    if (isOpen && token) {
      setError(null);
      setSuccess(null);
      setCurrentPassword("");
      setNewPassword("");
      fetchUser();
    } else if (!isOpen) {
      setUser(null);
    }
  }, [isOpen, token, fetchUser]);

  useEffect(() => {
    if (user) setFullName(user.full_name ?? "");
  }, [user]);

  const handleSaveProfile = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await api.patch("/auth/me", { full_name: fullName.trim() || null });
      useAuthStore.setState({ user: { email: user.email, full_name: fullName.trim() || null } });
      setSuccess("Profile updated.");
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof d === "string" ? d : "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      setError("Enter current and new password.");
      return;
    }
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await api.post("/auth/me/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess("Password updated.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof d === "string" ? d : "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Profile">
      <div className="space-y-6">
        {loadingUser ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <>
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <Input
                label="Email"
                type="email"
                value={user?.email ?? ""}
                disabled
                showPasswordToggle={false}
              />
              <Input
                label="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your name"
              />
              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  Save changes
                </Button>
                <Button type="button" variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
              </div>
            </form>

            <hr className="border-slate-800" />

            <form onSubmit={handleChangePassword} className="space-y-4">
              <h3 className="text-sm font-medium text-slate-300">Change password</h3>
              <Input
                label="Current password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
              />
              <Input
                label="New password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                minLength={8}
              />
              <Button type="submit" variant="secondary" disabled={loading}>
                Change password
              </Button>
            </form>

            {error && <p className="text-sm text-red-400">{error}</p>}
            {success && <p className="text-sm text-emerald-400">{success}</p>}
          </>
        )}
      </div>
    </Modal>
  );
}
