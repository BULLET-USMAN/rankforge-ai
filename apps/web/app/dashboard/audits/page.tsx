"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  SearchCode,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Play,
  RotateCw,
  FileText,
  Lock,
  Server,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

function AuditsContent() {
  const searchParams = useSearchParams();
  const initialProjectId = searchParams.get("project_id");

  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(initialProjectId || "");
  const [targetUrl, setTargetUrl] = useState<string>("");
  const [isAuditing, setIsAuditing] = useState(false);
  const [currentJob, setCurrentJob] = useState<any | null>(null);
  const [auditHistory, setAuditHistory] = useState<any[]>([]);
  const [auditError, setAuditError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const projs = await api.listProjects();
        setProjects(projs || []);
        if (projs && projs.length > 0) {
          const activeId = initialProjectId || projs[0].id;
          setSelectedProjectId(activeId);
          const found = projs.find((p) => p.id === activeId);
          if (found) {
            setTargetUrl(found.primary_url);
            loadHistory(found.id);
          }
        }
      } catch {}
    }
    init();
  }, [initialProjectId]);

  const loadHistory = async (projectId: string) => {
    try {
      const history = await api.listProjectAudits(projectId);
      setAuditHistory(history || []);
      if (history && history.length > 0 && !currentJob) {
        setCurrentJob(history[0]);
      }
    } catch {}
  };

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedProjectId(id);
    const p = projects.find((proj) => proj.id === id);
    if (p) {
      setTargetUrl(p.primary_url);
      loadHistory(p.id);
    }
  };

  const handleRunAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuditError(null);

    if (!selectedProjectId) {
      setAuditError("Please select a website project.");
      return;
    }
    if (!targetUrl.trim()) {
      setAuditError("Target URL is required.");
      return;
    }

    setIsAuditing(true);
    try {
      const job = await api.triggerAudit({
        project_id: selectedProjectId,
        target_url: targetUrl.trim(),
        job_type: "preflight",
      });
      setCurrentJob(job);
      await loadHistory(selectedProjectId);
    } catch (err: any) {
      setAuditError(err.message || "Audit execution failed");
    } finally {
      setIsAuditing(false);
    }
  };

  const activeResult = currentJob?.results?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-rf-text tracking-tight">Technical SEO Audits</h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Deterministic HTTP inspection, SSL security, robots.txt, sitemap, and latency analysis.
          </p>
        </div>
      </div>

      {/* Runner Bar */}
      <Card className="border-rf-border bg-rf-bg-secondary">
        <CardContent className="p-4">
          <form onSubmit={handleRunAudit} className="flex flex-col md:flex-row gap-3">
            <div className="w-full md:w-64">
              <label className="text-[11px] font-medium text-rf-text-secondary block mb-1">
                Website Project
              </label>
              <select
                value={selectedProjectId}
                onChange={handleProjectSelect}
                className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:border-rf-crimson focus:outline-none"
              >
                {projects.length === 0 && <option value="">No projects registered</option>}
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.domain})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1">
              <label className="text-[11px] font-medium text-rf-text-secondary block mb-1">
                Target URL
              </label>
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                required
              />
            </div>

            <div className="flex items-end">
              <Button type="submit" disabled={isAuditing || !selectedProjectId} className="h-9 px-5">
                {isAuditing ? (
                  <>
                    <RotateCw className="w-3.5 h-3.5 mr-2 animate-spin" />
                    Inspecting...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 mr-2" />
                    Run Preflight Audit
                  </>
                )}
              </Button>
            </div>
          </form>

          {auditError && (
            <div className="mt-3 p-3 rounded bg-rf-error/15 border border-rf-error/30 text-xs text-red-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Security / Validation Error:</span> {auditError}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Grid: Audit Results & History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Detailed Audit Findings */}
        <div className="lg:col-span-2 space-y-4">
          {activeResult ? (
            <div className="space-y-4">
              {/* Score & Key Metrics Banner */}
              <div className="p-5 rounded-lg border border-rf-border bg-rf-bg-secondary grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <div className="text-[11px] uppercase tracking-wider text-rf-text-muted font-mono">
                    Health Score
                  </div>
                  <div
                    className={`text-3xl font-bold font-tabular ${
                      activeResult.score >= 80
                        ? "text-green-400"
                        : activeResult.score >= 50
                        ? "text-amber-400"
                        : "text-red-400"
                    }`}
                  >
                    {activeResult.score}
                    <span className="text-sm font-normal text-rf-text-muted">/100</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[11px] uppercase tracking-wider text-rf-text-muted font-mono">
                    HTTP Status
                  </div>
                  <div className="text-2xl font-bold font-tabular text-rf-text">
                    {activeResult.status_code || "—"}
                  </div>
                  <div className="text-[11px] text-rf-text-secondary">
                    {activeResult.status_code === 200 ? "OK" : "Status Code"}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[11px] uppercase tracking-wider text-rf-text-muted font-mono">
                    Latency
                  </div>
                  <div className="text-2xl font-bold font-tabular text-rf-text">
                    {activeResult.response_time_ms}
                    <span className="text-xs font-normal text-rf-text-secondary">ms</span>
                  </div>
                  <div className="text-[11px] text-rf-text-secondary">Time to First Byte</div>
                </div>

                <div className="space-y-1">
                  <div className="text-[11px] uppercase tracking-wider text-rf-text-muted font-mono">
                    SSL Security
                  </div>
                  <div className="text-2xl font-bold text-rf-text flex items-center gap-1.5">
                    {activeResult.ssl_info_json?.is_https ? (
                      <span className="text-green-400 text-sm font-medium">HTTPS Active</span>
                    ) : (
                      <span className="text-amber-400 text-sm font-medium">Insecure HTTP</span>
                    )}
                  </div>
                  <div className="text-[11px] text-rf-text-secondary">Transport Layer</div>
                </div>
              </div>

              {/* Protocol Checks Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-rf-text-muted" />
                      <div>
                        <div className="font-semibold text-rf-text">robots.txt Directives</div>
                        <div className="text-[11px] text-rf-text-secondary">
                          Crawling instructions file
                        </div>
                      </div>
                    </div>
                    <Badge variant={activeResult.robots_txt_found ? "success" : "secondary"}>
                      {activeResult.robots_txt_found ? "Accessible" : "Not Found"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Server className="w-4 h-4 text-rf-text-muted" />
                      <div>
                        <div className="font-semibold text-rf-text">XML Sitemap</div>
                        <div className="text-[11px] text-rf-text-secondary">
                          Standard root sitemap.xml
                        </div>
                      </div>
                    </div>
                    <Badge variant={activeResult.sitemap_found ? "success" : "secondary"}>
                      {activeResult.sitemap_found ? "Found" : "Not Found"}
                    </Badge>
                  </CardContent>
                </Card>
              </div>

              {/* Findings & Identified Issues */}
              <Card>
                <CardHeader className="py-4">
                  <CardTitle>Identified Diagnostic Findings</CardTitle>
                  <CardDescription>
                    Deterministic observations based on headers and protocol responses
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(!activeResult.issues_json || activeResult.issues_json.length === 0) ? (
                    <div className="p-6 text-center text-xs text-rf-text-secondary">
                      No technical issues discovered during this preflight inspection.
                    </div>
                  ) : (
                    activeResult.issues_json.map((issue: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-md border border-rf-border bg-rf-surface/50 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-rf-text flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                issue.severity === "critical"
                                  ? "bg-red-500"
                                  : issue.severity === "warning"
                                  ? "bg-amber-500"
                                  : "bg-blue-400"
                              }`}
                            />
                            {issue.title}
                          </span>
                          <Badge
                            variant={
                              issue.severity === "critical"
                                ? "error"
                                : issue.severity === "warning"
                                ? "warning"
                                : "outline"
                            }
                            className="uppercase text-[9px] font-mono"
                          >
                            {issue.severity}
                          </Badge>
                        </div>
                        <p className="text-rf-text-secondary leading-relaxed pl-4">
                          {issue.description}
                        </p>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Response Headers Inspector */}
              <Card>
                <CardHeader className="py-4">
                  <CardTitle>Inspected Response Headers</CardTitle>
                  <CardDescription>
                    Direct server response headers captured during preflight check
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-60 overflow-y-auto divide-y divide-rf-border/40 font-mono text-[11px]">
                    {Object.entries(activeResult.headers_json || {}).map(([key, val]: any) => (
                      <div key={key} className="px-4 py-2 flex items-center justify-between">
                        <span className="text-rf-text-secondary select-all">{key}</span>
                        <span className="text-rf-text max-w-xs truncate select-all">{val}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-12 text-center space-y-3">
                <SearchCode className="w-10 h-10 text-rf-text-muted mx-auto" />
                <div className="text-sm font-semibold text-rf-text">No audit selected</div>
                <p className="text-xs text-rf-text-secondary max-w-sm mx-auto">
                  Select a project and click &ldquo;Run Preflight Audit&rdquo; to execute a real-time
                  technical analysis.
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Col: Audit Run History */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="py-4">
              <CardTitle>Audit History</CardTitle>
              <CardDescription>Historical preflight runs for this project</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {auditHistory.length === 0 ? (
                <div className="p-6 text-center text-xs text-rf-text-secondary">
                  No audits conducted yet.
                </div>
              ) : (
                <div className="divide-y divide-rf-border/40">
                  {auditHistory.map((job) => {
                    const isSelected = currentJob?.id === job.id;
                    const res = job.results?.[0];
                    return (
                      <div
                        key={job.id}
                        onClick={() => setCurrentJob(job)}
                        className={`p-3.5 cursor-pointer text-xs transition-colors ${
                          isSelected
                            ? "bg-rf-surface border-l-2 border-rf-crimson"
                            : "hover:bg-rf-surface/40"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-rf-text">
                            {formatDate(job.created_at)}
                          </span>
                          <Badge
                            variant={job.status === "completed" ? "success" : "secondary"}
                            className="text-[9px]"
                          >
                            {job.status}
                          </Badge>
                        </div>
                        {res && (
                          <div className="flex items-center gap-3 mt-1.5 font-mono text-[11px] text-rf-text-secondary">
                            <span>Score: {res.score}</span>
                            <span>&bull;</span>
                            <span>{res.response_time_ms}ms</span>
                            <span>&bull;</span>
                            <span>HTTP {res.status_code}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function AuditsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs text-rf-text-secondary">
          Loading audit workspace...
        </div>
      }
    >
      <AuditsContent />
    </Suspense>
  );
}
