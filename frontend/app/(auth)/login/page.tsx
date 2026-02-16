"use client";

import Link from "next/link";
import { FormEvent, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/auth";
import { api } from "@/lib/api-client";

type ForgotStep = "email" | "otp" | null;

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loading, error, clearError } = useAuthStore();
  const showRegistered = searchParams.get("registered") === "1";
  const showPasswordReset = searchParams.get("reset") === "1";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [forgotStep, setForgotStep] = useState<ForgotStep>(null);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotPassword, setForgotPassword] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await login(email, password);
    if (!useAuthStore.getState().error) {
      router.push("/dashboard");
    }
  }

  async function handleForgotEmail(e: FormEvent) {
    e.preventDefault();
    setForgotError(null);
    setForgotLoading(true);
    try {
      await api.post("/auth/forgot-password", { email: forgotEmail });
      setForgotStep("otp");
    } catch {
      setForgotError("Failed to send OTP. Try again.");
    } finally {
      setForgotLoading(false);
    }
  }

  async function handleForgotOtp(e: FormEvent) {
    e.preventDefault();
    setForgotError(null);
    setForgotLoading(true);
    try {
      await api.post("/auth/forgot-password/verify", {
        email: forgotEmail,
        otp: forgotOtp,
        new_password: forgotPassword,
      });
      router.push("/login?reset=1");
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setForgotError(typeof d === "string" ? d : "Invalid or expired OTP. Try again.");
    } finally {
      setForgotLoading(false);
    }
  }

  if (forgotStep === "email") {
    return (
      <div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4">
        <Card className="w-full max-w-md space-y-6">
          <div>
            <h1 className="text-xl font-semibold text-slate-100">Forgot password?</h1>
            <p className="mt-1 text-sm text-slate-400">
              Enter your email to receive a one-time code.
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleForgotEmail}>
            <Input
              label="Email"
              type="email"
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
              required
            />
            {forgotError && <p className="text-sm text-red-400">{forgotError}</p>}
            <div className="flex gap-2">
              <Button type="submit" className="flex-1" disabled={forgotLoading}>
                {forgotLoading ? "Sending…" : "Send OTP"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setForgotStep(null);
                  setForgotError(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </div>
    );
  }

  if (forgotStep === "otp") {
    return (
      <div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4">
        <Card className="w-full max-w-md space-y-6">
          <div>
            <h1 className="text-xl font-semibold text-slate-100">Enter OTP</h1>
            <p className="mt-1 text-sm text-slate-400">
              Check your email for the code, then set a new password.
            </p>
            <p className="mt-1 text-xs text-slate-500">
              (Mocked: use <strong>123456</strong> for testing)
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleForgotOtp}>
            <Input
              label="OTP"
              value={forgotOtp}
              onChange={(e) => setForgotOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="123456"
              maxLength={6}
            />
            <Input
              label="New password"
              type="password"
              value={forgotPassword}
              onChange={(e) => setForgotPassword(e.target.value)}
              minLength={8}
              required
            />
            {forgotError && <p className="text-sm text-red-400">{forgotError}</p>}
            <div className="flex gap-2">
              <Button type="submit" className="flex-1" disabled={forgotLoading}>
                {forgotLoading ? "Updating…" : "Set new password"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setForgotStep("email");
                  setForgotOtp("");
                  setForgotPassword("");
                  setForgotError(null);
                }}
              >
                Back
              </Button>
            </div>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4">
      <Card className="w-full max-w-md space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Welcome back</h1>
          <p className="mt-1 text-sm text-slate-400">
            Sign in to StockSentinel to view your dashboard.
          </p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {showRegistered && (
            <p className="text-sm text-emerald-400" aria-live="polite">
              Account created successfully. Please log in.
            </p>
          )}
          {showPasswordReset && (
            <p className="text-sm text-emerald-400" aria-live="polite">
              Password reset successfully. Please log in.
            </p>
          )}
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              clearError();
            }}
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              clearError();
            }}
            required
          />
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setForgotStep("email")}
              className="text-xs text-slate-400 transition hover:text-emerald-400"
            >
              Forgot password?
            </button>
          </div>
          {error && (
            <p className="text-sm text-red-400" aria-live="polite">
              {error}
            </p>
          )}
          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>
        <p className="text-center text-sm text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-emerald-500 hover:text-emerald-400">
            Sign up
          </Link>
        </p>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4">Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}

