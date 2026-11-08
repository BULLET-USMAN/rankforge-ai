"use client";

import React, { useState, useEffect } from "react";
import { CreditCard, Check, AlertCircle, Sparkles, Layers, ShieldCheck, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";

export default function BillingPage() {
  const [projectCount, setProjectCount] = useState(0);

  useEffect(() => {
    api.listProjects().then((p) => setProjectCount(p ? p.length : 0)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-rf-text tracking-tight">Subscription & Usage</h1>
        <p className="text-xs text-rf-text-secondary mt-1">
          Monitor resource consumption, workspace quotas, and billing tier entitlements.
        </p>
      </div>

      {/* Phase 1 Stripe Notice */}
      <div className="p-4 rounded-lg border border-rf-border bg-rf-bg-secondary text-xs space-y-1.5">
        <div className="flex items-center gap-2 font-medium text-rf-text">
          <CreditCard className="w-4 h-4 text-rf-crimson flex-shrink-0" />
          <span>Billing Environment Status</span>
          <Badge variant="outline" className="font-mono text-[9px] ml-auto">
            Sandbox Mode
          </Badge>
        </div>
        <p className="text-rf-text-secondary text-[11px] leading-relaxed">
          Production Stripe Customer Portal and webhook event ingestion are scheduled for Phase 2.
          During Phase 1 local development, all workspaces operate under the unlimited Developer Starter
          profile. No credit card is required.
        </p>
      </div>

      {/* Usage Quota Card */}
      <Card>
        <CardHeader className="py-4">
          <CardTitle>Workspace Usage Quotas</CardTitle>
          <CardDescription>Current billing cycle resource consumption</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3.5 rounded-md bg-rf-surface border border-rf-border/40 space-y-1">
              <div className="text-[11px] text-rf-text-secondary">Monitored Domains</div>
              <div className="text-xl font-bold font-tabular text-rf-text">
                {projectCount} <span className="text-xs font-normal text-rf-text-muted">/ 5 sites</span>
              </div>
              <div className="w-full bg-rf-bg h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-rf-crimson h-full rounded-full"
                  style={{ width: `${Math.min(100, (projectCount / 5) * 100)}%` }}
                />
              </div>
            </div>

            <div className="p-3.5 rounded-md bg-rf-surface border border-rf-border/40 space-y-1">
              <div className="text-[11px] text-rf-text-secondary">Preflight Audits</div>
              <div className="text-xl font-bold font-tabular text-rf-text">
                Unlimited <span className="text-xs font-normal text-rf-text-muted">(Local Dev)</span>
              </div>
              <div className="w-full bg-rf-bg h-1.5 rounded-full overflow-hidden">
                <div className="bg-green-500 h-full rounded-full" style={{ width: "20%" }} />
              </div>
            </div>

            <div className="p-3.5 rounded-md bg-rf-surface border border-rf-border/40 space-y-1">
              <div className="text-[11px] text-rf-text-secondary">Background Tasks</div>
              <div className="text-xl font-bold font-tabular text-rf-text">
                Active <span className="text-xs font-normal text-rf-text-muted">(Celery/Redis)</span>
              </div>
              <div className="w-full bg-rf-bg h-1.5 rounded-full overflow-hidden">
                <div className="bg-green-500 h-full rounded-full" style={{ width: "15%" }} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Plan Tiers Grid */}
      <div className="space-y-3">
        <div className="text-xs font-semibold uppercase tracking-wider text-rf-text-muted">
          Available Subscription Tiers
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Starter Plan */}
          <Card className="border-rf-crimson/50 bg-rf-bg-secondary flex flex-col justify-between">
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <Badge variant="crimson">Current Tier</Badge>
                <span className="font-mono text-xs text-rf-text-muted">$0/mo</span>
              </div>
              <CardTitle className="pt-2 text-base">Starter</CardTitle>
              <CardDescription>For founders and individual site operators</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs flex-1">
              <ul className="space-y-2 text-rf-text-secondary">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  <span>Up to 5 monitored domains</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  <span>Deterministic preflight auditing</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  <span>DNS & HTML meta verification</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  <span>JSON & CSV exports</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Professional Plan */}
          <Card className="border-rf-border bg-rf-bg-secondary flex flex-col justify-between opacity-80">
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <Badge variant="outline">Phase 2</Badge>
                <span className="font-mono text-xs text-rf-text-muted">$79/mo</span>
              </div>
              <CardTitle className="pt-2 text-base">Professional</CardTitle>
              <CardDescription>For growing SaaS & e-commerce brands</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs flex-1">
              <ul className="space-y-2 text-rf-text-secondary">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Up to 25 monitored domains</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Google Search Console sync</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>AI optimization recommendations</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Automated weekly scans</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Agency Plan */}
          <Card className="border-rf-border bg-rf-bg-secondary flex flex-col justify-between opacity-80">
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <Badge variant="outline">Phase 2</Badge>
                <span className="font-mono text-xs text-rf-text-muted">$249/mo</span>
              </div>
              <CardTitle className="pt-2 text-base">Agency</CardTitle>
              <CardDescription>For agencies & multi-client consultants</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs flex-1">
              <ul className="space-y-2 text-rf-text-secondary">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Unlimited client projects</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>White-label PDF reports</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Automated CMS remediation</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-rf-text-muted flex-shrink-0" />
                  <span>Role-based team workspaces</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
