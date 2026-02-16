"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, loading, error, clearError } = useAuthStore();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await register(email, password, fullName);
    if (!useAuthStore.getState().error) {
      router.push("/login?registered=1");
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-56px)] items-center justify-center px-4">
      <Card className="w-full max-w-md space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Create your account</h1>
          <p className="mt-1 text-sm text-slate-400">
            Start monitoring sentiment and predictions for your favorite stocks.
          </p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <Input
            label="Full name"
            value={fullName}
            onChange={(e) => {
              setFullName(e.target.value);
              clearError();
            }}
          />
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
            {loading ? "Creating account..." : "Sign up"}
          </Button>
        </form>
        <p className="text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link href="/login" className="text-emerald-500 hover:text-emerald-400">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}

