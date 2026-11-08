"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { MailCheck, ArrowLeft, RefreshCw, CheckCircle2 } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "your work email";

  const [resending, setResending] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);

  const handleResend = async () => {
    if (!searchParams.get("email")) return;
    setResending(true);
    setResendMessage(null);

    try {
      const supabase = getSupabaseBrowserClient();
      await supabase.auth.resend({
        type: "signup",
        email: searchParams.get("email")!,
      });
      setResendMessage("Verification email re-sent. Please check your inbox and spam folder.");
    } catch {
      setResendMessage("Verification request queued. If an account is pending, instructions will arrive shortly.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <Link href="/" className="inline-block">
          <Logo size={32} />
        </Link>
      </div>

      <Card className="text-center">
        <CardHeader className="pb-3">
          <div className="mx-auto w-12 h-12 rounded-full bg-rf-crimson/15 border border-rf-crimson/30 flex items-center justify-center mb-2">
            <MailCheck className="w-6 h-6 text-rf-crimson" />
          </div>
          <CardTitle>Verify Your Email</CardTitle>
          <CardDescription>
            We've sent a verification link to <span className="text-rf-text font-medium">{email}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-rf-text-secondary text-left">
          <div className="p-3 rounded-md border border-rf-border bg-rf-surface/50 space-y-2">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
              <span>Click the verification link in the email to activate your account.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
              <span>Once confirmed, your workspace will be ready for site analysis.</span>
            </div>
          </div>

          {resendMessage && (
            <div className="p-2.5 rounded bg-rf-surface border border-rf-border text-xs text-rf-text">
              {resendMessage}
            </div>
          )}

          <div className="pt-2 flex flex-col gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleResend}
              disabled={resending}
              className="w-full text-xs h-9 flex items-center justify-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${resending ? "animate-spin" : ""}`} />
              <span>Resend Verification Email</span>
            </Button>

            <Link
              href="/login"
              className="w-full h-9 rounded-md border border-rf-border bg-rf-surface text-rf-text hover:bg-rf-surface/80 flex items-center justify-center gap-1.5 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Sign In</span>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <Suspense fallback={<div className="text-xs text-rf-text-muted">Loading verification details...</div>}>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
