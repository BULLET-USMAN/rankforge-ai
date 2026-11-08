"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !email.includes("@")) {
      setError("Please enter a valid work email address.");
      return;
    }

    setIsLoading(true);

    try {
      const supabase = getSupabaseBrowserClient();
      await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      setIsSubmitted(true);
    } catch {
      // Always show generic success for security (prevents account enumeration)
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block">
            <Logo size={32} />
          </Link>
          <p className="text-xs text-rf-text-secondary">Password recovery portal</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Reset Password</CardTitle>
            <CardDescription>
              Enter the email associated with your RankForge account and we will send you a recovery link
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isSubmitted ? (
              <div className="space-y-4 text-center">
                <div className="mx-auto w-10 h-10 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                </div>
                <div className="space-y-1 text-xs">
                  <p className="font-medium text-rf-text">Check your inbox</p>
                  <p className="text-rf-text-secondary">
                    If an account exists for <span className="text-rf-text font-medium">{email}</span>, you will receive password reset instructions.
                  </p>
                </div>
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center gap-1.5 text-xs text-rf-text hover:text-rf-crimson transition-colors pt-2"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Return to Sign In</span>
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300">
                    {error}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text" htmlFor="email">
                    Account Email
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

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-9 flex items-center justify-center gap-1.5"
                >
                  {isLoading ? (
                    <span>Sending instructions...</span>
                  ) : (
                    <>
                      <span>Send Recovery Link</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>

                <div className="text-center pt-2">
                  <Link
                    href="/login"
                    className="inline-flex items-center gap-1 text-xs text-rf-text-secondary hover:text-rf-text transition-colors"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back to Sign In</span>
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
