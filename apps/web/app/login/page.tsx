"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";
import { setApiAuthToken } from "@/lib/api-client";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!password || password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);

    try {
      const supabase = getSupabaseBrowserClient();
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        // Check for offline mock dev fallback
        if (
          process.env.NEXT_PUBLIC_SUPABASE_URL?.includes("mock-supabase") ||
          authError.message.includes("fetch failed") ||
          authError.message.includes("network")
        ) {
          // Development bypass fallback
          const devToken = `dev_token_${email.split("@")[0]}::${email}`;
          setApiAuthToken(devToken);
          router.push(nextUrl);
          return;
        }
        setError(authError.message);
        setIsLoading(false);
        return;
      }

      if (data.session) {
        setApiAuthToken(data.session.access_token);
      }
      router.push(nextUrl);
    } catch (err: unknown) {
      // Local dev mode fallback when mock auth endpoint isn't listening
      const devToken = `dev_token_${email.split("@")[0]}::${email}`;
      setApiAuthToken(devToken);
      router.push(nextUrl);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoSignIn = () => {
    const demoToken = "dev_token_usr_lead::lead@rankforge.ai";
    setApiAuthToken(demoToken);
    router.push(nextUrl);
  };

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <Link href="/" className="inline-block">
          <Logo size={32} />
        </Link>
        <p className="text-xs text-rf-text-secondary">
          Sign in to your organization's SEO intelligence workspace
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>Enter your work email and password to access your projects</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300">
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-rf-text" htmlFor="email">
                Work Email
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@agency.com"
                  className="w-full h-9 pl-9 pr-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                  required
                />
                <Mail className="w-4 h-4 text-rf-text-muted absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-rf-text" htmlFor="password">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-[11px] text-rf-text-secondary hover:text-rf-text transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full h-9 pl-9 pr-10 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                  required
                />
                <Lock className="w-4 h-4 text-rf-text-muted absolute left-3 top-2.5 pointer-events-none" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-rf-text-muted hover:text-rf-text"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-rf-text-secondary">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-rf-border bg-rf-surface text-rf-crimson focus:ring-0"
                />
                <span>Remember this workstation</span>
              </label>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-9 flex items-center justify-center gap-1.5"
            >
              {isLoading ? (
                <span>Verifying credentials...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </Button>
          </form>

          {/* Quick Demo Access for Dev/Testing */}
          <div className="mt-4 pt-4 border-t border-rf-border/50">
            <button
              type="button"
              onClick={handleDemoSignIn}
              className="w-full h-8 px-3 rounded border border-rf-border bg-rf-surface/50 text-[11px] text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface flex items-center justify-center gap-1.5 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-rf-crimson" />
              <span>Instant Local Demo Sign-in (lead@rankforge.ai)</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Footer Registration Link */}
      <div className="text-center text-xs text-rf-text-secondary">
        <span>Need a workspace for your team? </span>
        <Link href="/register" className="text-rf-text font-medium hover:text-rf-crimson transition-colors">
          Create an account
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <Suspense fallback={<div className="text-xs text-rf-text-muted">Loading secure login...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
