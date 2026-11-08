"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Info, ArrowRight, Lock, CheckCircle2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!email || !email.includes("@")) {
      setError("Please provide a valid business email address.");
      return;
    }
    if (!password || password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setIsLoading(true);
    // In Phase 1: Authentication provider (Supabase Auth) is prepared for Phase 2.
    // Local development mode routes to /dashboard
    setTimeout(() => {
      setIsLoading(false);
      router.push("/dashboard");
    }, 400);
  };

  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block">
            <Logo size={32} />
          </Link>
          <p className="text-xs text-rf-text-secondary">
            Sign in to your organization's SEO workspace
          </p>
        </div>

        {/* Phase 1 Auth Status Notice */}
        <div className="p-3.5 rounded-lg border border-rf-border bg-rf-bg-secondary text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 font-medium text-rf-text">
            <Info className="w-3.5 h-3.5 text-rf-crimson flex-shrink-0" />
            <span>Phase 1 Architecture Notice</span>
            <Badge variant="outline" className="font-mono text-[9px] ml-auto">
              Dev Mode
            </Badge>
          </div>
          <p className="text-rf-text-secondary text-[11px] leading-relaxed">
            Full Supabase OAuth & JWT session cookies are scheduled for Phase 2. In Phase 1, form
            validation operates locally, allowing immediate developer access to the product console.
          </p>
        </div>

        {/* Login Card */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Enter your credentials to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-2.5 rounded bg-rf-error/15 border border-rf-error/30 text-xs text-red-300">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="email">
                  Work Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@agency.com"
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-rf-text" htmlFor="password">
                    Password
                  </label>
                  <span className="text-[11px] text-rf-text-muted">Min. 8 characters</span>
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                  required
                />
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Authenticating..." : "Sign In to Workspace"}
              </Button>
            </form>

            <div className="pt-4 mt-4 border-t border-rf-border/50 text-center">
              <Link
                href="/dashboard"
                className="text-xs text-rf-text-secondary hover:text-rf-text flex items-center justify-center gap-1.5"
              >
                <span>Direct Access (Bypass Login for Local Inspection)</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Footer Link */}
        <div className="text-center text-xs text-rf-text-secondary">
          Don't have an organization workspace yet?{" "}
          <Link href="/register" className="text-rf-crimson hover:underline font-medium">
            Register Workspace
          </Link>
        </div>
      </div>
    </div>
  );
}
