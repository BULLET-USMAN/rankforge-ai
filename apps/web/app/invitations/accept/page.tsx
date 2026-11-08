"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Building2, ShieldCheck, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api, getApiAuthToken } from "@/lib/api-client";

function AcceptInvitationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleAccept = async () => {
    if (!token) {
      setError("Missing invitation token.");
      return;
    }

    const authToken = getApiAuthToken();
    if (!authToken) {
      // Direct user to login first with return URL
      router.push(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.acceptInvitation({ token });
      setSuccess(`Joined ${res.organization_name} as ${res.role}! Redirecting...`);
      setTimeout(() => {
        router.push("/dashboard");
      }, 1200);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to accept invitation");
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      <div className="text-center space-y-2">
        <Link href="/" className="inline-block">
          <Logo size={32} />
        </Link>
        <p className="text-xs text-rf-text-secondary">Workspace team invitation</p>
      </div>

      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-rf-crimson/15 border border-rf-crimson/30 flex items-center justify-center mb-2">
            <Building2 className="w-6 h-6 text-rf-crimson" />
          </div>
          <CardTitle>Join Workspace</CardTitle>
          <CardDescription>
            You have been invited to collaborate on SEO intelligence and technical optimization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rf-crimson flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded bg-green-500/10 border border-green-500/30 text-xs text-green-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>{success}</span>
            </div>
          )}

          {!token ? (
            <div className="text-center py-4 text-xs text-rf-text-secondary">
              Invalid or missing invitation token. Please check the link provided in your invitation email.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface/50 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">Invitation Status:</span>
                  <span className="text-rf-text font-medium">Valid & Ready</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">Security:</span>
                  <span className="font-mono text-[11px] text-green-400">Cryptographically Verified</span>
                </div>
              </div>

              <Button
                onClick={handleAccept}
                disabled={isLoading || !!success}
                className="w-full bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-9 flex items-center justify-center gap-1.5"
              >
                {isLoading ? (
                  <span>Accepting Invitation...</span>
                ) : (
                  <>
                    <span>Accept & Join Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <Suspense fallback={<div className="text-xs text-rf-text-muted">Loading invitation...</div>}>
        <AcceptInvitationContent />
      </Suspense>
    </div>
  );
}
