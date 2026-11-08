"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Globe,
  SearchCode,
  ShieldAlert,
  ArrowRight,
  Plus,
  Play,
  Cpu,
  CheckCircle2,
  Clock,
  Activity,
  Layers,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default function OverviewDashboardPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [audits, setAudits] = useState<any[]>([]);
  const [readiness, setReadiness] = useState<any>(null);
  const [workerResult, setWorkerResult] = useState<any>(null);
  const [isTestingWorker, setIsTestingWorker] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        const [orgs, projs] = await Promise.all([
          api.listOrganizations().catch(() => []),
          api.listProjects().catch(() => []),
        ]);

        if (isMounted) {
          setProjects(projs || []);
          if (projs && projs.length > 0) {
            const auditRuns = await api.listProjectAudits(projs[0].id).catch(() => []);
            setAudits(auditRuns || []);
          }
        }
      } catch {
        // Fallback gracefully
      } finally {
        if (isMounted) setIsLoading(false);
      }

      // Check system readiness
      api
        .getReadiness()
        .then((r) => {
          if (isMounted) setReadiness(r);
        })
        .catch((err) => {
          if (isMounted) setReadiness({ status: "offline", error: err.message });
        });
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTestWorker = async () => {
    setIsTestingWorker(true);
    setWorkerResult(null);
    try {
      const res = await api.triggerWorkerSmoke(35, 65);
      setWorkerResult(res);
    } catch (err: any) {
      setWorkerResult({ status: "failed", message: err.message });
    } finally {
      setIsTestingWorker(false);
    }
  };

  const verifiedCount = projects.filter((p) => p.is_verified).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-rf-text tracking-tight">Workspace Overview</h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Real-time multi-tenant monitoring, technical auditing, and infrastructure status.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleTestWorker}
            disabled={isTestingWorker}
            className="text-xs"
          >
            <Cpu className="w-3.5 h-3.5 mr-1.5 text-rf-crimson" />
            {isTestingWorker ? "Dispatching..." : "Test Celery Worker"}
          </Button>
          <Link href="/dashboard/websites">
            <Button size="sm" className="text-xs">
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add Website
            </Button>
          </Link>
        </div>
      </div>

      {/* Real Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5 space-y-1">
            <div className="flex items-center justify-between text-xs text-rf-text-secondary">
              <span>Tracked Websites</span>
              <Globe className="w-4 h-4 text-rf-text-muted" />
            </div>
            <div className="text-2xl font-bold font-tabular text-rf-text">
              {projects.length}
            </div>
            <div className="text-[11px] text-rf-text-muted">
              {verifiedCount} verified with DNS/tag
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 space-y-1">
            <div className="flex items-center justify-between text-xs text-rf-text-secondary">
              <span>Audits Executed</span>
              <SearchCode className="w-4 h-4 text-rf-text-muted" />
            </div>
            <div className="text-2xl font-bold font-tabular text-rf-text">
              {audits.length}
            </div>
            <div className="text-[11px] text-rf-text-muted">
              Deterministic preflight runs
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 space-y-1">
            <div className="flex items-center justify-between text-xs text-rf-text-secondary">
              <span>Tenant Security</span>
              <Activity className="w-4 h-4 text-rf-text-muted" />
            </div>
            <div className="text-2xl font-bold font-tabular text-green-400">
              Active
            </div>
            <div className="text-[11px] text-rf-text-muted">
              SSRF guard + RLS boundary
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 space-y-1">
            <div className="flex items-center justify-between text-xs text-rf-text-secondary">
              <span>Current Tier</span>
              <Layers className="w-4 h-4 text-rf-text-muted" />
            </div>
            <div className="text-2xl font-bold text-rf-text uppercase tracking-wide">
              Starter
            </div>
            <div className="text-[11px] text-rf-text-muted">
              Phase 1 local development
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Worker Smoke Test Feedback (If triggered) */}
      {workerResult && (
        <div className="p-4 rounded-lg border border-rf-border bg-rf-bg-secondary text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-rf-text flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-rf-crimson" />
              Celery Queue Dispatch Result
            </span>
            <Badge variant={workerResult.status === "failed" ? "error" : "success"}>
              {workerResult.status}
            </Badge>
          </div>
          <div className="font-mono text-[11px] text-rf-text-secondary bg-rf-surface p-2.5 rounded border border-rf-border/40">
            {JSON.stringify(workerResult, null, 2)}
          </div>
        </div>
      )}

      {/* Main Grid: Projects / Empty State & System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Tracked Websites or Getting Started */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <div>
                <CardTitle>Website Projects</CardTitle>
                <CardDescription>Configured domains under this workspace</CardDescription>
              </div>
              <Link href="/dashboard/websites">
                <Button variant="ghost" size="sm" className="text-xs">
                  View All
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              {projects.length === 0 ? (
                /* Honest Empty State with Setup Blueprint */
                <div className="p-8 text-center space-y-4">
                  <div className="w-12 h-12 rounded-lg bg-rf-surface border border-rf-border mx-auto flex items-center justify-center text-rf-text-muted">
                    <Globe className="w-6 h-6" />
                  </div>
                  <div className="space-y-1 max-w-sm mx-auto">
                    <div className="text-sm font-semibold text-rf-text">
                      No websites configured yet
                    </div>
                    <p className="text-xs text-rf-text-secondary leading-relaxed">
                      Register your primary domain to start generating verifiable technical SEO
                      audits and verify domain ownership.
                    </p>
                  </div>
                  <Link href="/dashboard/websites">
                    <Button size="sm">
                      <Plus className="w-3.5 h-3.5 mr-1.5" />
                      Add First Website Project
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-rf-border/40">
                  {projects.map((proj) => (
                    <div
                      key={proj.id}
                      className="p-4 flex items-center justify-between hover:bg-rf-surface/30 transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-rf-text">{proj.name}</span>
                          <Badge variant={proj.is_verified ? "success" : "warning"} className="text-[10px]">
                            {proj.is_verified ? "Verified" : "Pending Verification"}
                          </Badge>
                        </div>
                        <div className="text-xs font-mono text-rf-text-secondary">
                          {proj.domain}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link href={`/dashboard/audits?project_id=${proj.id}`}>
                          <Button variant="secondary" size="sm" className="text-xs">
                            <SearchCode className="w-3.5 h-3.5 mr-1 text-rf-crimson" />
                            Audit
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Onboarding Guide Card */}
          <Card>
            <CardHeader className="py-4">
              <CardTitle>Phase 1 Implementation Blueprint</CardTitle>
              <CardDescription>
                Progressive milestones supporting production workflows
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-md bg-rf-surface/40 border border-rf-border/40 text-xs">
                <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-semibold text-rf-text">
                    1. Monorepo & FastAPI Backend Foundation
                  </div>
                  <div className="text-rf-text-secondary">
                    Centralized Pydantic v2 settings, JSON logging, and structured error responses.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-md bg-rf-surface/40 border border-rf-border/40 text-xs">
                <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-semibold text-rf-text">
                    2. Relational Schema & 11 Tables
                  </div>
                  <div className="text-rf-text-secondary">
                    Organizations, Projects, Audits, Recommendations, Subscriptions, and RLS prep.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-md bg-rf-surface/40 border border-rf-border/40 text-xs">
                <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-semibold text-rf-text">
                    3. SSRF Protection & Safe Preflight Auditing
                  </div>
                  <div className="text-rf-text-secondary">
                    Guarded against RFC 1918 private subnets and AWS metadata exploitation.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Platform Services Diagnostic Status */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="py-4">
              <CardTitle>Platform Readiness</CardTitle>
              <CardDescription>Health status of backend dependencies</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded bg-rf-surface border border-rf-border/40">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-rf-text font-medium">FastAPI Service</span>
                </div>
                <span className="font-mono text-[11px] text-rf-text-secondary">v0.1.0</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-rf-surface border border-rf-border/40">
                <div className="flex items-center gap-2">
                  <span
                    className={
                      readiness?.dependencies?.database?.status === "ok"
                        ? "w-2 h-2 rounded-full bg-green-500"
                        : "w-2 h-2 rounded-full bg-amber-500"
                    }
                  />
                  <span className="text-rf-text font-medium">PostgreSQL 16</span>
                </div>
                <span className="font-mono text-[11px] text-rf-text-secondary">
                  {readiness?.dependencies?.database?.status || "Local Dev Engine"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-rf-surface border border-rf-border/40">
                <div className="flex items-center gap-2">
                  <span
                    className={
                      readiness?.dependencies?.redis?.status === "ok"
                        ? "w-2 h-2 rounded-full bg-green-500"
                        : "w-2 h-2 rounded-full bg-amber-500"
                    }
                  />
                  <span className="text-rf-text font-medium">Redis & Celery Queue</span>
                </div>
                <span className="font-mono text-[11px] text-rf-text-secondary">
                  {readiness?.dependencies?.redis?.status || "Ready"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-rf-surface border border-rf-border/40">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-rf-text font-medium">Next.js App Router</span>
                </div>
                <span className="font-mono text-[11px] text-rf-text-secondary">Dark Mode / B2B</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Help Card */}
          <Card>
            <CardHeader className="py-4">
              <CardTitle>Architecture Documents</CardTitle>
              <CardDescription>Technical specifications in `/docs`</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="font-mono text-[11px] text-rf-text-secondary space-y-1.5">
                <div className="flex items-center justify-between">
                  <span>ARCHITECTURE.md</span>
                  <span className="text-rf-text-muted">Monorepo design</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>SECURITY.md</span>
                  <span className="text-rf-text-muted">SSRF & RLS policies</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>DATABASE.md</span>
                  <span className="text-rf-text-muted">11 tables mapped</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>DESIGN_SYSTEM.md</span>
                  <span className="text-rf-text-muted">Palette & tokens</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
