"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Play,
  RotateCw,
  Search,
  Filter,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Info,
  Calendar,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Check,
  Code2,
  HelpCircle,
  X,
  FileText,
  Clock,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  api,
  type SEOAuditRun,
  type SEOAuditFinding,
  type SEOAuditCategoryScore,
  type SEOAuditComparison,
  type AuditedPage,
  type CrawlJob,
} from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

interface TechnicalAuditDashboardProps {
  orgId: string;
  websiteId: string;
  domain: string;
  isVerified: boolean;
  availableCrawls?: CrawlJob[];
}

const CATEGORY_NAMES: Record<string, string> = {
  indexability: "Indexability",
  links_http: "Links & HTTP",
  canonical: "Canonical URLs",
  metadata: "Metadata & Tags",
  site_structure: "Site Structure",
  headings: "Heading Hierarchy",
  images: "Image Optimization",
  structured_data_sitemaps: "Schema & Sitemaps",
};

export default function TechnicalAuditDashboard({
  orgId,
  websiteId,
  domain,
  isVerified,
  availableCrawls = [],
}: TechnicalAuditDashboardProps) {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<"issues" | "pages" | "history">("issues");

  // Audits state
  const [audits, setAudits] = useState<SEOAuditRun[]>([]);
  const [currentAudit, setCurrentAudit] = useState<SEOAuditRun | null>(null);
  const [categoryScores, setCategoryScores] = useState<SEOAuditCategoryScore[]>([]);
  const [findings, setFindings] = useState<SEOAuditFinding[]>([]);
  const [totalFindings, setTotalFindings] = useState<number>(0);
  const [auditedPages, setAuditedPages] = useState<AuditedPage[]>([]);

  // Filtering state
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [findingsPage, setFindingsPage] = useState<number>(1);
  const [expandedFindingId, setExpandedFindingId] = useState<string | null>(null);

  // Inspector & Comparison state
  const [inspectingPage, setInspectingPage] = useState<AuditedPage | null>(null);
  const [comparison, setComparison] = useState<SEOAuditComparison | null>(null);
  const [compareTargetId, setCompareTargetId] = useState<string>("");
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [showHowScoreModal, setShowHowScoreModal] = useState<boolean>(false);

  // Execution state
  const [isRunningAudit, setIsRunningAudit] = useState<boolean>(false);
  const [selectedCrawlId, setSelectedCrawlId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // 1. Load Audits History
  const loadAudits = useCallback(async () => {
    if (!orgId || !websiteId) return;
    try {
      const res = await api.listWebsiteSEOAudits(orgId, websiteId, 1, 20);
      setAudits(res.items || []);
      if (res.items && res.items.length > 0) {
        // Select latest audit if current not set
        if (!currentAudit) {
          setCurrentAudit(res.items[0]);
        }
      }
    } catch (err: unknown) {
      console.error("Failed to load SEO audits", err);
    }
  }, [orgId, websiteId, currentAudit]);

  useEffect(() => {
    loadAudits();
  }, [loadAudits]);

  // 2. Load Details for Current Audit
  useEffect(() => {
    if (!currentAudit || !orgId) return;

    // Load category scores
    api
      .getSEOAuditCategoryScores(orgId, currentAudit.id)
      .then((scores) => setCategoryScores(scores || []))
      .catch((err) => console.error("Failed to load category scores", err));

    // Load audited pages
    api
      .listAuditedPages(orgId, currentAudit.id)
      .then((pages) => setAuditedPages(pages || []))
      .catch((err) => console.error("Failed to load audited pages", err));
  }, [currentAudit, orgId]);

  // 3. Load Findings with Filters
  useEffect(() => {
    if (!currentAudit || !orgId) return;

    const params: Record<string, any> = {
      page: findingsPage,
      page_size: 50,
    };
    if (categoryFilter !== "all") params.category = categoryFilter;
    if (severityFilter !== "all") params.severity = severityFilter;
    if (searchQuery.trim()) params.search = searchQuery.trim();

    api
      .listSEOAuditFindings(orgId, currentAudit.id, params)
      .then((res) => {
        setFindings(res.items || []);
        setTotalFindings(res.total || 0);
      })
      .catch((err) => console.error("Failed to load findings", err));
  }, [currentAudit, orgId, categoryFilter, severityFilter, searchQuery, findingsPage]);

  // 4. Trigger Audit Execution
  const handleTriggerAudit = async () => {
    if (!orgId || !websiteId) return;
    if (!isVerified) {
      setError("Website ownership verification is required before running technical SEO audits.");
      return;
    }

    setIsRunningAudit(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const newAudit = await api.triggerSEOAudit(orgId, websiteId, {
        crawl_job_id: selectedCrawlId || undefined,
        execute_sync: true,
      });

      setCurrentAudit(newAudit);
      setAudits((prev) => [newAudit, ...prev]);
      setSuccessMsg(`Technical SEO audit completed successfully! Health score: ${newAudit.score ?? "N/A"}/100.`);
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadAudits();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute SEO audit.");
    } finally {
      setIsRunningAudit(false);
    }
  };

  // 5. Differential Comparison
  const handleCompare = async (prevAuditId: string) => {
    if (!currentAudit || !orgId || !prevAuditId) return;
    setIsComparing(true);
    setCompareTargetId(prevAuditId);
    try {
      const comp = await api.compareSEOAudits(orgId, currentAudit.id, prevAuditId);
      setComparison(comp);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to compare audit snapshots.");
    } finally {
      setIsComparing(false);
    }
  };

  // Severity color mappings
  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/40 text-[10px]">Critical</Badge>;
      case "high":
        return <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/40 text-[10px]">High</Badge>;
      case "medium":
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/40 text-[10px]">Medium</Badge>;
      case "low":
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/40 text-[10px]">Low</Badge>;
      default:
        return <Badge className="bg-zinc-500/20 text-zinc-300 border-zinc-500/40 text-[10px]">Info</Badge>;
    }
  };

  // Health Score Color
  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "text-zinc-500";
    if (score >= 90) return "text-emerald-400";
    if (score >= 70) return "text-amber-400";
    if (score >= 50) return "text-orange-400";
    return "text-red-500";
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Execution Controls */}
      <Card className="border-rf-border bg-rf-surface/80">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base text-rf-text flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-rf-crimson" />
                  <span>Technical SEO Audit Engine</span>
                </CardTitle>
                <Badge variant="outline" className="font-mono text-[10px] text-rf-text-muted border-rf-border">
                  Ruleset v1.0.0
                </Badge>
              </div>
              <CardDescription className="text-xs text-rf-text-secondary">
                Deterministic rule analysis verifying crawl snapshots across 8 technical SEO categories.
              </CardDescription>
            </div>

            {/* Launch Controls */}
            <div className="flex items-center gap-2 flex-wrap">
              {availableCrawls.length > 0 && (
                <select
                  value={selectedCrawlId}
                  onChange={(e) => setSelectedCrawlId(e.target.value)}
                  className="bg-rf-bg border border-rf-border rounded text-xs px-2.5 py-1.5 text-rf-text focus:outline-none focus:border-rf-crimson"
                >
                  <option value="">Latest Completed Crawl Snapshot</option>
                  {availableCrawls
                    .filter((c) => c.pages_crawled > 0)
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        Crawl {formatDate(c.created_at)} ({c.pages_crawled} pages)
                      </option>
                    ))}
                </select>
              )}

              <Button
                onClick={handleTriggerAudit}
                disabled={!isVerified || isRunningAudit}
                className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5 disabled:opacity-50"
                title={!isVerified ? "Ownership verification required" : "Execute audit against crawl snapshot"}
              >
                <RotateCw className={`w-3.5 h-3.5 ${isRunningAudit ? "animate-spin" : ""}`} />
                <span>{isRunningAudit ? "Analyzing Rules..." : "Run Technical Audit"}</span>
              </Button>
            </div>
          </div>
        </CardHeader>

        {/* Notifications */}
        {error && (
          <div className="mx-6 mb-4 p-3 rounded bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-rf-text-muted hover:text-rf-text">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {successMsg && (
          <div className="mx-6 mb-4 p-3 rounded bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Current Audit Metrics Banner */}
        {currentAudit ? (
          <CardContent className="pt-0">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-lg bg-rf-bg border border-rf-border">
              {/* Health Score Gauge */}
              <div className="flex items-center gap-4">
                <div className="relative w-20 h-20 flex-shrink-0 flex items-center justify-center rounded-full border-4 border-rf-border bg-rf-surface/50">
                  <div className="text-center">
                    <span className={`text-2xl font-bold font-mono ${getScoreColor(currentAudit.score)}`}>
                      {currentAudit.score ?? "--"}
                    </span>
                    <span className="block text-[9px] text-rf-text-muted">/ 100</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-rf-text">Technical Health Score</div>
                  <div className="text-[11px] text-rf-text-secondary">
                    {currentAudit.score == null
                      ? "Insufficient coverage"
                      : currentAudit.score >= 90
                      ? "Optimal technical state"
                      : currentAudit.score >= 70
                      ? "Optimization advised"
                      : "Action required"}
                  </div>
                  <button
                    onClick={() => setShowHowScoreModal(true)}
                    className="inline-flex items-center gap-1 text-[10px] text-rf-crimson hover:underline pt-1"
                  >
                    <HelpCircle className="w-3 h-3" />
                    <span>How score is calculated</span>
                  </button>
                </div>
              </div>

              {/* Crawl Coverage */}
              <div className="space-y-1">
                <div className="text-[11px] font-medium text-rf-text-secondary">Crawl Snapshot Coverage</div>
                <div className="text-lg font-bold font-mono text-rf-text">
                  {Math.round(currentAudit.score_coverage * 100)}%
                </div>
                <div className="text-[11px] text-rf-text-muted">
                  {currentAudit.pages_evaluated} pages evaluated • {currentAudit.pages_not_evaluated} skipped
                </div>
              </div>

              {/* Total Findings Breakdown */}
              <div className="space-y-1">
                <div className="text-[11px] font-medium text-rf-text-secondary">Issues Detected</div>
                <div className="text-lg font-bold font-mono text-rf-text">{currentAudit.findings_count}</div>
                <div className="flex items-center gap-2 pt-0.5">
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                    {currentAudit.critical_count} Critical
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-orange-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                    {currentAudit.high_count} High
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                    {currentAudit.medium_count} Med
                  </span>
                </div>
              </div>

              {/* Audit Timestamp & Snapshot */}
              <div className="space-y-1">
                <div className="text-[11px] font-medium text-rf-text-secondary">Audit Execution</div>
                <div className="text-xs text-rf-text flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-rf-text-muted" />
                  <span>{formatDate(currentAudit.created_at)}</span>
                </div>
                <div className="text-[11px] text-rf-text-muted font-mono truncate">
                  ID: {currentAudit.id.slice(0, 13)}...
                </div>
              </div>
            </div>
          </CardContent>
        ) : (
          <CardContent className="py-8 text-center text-xs text-rf-text-muted">
            No technical SEO audits recorded yet. Run your first audit to analyze crawl findings.
          </CardContent>
        )}
      </Card>

      {/* 8 Category Score Cards */}
      {currentAudit && categoryScores.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-rf-text flex items-center justify-between">
            <span>Category Health Breakdown</span>
            <span className="text-[11px] font-normal text-rf-text-muted">
              Click any category card to filter issues below
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {categoryScores.map((cat) => {
              const catName = CATEGORY_NAMES[cat.category] || cat.category;
              const isSelected = categoryFilter === cat.category;
              return (
                <button
                  key={cat.id}
                  onClick={() => setCategoryFilter(isSelected ? "all" : cat.category)}
                  className={`text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? "bg-rf-surface border-rf-crimson ring-1 ring-rf-crimson"
                      : "bg-rf-surface/50 border-rf-border hover:border-rf-text-muted hover:bg-rf-surface"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-rf-text truncate">{catName}</span>
                    <span className="text-[10px] text-rf-text-muted font-mono">{(cat.weight * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-baseline justify-between pt-2">
                    <span className={`text-xl font-bold font-mono ${getScoreColor(cat.score)}`}>
                      {cat.score}
                    </span>
                    <span className="text-[10px] text-rf-text-secondary">
                      {cat.findings_count} {cat.findings_count === 1 ? "issue" : "issues"}
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full bg-rf-bg h-1.5 rounded-full overflow-hidden mt-2">
                    <div
                      className={`h-full ${
                        cat.score >= 90
                          ? "bg-emerald-500"
                          : cat.score >= 70
                          ? "bg-amber-500"
                          : cat.score >= 50
                          ? "bg-orange-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* View Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-rf-border pb-2">
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setActiveTab("issues")}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === "issues"
                ? "bg-rf-crimson text-white"
                : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
            }`}
          >
            Issue Explorer ({totalFindings})
          </button>
          <button
            onClick={() => setActiveTab("pages")}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === "pages"
                ? "bg-rf-crimson text-white"
                : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
            }`}
          >
            Audited Pages ({auditedPages.length})
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === "history"
                ? "bg-rf-crimson text-white"
                : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
            }`}
          >
            Audit History & Comparison ({audits.length})
          </button>
        </div>

        {categoryFilter !== "all" && (
          <button
            onClick={() => setCategoryFilter("all")}
            className="text-[11px] text-rf-crimson hover:underline"
          >
            Clear category filter ({CATEGORY_NAMES[categoryFilter] || categoryFilter})
          </button>
        )}
      </div>

      {/* TAB 1: ISSUE EXPLORER */}
      {activeTab === "issues" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-rf-text-muted" />
              <input
                type="text"
                placeholder="Search issues, rules, URLs..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setFindingsPage(1);
                }}
                className="w-full bg-rf-bg border border-rf-border rounded pl-8 pr-3 py-1.5 text-xs text-rf-text placeholder:text-rf-text-muted focus:outline-none focus:border-rf-crimson"
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setFindingsPage(1);
              }}
              className="bg-rf-bg border border-rf-border rounded px-3 py-1.5 text-xs text-rf-text focus:outline-none focus:border-rf-crimson"
            >
              <option value="all">All Categories</option>
              {Object.entries(CATEGORY_NAMES).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>

            <select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setFindingsPage(1);
              }}
              className="bg-rf-bg border border-rf-border rounded px-3 py-1.5 text-xs text-rf-text focus:outline-none focus:border-rf-crimson"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="informational">Informational</option>
            </select>
          </div>

          {/* Findings List */}
          {findings.length === 0 ? (
            <div className="p-8 text-center text-xs text-rf-text-muted rounded-lg border border-rf-border bg-rf-surface/30">
              No technical issues found matching current filters.
            </div>
          ) : (
            <div className="space-y-2">
              {findings.map((f) => {
                const isExpanded = expandedFindingId === f.id;
                return (
                  <div
                    key={f.id}
                    className="border border-rf-border rounded-lg bg-rf-surface/50 overflow-hidden transition-colors"
                  >
                    <div
                      onClick={() => setExpandedFindingId(isExpanded ? null : f.id)}
                      className="p-3.5 flex items-start justify-between gap-3 cursor-pointer hover:bg-rf-surface transition-colors"
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          {getSeverityBadge(f.severity)}
                          <span className="text-xs font-semibold text-rf-text">{f.title}</span>
                          <span className="text-[10px] text-rf-text-muted font-mono">[{f.rule_id}]</span>
                          <Badge variant="outline" className="text-[9px] text-rf-text-secondary border-rf-border">
                            {CATEGORY_NAMES[f.category] || f.category}
                          </Badge>
                        </div>
                        {f.page_url && (
                          <div className="text-[11px] font-mono text-rf-text-secondary truncate flex items-center gap-1">
                            <span className="text-rf-text-muted">URL:</span>
                            <span>{f.page_url}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-rf-text-muted flex-shrink-0">
                        <ChevronDown
                          className={`w-4 h-4 transition-transform duration-200 ${
                            isExpanded ? "transform rotate-180" : ""
                          }`}
                        />
                      </div>
                    </div>

                    {/* Accordion Content */}
                    {isExpanded && (
                      <div className="p-4 border-t border-rf-border bg-rf-bg/70 space-y-3 text-xs">
                        <div className="space-y-1">
                          <span className="font-semibold text-rf-text">Problem Description</span>
                          <p className="text-rf-text-secondary text-[11px] leading-relaxed">{f.description}</p>
                        </div>

                        <div className="space-y-1">
                          <span className="font-semibold text-emerald-400">Actionable Recommendation</span>
                          <p className="text-rf-text text-[11px] leading-relaxed">{f.recommendation}</p>
                        </div>

                        {/* Concrete Evidence Box */}
                        {f.evidence_json && Object.keys(f.evidence_json).length > 0 && (
                          <div className="space-y-1">
                            <span className="font-semibold text-rf-text-muted flex items-center gap-1 text-[11px]">
                              <Code2 className="w-3.5 h-3.5 text-rf-crimson" />
                              <span>Observed Evidence</span>
                            </span>
                            <pre className="p-2.5 rounded bg-rf-bg border border-rf-border text-[11px] font-mono text-rf-text-secondary overflow-x-auto">
                              {JSON.stringify(f.evidence_json, null, 2)}
                            </pre>
                          </div>
                        )}

                        <div className="pt-2 flex items-center justify-between border-t border-rf-border/50 text-[10px] text-rf-text-muted font-mono">
                          <span>Fingerprint: {f.finding_fingerprint.slice(0, 16)}...</span>
                          {f.page_url && (
                            <a
                              href={f.page_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-rf-crimson hover:underline flex items-center gap-1"
                            >
                              <span>Open URL in browser</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AUDITED PAGES INVENTORY */}
      {activeTab === "pages" && (
        <Card className="border-rf-border bg-rf-surface/80">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Audited Pages & Issue Density</CardTitle>
            <CardDescription className="text-xs">
              Every page evaluated in this crawl snapshot along with technical SEO attributes and finding counts.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-rf-bg border-y border-rf-border text-[11px] font-medium text-rf-text-muted">
                  <tr>
                    <th className="p-3">Page URL</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">H1 Count</th>
                    <th className="p-3">Images (Missing Alt)</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Issues</th>
                    <th className="p-3 text-right">Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rf-border/40 font-mono text-[11px]">
                  {auditedPages.map((p, idx) => (
                    <tr key={idx} className="hover:bg-rf-surface/50 transition-colors">
                      <td className="p-3 max-w-xs truncate text-rf-text font-sans font-medium">
                        {p.title || p.url}
                        <span className="block text-[10px] font-mono text-rf-text-muted truncate">{p.url}</span>
                      </td>
                      <td className="p-3">
                        <Badge
                          variant="outline"
                          className={p.status_code === 200 ? "text-emerald-400 border-emerald-500/40" : "text-red-400 border-red-500/40"}
                        >
                          {p.status_code}
                        </Badge>
                      </td>
                      <td className="p-3">{p.h1_count}</td>
                      <td className="p-3">
                        {p.images_count} ({p.images_missing_alt_count} missing)
                      </td>
                      <td className="p-3">{Math.round(p.response_time_ms)} ms</td>
                      <td className="p-3">
                        {p.findings_count > 0 ? (
                          <Badge className="bg-red-500/20 text-red-400 border-red-500/40 text-[10px]">
                            {p.findings_count}
                          </Badge>
                        ) : (
                          <span className="text-emerald-400 text-xs font-semibold">0</span>
                        )}
                      </td>
                      <td className="p-3 text-right font-sans">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setInspectingPage(p)}
                          className="text-[11px] h-6 px-2 text-rf-text-secondary hover:text-rf-text"
                        >
                          Inspect
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 3: AUDIT HISTORY & COMPARISON */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <Card className="border-rf-border bg-rf-surface/80">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Historical SEO Audits</CardTitle>
              <CardDescription className="text-xs">
                Select any prior audit snapshot to compare against the current audit and detect score changes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {audits.map((a) => {
                const isSelected = currentAudit?.id === a.id;
                return (
                  <div
                    key={a.id}
                    className={`p-3 rounded-lg border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${
                      isSelected ? "border-rf-crimson bg-rf-bg" : "border-rf-border bg-rf-surface/40 hover:bg-rf-surface"
                    }`}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-rf-text">{formatDate(a.created_at)}</span>
                        {isSelected && (
                          <Badge className="bg-rf-crimson/20 text-rf-crimson border-rf-crimson/40 text-[10px]">
                            Active
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-[10px] text-rf-text-muted border-rf-border">
                          {a.status}
                        </Badge>
                      </div>
                      <div className="text-[11px] text-rf-text-secondary font-mono">
                        Score: {a.score ?? "N/A"} • {a.findings_count} issues • {a.pages_evaluated} pages
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {!isSelected && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentAudit(a)}
                            className="text-xs h-7"
                          >
                            Load
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={isComparing}
                            onClick={() => handleCompare(a.id)}
                            className="text-xs h-7 border-rf-crimson/50 text-rf-crimson hover:bg-rf-crimson/10"
                          >
                            Compare with Active
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Differential Comparison Display */}
          {comparison && (
            <Card className="border-rf-crimson/40 bg-rf-bg">
              <CardHeader className="pb-3 border-b border-rf-border">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm text-rf-text flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-rf-crimson" />
                    <span>Differential Audit Analysis</span>
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setComparison(null)}
                    className="h-6 text-xs text-rf-text-muted hover:text-rf-text"
                  >
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded bg-rf-surface border border-rf-border">
                    <span className="text-[11px] text-rf-text-muted block">Score Delta</span>
                    <span
                      className={`text-xl font-bold font-mono ${
                        comparison.score_change > 0
                          ? "text-emerald-400"
                          : comparison.score_change < 0
                          ? "text-red-400"
                          : "text-zinc-400"
                      }`}
                    >
                      {comparison.score_change > 0 ? `+${comparison.score_change}` : comparison.score_change}
                    </span>
                  </div>

                  <div className="p-3 rounded bg-rf-surface border border-rf-border">
                    <span className="text-[11px] text-rf-text-muted block">New Issues</span>
                    <span className="text-xl font-bold font-mono text-red-400">
                      +{comparison.new_findings_count}
                    </span>
                  </div>

                  <div className="p-3 rounded bg-rf-surface border border-rf-border">
                    <span className="text-[11px] text-rf-text-muted block">Resolved Issues</span>
                    <span className="text-xl font-bold font-mono text-emerald-400">
                      -{comparison.resolved_findings_count}
                    </span>
                  </div>

                  <div className="p-3 rounded bg-rf-surface border border-rf-border">
                    <span className="text-[11px] text-rf-text-muted block">Persisting Issues</span>
                    <span className="text-xl font-bold font-mono text-amber-400">
                      {comparison.persisting_findings_count}
                    </span>
                  </div>
                </div>

                {/* Resolved Issues Highlights */}
                {comparison.resolved_findings_count > 0 && (
                  <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">
                    <div className="font-semibold flex items-center gap-1.5 pb-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>{comparison.resolved_findings_count} Issue(s) Successfully Resolved Since Prior Audit</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Page SEO Inspector Drawer / Modal */}
      {inspectingPage && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-rf-surface border border-rf-border rounded-lg max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <div>
                <h3 className="text-sm font-semibold text-rf-text">Page SEO Inspector</h3>
                <p className="text-xs font-mono text-rf-text-muted truncate max-w-md">{inspectingPage.url}</p>
              </div>
              <button
                onClick={() => setInspectingPage(null)}
                className="text-rf-text-muted hover:text-rf-text text-sm"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded bg-rf-bg border border-rf-border">
                <span className="text-rf-text-muted block text-[10px]">Title Tag</span>
                <span className="font-medium text-rf-text">{inspectingPage.title || "Missing"}</span>
              </div>
              <div className="p-2.5 rounded bg-rf-bg border border-rf-border">
                <span className="text-rf-text-muted block text-[10px]">Canonical URL</span>
                <span className="font-mono text-rf-text truncate block">{inspectingPage.canonical_url || "None"}</span>
              </div>
              <div className="p-2.5 rounded bg-rf-bg border border-rf-border">
                <span className="text-rf-text-muted block text-[10px]">HTTP Status</span>
                <span className="font-mono text-rf-text">{inspectingPage.status_code}</span>
              </div>
              <div className="p-2.5 rounded bg-rf-bg border border-rf-border">
                <span className="text-rf-text-muted block text-[10px]">Response Latency</span>
                <span className="font-mono text-rf-text">{Math.round(inspectingPage.response_time_ms)} ms</span>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-rf-text">Issues on this Page ({inspectingPage.findings_count})</span>
              {findings
                .filter((f) => f.page_url === inspectingPage.url)
                .map((f) => (
                  <div key={f.id} className="p-2.5 rounded bg-rf-bg border border-rf-border text-xs space-y-1">
                    <div className="flex items-center gap-2">
                      {getSeverityBadge(f.severity)}
                      <span className="font-semibold text-rf-text">{f.title}</span>
                    </div>
                    <p className="text-rf-text-secondary text-[11px]">{f.recommendation}</p>
                  </div>
                ))}
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setInspectingPage(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* "How Score Is Calculated" Modal */}
      {showHowScoreModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-rf-surface border border-rf-border rounded-lg max-w-xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto text-xs">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <h3 className="text-sm font-semibold text-rf-text">How the SEO Health Score is Calculated</h3>
              <button
                onClick={() => setShowHowScoreModal(false)}
                className="text-rf-text-muted hover:text-rf-text text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-rf-text-secondary leading-relaxed">
              RankForge AI calculates a transparent, deterministic technical SEO health score between 0 and 100 based on audited crawl findings.
            </p>

            <div className="space-y-2">
              <span className="font-semibold text-rf-text">1. Category Weights (Sum: 100%)</span>
              <ul className="list-disc pl-5 space-y-1 text-rf-text-secondary">
                <li><strong className="text-rf-text">Indexability (25%):</strong> Meta robots noindex, X-Robots-Tag, conflicting sitemap directives.</li>
                <li><strong className="text-rf-text">Links & HTTP (20%):</strong> Broken 4xx links, 5xx server errors, redirect hops, server latency.</li>
                <li><strong className="text-rf-text">Canonical URLs (15%):</strong> Broken canonicals, redirect canonicals, circular canonical loops, fragment anchors.</li>
                <li><strong className="text-rf-text">Metadata & Tags (15%):</strong> Missing/empty titles, duplicate titles, missing/empty meta descriptions.</li>
                <li><strong className="text-rf-text">Site Structure (10%):</strong> Crawl depth &gt; 3, orphan pages with 0 internal inlinks, empty anchor text.</li>
                <li><strong className="text-rf-text">Heading Hierarchy (5%):</strong> Missing H1 tags, empty H1s, heading hierarchy level skips.</li>
                <li><strong className="text-rf-text">Image Optimization (5%):</strong> Missing alt attributes (decorative alt=&quot;&quot; is permitted), generic alt text.</li>
                <li><strong className="text-rf-text">Schema & Sitemaps (5%):</strong> Malformed JSON-LD structured data, unreachable sitemap documents.</li>
              </ul>
            </div>

            <div className="space-y-2">
              <span className="font-semibold text-rf-text">2. Severity Base Deductions</span>
              <p className="text-rf-text-secondary">
                Critical (-20 pts), High (-10 pts), Medium (-5 pts), Low (-2 pts), Informational (0 pts).
              </p>
            </div>

            <div className="space-y-2">
              <span className="font-semibold text-rf-text">3. Template Repetition Damping</span>
              <p className="text-rf-text-secondary leading-relaxed">
                To prevent sitewide template flaws (such as a missing meta description across 100 pages) from single-handedly reducing category scores to zero, logarithmic damping is applied: <code className="font-mono bg-rf-bg px-1 py-0.5 rounded text-rf-crimson">penalty = base_penalty * (1 + 0.5 * log2(n))</code>.
              </p>
            </div>

            <div className="pt-2 flex justify-end">
              <Button size="sm" onClick={() => setShowHowScoreModal(false)} className="bg-rf-crimson text-white">
                Understood
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
