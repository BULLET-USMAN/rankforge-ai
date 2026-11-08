"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCw,
  Globe,
  Sparkles,
  Zap,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type Organization, type WebsiteProject } from "@/lib/api-client";
import TechnicalAuditDashboard from "@/components/audits/technical-audit-dashboard";
import Link from "next/link";

function AuditsContent() {
  const searchParams = useSearchParams();
  const initialProjectId = searchParams.get("project_id");

  // Mode: "technical_engine" (Phase 4) or "preflight_quick" (Phase 1 legacy)
  const [auditMode, setAuditMode] = useState<"technical_engine" | "preflight_quick">("technical_engine");

  // Workspace & Websites
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string>("");
  const [websites, setWebsites] = useState<WebsiteProject[]>([]);
  const [selectedWebsiteId, setSelectedWebsiteId] = useState<string>(initialProjectId || "");
  const [isLoading, setIsLoading] = useState(true);

  // Preflight legacy state
  const [targetUrl, setTargetUrl] = useState<string>("");
  const [isAuditingPreflight, setIsAuditingPreflight] = useState(false);
  const [preflightJob, setPreflightJob] = useState<any | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);

  // 1. Initial Load: Organizations & Websites
  useEffect(() => {
    async function loadData() {
      try {
        const orgs = await api.listOrganizations();
        setOrganizations(orgs || []);
        if (orgs && orgs.length > 0) {
          const orgId = orgs[0].id;
          setCurrentOrgId(orgId);

          const sites = await api.listWebsites(orgId);
          setWebsites(sites || []);

          if (sites && sites.length > 0) {
            const activeId = initialProjectId && sites.some((s) => s.id === initialProjectId)
              ? initialProjectId
              : sites[0].id;
            setSelectedWebsiteId(activeId);
            const found = sites.find((s) => s.id === activeId);
            if (found) {
              setTargetUrl(found.primary_url);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load organizations or websites", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [initialProjectId]);

  // When Org changes
  const handleOrgChange = async (orgId: string) => {
    setCurrentOrgId(orgId);
    try {
      const sites = await api.listWebsites(orgId);
      setWebsites(sites || []);
      if (sites && sites.length > 0) {
        setSelectedWebsiteId(sites[0].id);
        setTargetUrl(sites[0].primary_url);
      } else {
        setSelectedWebsiteId("");
        setTargetUrl("");
      }
    } catch (err) {
      console.error("Failed to fetch websites for org", err);
    }
  };

  const handleWebsiteChange = (siteId: string) => {
    setSelectedWebsiteId(siteId);
    const site = websites.find((s) => s.id === siteId);
    if (site) {
      setTargetUrl(site.primary_url);
    }
  };

  // Run Preflight Audit (Legacy)
  const handleRunPreflight = async (e: React.FormEvent) => {
    e.preventDefault();
    setPreflightError(null);
    if (!selectedWebsiteId) {
      setPreflightError("Please select a website project.");
      return;
    }
    if (!targetUrl.trim()) {
      setPreflightError("Target URL is required.");
      return;
    }

    setIsAuditingPreflight(true);
    try {
      const job = await api.triggerAudit({
        project_id: selectedWebsiteId,
        target_url: targetUrl.trim(),
        job_type: "preflight",
      });
      setPreflightJob(job);
    } catch (err: any) {
      setPreflightError(err.message || "Preflight audit failed");
    } finally {
      setIsAuditingPreflight(false);
    }
  };

  const activeWebsite = websites.find((s) => s.id === selectedWebsiteId);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-rf-text tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-rf-crimson" />
            <span>Technical SEO Audits</span>
          </h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Comprehensive deterministic SEO auditing engine analyzing crawl snapshots across 8 technical categories.
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-rf-surface border border-rf-border rounded-lg text-xs">
          <button
            onClick={() => setAuditMode("technical_engine")}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              auditMode === "technical_engine"
                ? "bg-rf-crimson text-white"
                : "text-rf-text-secondary hover:text-rf-text"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Audit Engine (Phase 4)</span>
          </button>
          <button
            onClick={() => setAuditMode("preflight_quick")}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              auditMode === "preflight_quick"
                ? "bg-rf-crimson text-white"
                : "text-rf-text-secondary hover:text-rf-text"
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Quick Single-URL Check</span>
          </button>
        </div>
      </div>

      {/* Website Project & Workspace Selector Bar */}
      <Card className="border-rf-border bg-rf-bg-secondary">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-rf-text-secondary block mb-1">
                Workspace / Organization
              </label>
              <select
                value={currentOrgId}
                onChange={(e) => handleOrgChange(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:border-rf-crimson focus:outline-none"
              >
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-medium text-rf-text-secondary block mb-1">
                Website Project
              </label>
              <select
                value={selectedWebsiteId}
                onChange={(e) => handleWebsiteChange(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:border-rf-crimson focus:outline-none"
              >
                {websites.length === 0 ? (
                  <option value="">No website projects registered</option>
                ) : (
                  websites.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name} ({w.domain}) {w.is_verified ? "• Verified" : "• Pending"}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* No Websites State */}
      {!isLoading && websites.length === 0 && (
        <div className="p-8 text-center rounded-lg border border-rf-border bg-rf-surface/40 space-y-3">
          <Globe className="w-8 h-8 text-rf-crimson mx-auto" />
          <h3 className="text-sm font-semibold text-rf-text">No Website Projects Found</h3>
          <p className="text-xs text-rf-text-secondary max-w-sm mx-auto">
            Add a website project to your workspace and complete domain ownership verification to run technical SEO audits.
          </p>
          <Link
            href="/dashboard/websites"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs rounded-md transition-colors"
          >
            Add Website Project
          </Link>
        </div>
      )}

      {/* MODE 1: Full Technical SEO Audit Engine */}
      {auditMode === "technical_engine" && activeWebsite && (
        <TechnicalAuditDashboard
          orgId={currentOrgId}
          websiteId={activeWebsite.id}
          domain={activeWebsite.domain}
          isVerified={activeWebsite.is_verified}
        />
      )}

      {/* MODE 2: Preflight Single-URL Check (Legacy) */}
      {auditMode === "preflight_quick" && activeWebsite && (
        <div className="space-y-4">
          <Card className="border-rf-border bg-rf-surface/50">
            <CardContent className="p-4">
              <form onSubmit={handleRunPreflight} className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <label className="text-[11px] font-medium text-rf-text-secondary block mb-1">
                    Target Inspection URL
                  </label>
                  <input
                    type="url"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-bg text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                    required
                  />
                </div>
                <div className="flex items-end">
                  <Button type="submit" disabled={isAuditingPreflight} className="h-9 px-4 text-xs bg-rf-crimson hover:bg-rf-crimson-hover text-white">
                    {isAuditingPreflight ? (
                      <>
                        <RotateCw className="w-3.5 h-3.5 mr-2 animate-spin" />
                        Inspecting...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 mr-2" />
                        Run Preflight
                      </>
                    )}
                  </Button>
                </div>
              </form>

              {preflightError && (
                <div className="mt-3 p-3 rounded bg-rf-error/15 border border-rf-error/30 text-xs text-red-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Error:</span> {preflightError}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {preflightJob && preflightJob.results && preflightJob.results[0] && (
            <Card className="border-rf-border bg-rf-surface/80 p-4 space-y-2 text-xs">
              <div className="font-semibold text-rf-text">Preflight Inspection Result</div>
              <div className="font-mono text-rf-text-secondary">
                URL: {preflightJob.results[0].url} • Status: {preflightJob.results[0].status_code} • Score: {preflightJob.results[0].score}/100
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

export default function AuditsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-xs text-rf-text-muted">Loading audit dashboard...</div>}>
      <AuditsContent />
    </Suspense>
  );
}
