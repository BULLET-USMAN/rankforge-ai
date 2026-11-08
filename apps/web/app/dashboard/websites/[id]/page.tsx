"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Globe,
  ArrowLeft,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Clock,
  CheckCircle2,
  Copy,
  Check,
  Play,
  RotateCw,
  XCircle,
  AlertCircle,
  Download,
  Search,
  Filter,
  ExternalLink as LinkIcon,
  ChevronRight,
  Info,
  Archive,
  RotateCcw,
  Trash2,
  Edit2,
  FileText,
  Layers,
  StopCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  api,
  type WebsiteProject,
  type Organization,
  type VerificationStatus,
  type CrawlJob,
  type CrawledPage,
  type CrawledPageDetail,
} from "@/lib/api-client";

export default function WebsiteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const websiteId = params?.id as string;

  // Website & Workspace state
  const [project, setProject] = useState<WebsiteProject | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Verification state
  const [verifMethod, setVerifMethod] = useState<"dns_txt" | "file_upload">("dns_txt");
  const [verifData, setVerifData] = useState<VerificationStatus | null>(null);
  const [isCheckingVerif, setIsCheckingVerif] = useState(false);
  const [verifCheckMsg, setVerifCheckMsg] = useState<{ isSuccess: boolean; text: string } | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Crawler state
  const [crawls, setCrawls] = useState<CrawlJob[]>([]);
  const [activeCrawl, setActiveCrawl] = useState<CrawlJob | null>(null);
  const [selectedCrawlId, setSelectedCrawlId] = useState<string | null>(null);
  const [isStartingCrawl, setIsStartingCrawl] = useState(false);
  const [maxPages, setMaxPages] = useState<number>(50);
  const [maxDepth, setMaxDepth] = useState<number>(3);
  const [crawlConfigOpen, setCrawlConfigOpen] = useState(false);

  // Crawled pages inventory
  const [pages, setPages] = useState<CrawledPage[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [pageSearch, setPageSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [pageNumber, setPageNumber] = useState(1);
  const [selectedPageDetail, setSelectedPageDetail] = useState<CrawledPageDetail | null>(null);
  const [isLoadingPages, setIsLoadingPages] = useState(false);

  // Edit metadata modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // 1. Initial Load: Locate Organization and Project
  useEffect(() => {
    if (!websiteId) return;

    api
      .listOrganizations()
      .then(async (orgs) => {
        if (!orgs || orgs.length === 0) {
          setIsLoading(false);
          return;
        }
        setOrganizations(orgs);

        for (const org of orgs) {
          try {
            const p = await api.getWebsite(org.id, websiteId);
            if (p) {
              setProject(p);
              setCurrentOrgId(org.id);
              setEditName(p.name);
              setEditDescription(p.description || "");

              // Load verification challenge details
              const v = await api.getVerificationStatus(org.id, p.id, verifMethod).catch(() => null);
              setVerifData(v);

              // Load crawls history
              const crawlsRes = await api.listCrawls(org.id, p.id).catch(() => null);
              if (crawlsRes && crawlsRes.items) {
                setCrawls(crawlsRes.items);
                const running = crawlsRes.items.find((c) => c.status === "running" || c.status === "queued");
                if (running) {
                  setActiveCrawl(running);
                  setSelectedCrawlId(running.id);
                } else if (crawlsRes.items.length > 0) {
                  setSelectedCrawlId(crawlsRes.items[0].id);
                }
              }

              setIsLoading(false);
              return;
            }
          } catch {
            // Check next org
          }
        }
        setError("Website project not found in any accessible workspace.");
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load project details");
        setIsLoading(false);
      });
  }, [websiteId]);

  // 2. Fetch Verification Challenge when method toggles
  const handleMethodChange = async (method: "dns_txt" | "file_upload") => {
    setVerifMethod(method);
    setVerifCheckMsg(null);
    if (project && currentOrgId) {
      try {
        const v = await api.getVerificationStatus(currentOrgId, project.id, method);
        setVerifData(v);
      } catch (err: unknown) {
        console.error("Failed to fetch verification status", err);
      }
    }
  };

  // 3. Trigger Verification Check
  const handleCheckVerification = async () => {
    if (!project || !currentOrgId) return;
    setIsCheckingVerif(true);
    setVerifCheckMsg(null);
    setError(null);

    try {
      const result = await api.checkVerification(currentOrgId, project.id, verifMethod);
      if (result.is_verified) {
        setVerifCheckMsg({
          isSuccess: true,
          text: result.message || "Domain ownership verified successfully!",
        });
        setProject((prev) => (prev ? { ...prev, is_verified: true, verification_status: "verified" } : prev));
        const updatedV = await api.getVerificationStatus(currentOrgId, project.id, verifMethod);
        setVerifData(updatedV);
      } else {
        setVerifCheckMsg({
          isSuccess: false,
          text: result.failure_reason || result.message || "Verification check failed. Please ensure records are published.",
        });
        const updatedV = await api.getVerificationStatus(currentOrgId, project.id, verifMethod);
        setVerifData(updatedV);
      }
    } catch (err: unknown) {
      setVerifCheckMsg({
        isSuccess: false,
        text: err instanceof Error ? err.message : "Verification check failed.",
      });
    } finally {
      setIsCheckingVerif(false);
    }
  };

  // 4. Revoke Verification
  const handleRevokeVerification = async () => {
    if (!project || !currentOrgId) return;
    if (!confirm("Are you sure you want to revoke verification for this domain? Active crawlers will be restricted.")) return;

    try {
      await api.revokeVerification(currentOrgId, project.id);
      setProject((prev) => (prev ? { ...prev, is_verified: false, verification_status: "revoked" } : prev));
      const updatedV = await api.getVerificationStatus(currentOrgId, project.id, verifMethod);
      setVerifData(updatedV);
      setActionSuccess("Domain verification revoked.");
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to revoke verification.");
    }
  };

  // 5. Start Crawl Job
  const handleStartCrawl = async () => {
    if (!project || !currentOrgId) return;
    setIsStartingCrawl(true);
    setError(null);
    setCrawlConfigOpen(false);

    try {
      const newJob = await api.startCrawl(currentOrgId, project.id, {
        max_pages: maxPages,
        max_depth: maxDepth,
      });
      setActiveCrawl(newJob);
      setSelectedCrawlId(newJob.id);
      setCrawls((prev) => [newJob, ...prev]);
      setActionSuccess(`Crawl job started (Max ${maxPages} pages, Depth ${maxDepth}).`);
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start crawl job.");
    } finally {
      setIsStartingCrawl(false);
    }
  };

  // 6. Cancel Crawl Job
  const handleCancelCrawl = async (jobId: string) => {
    if (!currentOrgId) return;
    try {
      const cancelled = await api.cancelCrawlJob(currentOrgId, jobId);
      setActiveCrawl(null);
      setCrawls((prev) => prev.map((c) => (c.id === jobId ? cancelled : c)));
      setActionSuccess("Crawl job cancelled.");
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel crawl job.");
    }
  };

  // 7. Poll Active Crawl Progress
  useEffect(() => {
    if (!activeCrawl || !currentOrgId) return;
    if (activeCrawl.status === "completed" || activeCrawl.status === "failed" || activeCrawl.status === "cancelled") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await api.getCrawlJob(currentOrgId, activeCrawl.id);
        setActiveCrawl(updated);
        setCrawls((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));

        if (updated.status === "completed" || updated.status === "failed" || updated.status === "cancelled") {
          clearInterval(interval);
          setActiveCrawl(null);
          // Reload pages for selected crawl
          if (selectedCrawlId === updated.id) {
            loadPages(selectedCrawlId);
          }
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [activeCrawl, currentOrgId, selectedCrawlId]);

  // 8. Load Pages for Selected Crawl
  const loadPages = useCallback(
    async (jobId: string) => {
      if (!currentOrgId || !jobId) return;
      setIsLoadingPages(true);
      try {
        const filterParam = statusFilter === "all" ? undefined : statusFilter;
        const res = await api.listCrawledPages(currentOrgId, jobId, {
          search: pageSearch || undefined,
          status_filter: filterParam,
          page: pageNumber,
          page_size: 50,
        });
        setPages(res.items || []);
        setTotalPages(res.total || 0);
      } catch (err) {
        console.error("Failed to load pages", err);
      } finally {
        setIsLoadingPages(false);
      }
    },
    [currentOrgId, pageSearch, statusFilter, pageNumber]
  );

  useEffect(() => {
    if (selectedCrawlId) {
      loadPages(selectedCrawlId);
    }
  }, [selectedCrawlId, loadPages]);

  // 9. Inspect Single Page Detail
  const handleInspectPage = async (pageId: string) => {
    if (!currentOrgId || !selectedCrawlId) return;
    try {
      const detail = await api.getCrawledPageDetail(currentOrgId, selectedCrawlId, pageId);
      setSelectedPageDetail(detail);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load page details.");
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleDownloadVerificationFile = () => {
    if (!verifData?.file_content) return;
    const blob = new Blob([verifData.file_content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "rankforge-verification.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSaveMetadata = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrgId || !project) return;
    setIsSaving(true);
    try {
      const updated = await api.updateWebsite(currentOrgId, project.id, {
        name: editName.trim(),
        description: editDescription.trim(),
      });
      setProject(updated);
      setShowEditModal(false);
      setActionSuccess("Project metadata updated.");
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update project metadata");
    } finally {
      setIsSaving(false);
    }
  };

  const handleArchiveToggle = async () => {
    if (!currentOrgId || !project) return;
    try {
      if (project.archived_at) {
        const restored = await api.restoreWebsite(currentOrgId, project.id);
        setProject(restored);
      } else {
        const archived = await api.archiveWebsite(currentOrgId, project.id);
        setProject(archived);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to toggle archive status");
    }
  };

  const handleDelete = async () => {
    if (!currentOrgId || !project) return;
    if (!confirm("Are you sure you want to permanently delete this website project? This cannot be undone.")) return;
    try {
      await api.deleteWebsite(currentOrgId, project.id);
      router.push("/dashboard/websites");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete website project");
    }
  };

  if (isLoading) {
    return <div className="py-12 text-center text-xs text-rf-text-muted">Loading website project...</div>;
  }

  if (!project) {
    return (
      <div className="space-y-4 max-w-xl mx-auto py-12 text-center">
        <h2 className="text-base font-semibold text-rf-text">Website Project Not Found</h2>
        <p className="text-xs text-rf-text-secondary">
          The requested website project could not be found or you do not have permission to view it.
        </p>
        <Link
          href="/dashboard/websites"
          className="inline-flex items-center gap-1.5 text-xs text-rf-crimson hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Websites</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl pb-16">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/dashboard/websites"
          className="inline-flex items-center gap-1.5 text-xs text-rf-text-secondary hover:text-rf-text transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to All Websites</span>
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowEditModal(true)}
            className="text-xs h-8 flex items-center gap-1.5"
          >
            <Edit2 className="w-3 h-3" />
            <span>Edit Details</span>
          </Button>

          <Button
            variant="outline"
            onClick={handleArchiveToggle}
            className="text-xs h-8 flex items-center gap-1.5"
          >
            {project.archived_at ? (
              <>
                <RotateCcw className="w-3 h-3" />
                <span>Restore Project</span>
              </>
            ) : (
              <>
                <Archive className="w-3 h-3" />
                <span>Archive</span>
              </>
            )}
          </Button>

          <button
            onClick={handleDelete}
            className="p-1.5 rounded border border-rf-border bg-rf-surface hover:bg-rf-crimson/10 hover:border-rf-crimson/30 text-rf-text-muted hover:text-red-300 transition-colors"
            title="Permanently delete project"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rf-crimson flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rf-text-muted hover:text-rf-text text-xs">
            Dismiss
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Website Overview Card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg">{project.name}</CardTitle>
                <Badge
                  variant="outline"
                  className={`font-mono text-[10px] ${
                    project.is_verified
                      ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
                      : "border-amber-500/40 text-amber-400 bg-amber-500/10"
                  }`}
                >
                  {project.is_verified ? "Domain Verified" : "Verification Pending"}
                </Badge>
                {project.archived_at && (
                  <Badge variant="outline" className="font-mono text-[10px] border-rf-border text-rf-text-muted">
                    Archived
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-rf-text-secondary">
                <Globe className="w-3.5 h-3.5 text-rf-crimson" />
                <span>{project.domain}</span>
                <span className="text-rf-border">•</span>
                <a
                  href={project.primary_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-rf-text-muted hover:text-rf-text flex items-center gap-1"
                >
                  <span>{project.primary_url}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => setCrawlConfigOpen(!crawlConfigOpen)}
                disabled={!project.is_verified || isStartingCrawl || activeCrawl !== null}
                className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5 disabled:opacity-50"
                title={!project.is_verified ? "Verify domain ownership first" : "Configure and launch crawler"}
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isStartingCrawl ? "Starting..." : "Start Website Crawl"}</span>
              </Button>
            </div>
          </div>
          {project.description && (
            <CardDescription className="text-xs pt-2">{project.description}</CardDescription>
          )}
        </CardHeader>

        {/* Crawl Config Drawer */}
        {crawlConfigOpen && project.is_verified && (
          <div className="p-4 border-t border-rf-border bg-rf-surface/50 rounded-b-lg space-y-4">
            <div className="text-xs font-semibold text-rf-text flex items-center justify-between">
              <span>Crawl Job Parameters</span>
              <span className="text-[11px] font-normal text-rf-text-secondary font-mono">
                Pacing: 1 req/sec • User-Agent: RankForgeBot/1.0
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-rf-text-secondary" htmlFor="maxPages">
                  Maximum Pages Budget (1–100)
                </label>
                <input
                  id="maxPages"
                  type="number"
                  min={1}
                  max={100}
                  value={maxPages}
                  onChange={(e) => setMaxPages(Math.max(1, Math.min(100, parseInt(e.target.value) || 10)))}
                  className="w-full h-8 px-2.5 rounded border border-rf-border bg-rf-bg text-rf-text text-xs font-mono"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-rf-text-secondary" htmlFor="maxDepth">
                  Maximum Crawl Depth (1–5)
                </label>
                <input
                  id="maxDepth"
                  type="number"
                  min={1}
                  max={5}
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(Math.max(1, Math.min(5, parseInt(e.target.value) || 1)))}
                  className="w-full h-8 px-2.5 rounded border border-rf-border bg-rf-bg text-rf-text text-xs font-mono"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 pt-1">
              <Button
                variant="outline"
                onClick={() => setCrawlConfigOpen(false)}
                className="text-xs h-7"
              >
                Cancel
              </Button>
              <Button
                onClick={handleStartCrawl}
                disabled={isStartingCrawl}
                className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-7"
              >
                Launch Crawl Now
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Domain Ownership Verification Section */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                {project.is_verified ? (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                )}
                <span>Domain Ownership Verification</span>
              </CardTitle>
              <CardDescription>
                Live verification is required before crawler execution and authorized SEO modifications.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {project.is_verified ? (
                <Button
                  variant="outline"
                  onClick={handleRevokeVerification}
                  className="text-xs h-7 text-rf-text-muted hover:text-red-400 border-rf-border"
                >
                  Revoke Verification
                </Button>
              ) : (
                <Button
                  onClick={handleCheckVerification}
                  disabled={isCheckingVerif}
                  className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5"
                >
                  <RotateCw className={`w-3.5 h-3.5 ${isCheckingVerif ? "animate-spin" : ""}`} />
                  <span>{isCheckingVerif ? "Verifying Records..." : "Check Verification Now"}</span>
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Verification Result Feedback Banner */}
          {verifCheckMsg && (
            <div
              className={`p-3 rounded-md text-xs border flex items-start gap-2.5 ${
                verifCheckMsg.isSuccess
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-amber-500/10 border-amber-500/30 text-amber-300"
              }`}
            >
              {verifCheckMsg.isSuccess ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <span className="font-semibold">{verifCheckMsg.isSuccess ? "Verification Successful" : "Verification Incomplete"}</span>
                <p className="text-[11px] leading-relaxed">{verifCheckMsg.text}</p>
              </div>
            </div>
          )}

          {/* Verification Method Tabs */}
          <div className="flex items-center gap-2 border-b border-rf-border pb-2 text-xs">
            <button
              onClick={() => handleMethodChange("dns_txt")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                verifMethod === "dns_txt"
                  ? "bg-rf-crimson text-white"
                  : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
              }`}
            >
              DNS TXT Record (Recommended)
            </button>
            <button
              onClick={() => handleMethodChange("file_upload")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                verifMethod === "file_upload"
                  ? "bg-rf-crimson text-white"
                  : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
              }`}
            >
              HTML Verification File
            </button>
          </div>

          {/* DNS TXT Instructions */}
          {verifMethod === "dns_txt" && (
            <div className="space-y-3 text-xs">
              <p className="text-rf-text-secondary">
                Publish a DNS TXT record with your domain registrar or DNS hosting provider for{" "}
                <span className="font-mono text-rf-text font-medium">{project.domain}</span>:
              </p>
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface font-mono text-[11px] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">Record Type:</span>
                  <span className="text-rf-text font-bold">TXT</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-rf-text-muted flex-shrink-0">Host / Name:</span>
                  <span className="truncate text-rf-text">{verifData?.txt_record_name || `_rankforge-challenge.${project.domain}`}</span>
                  <button
                    onClick={() => copyToClipboard(verifData?.txt_record_name || `_rankforge-challenge.${project.domain}`, "txt_host")}
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy Host"
                  >
                    {copiedKey === "txt_host" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-rf-border/40">
                  <span className="text-rf-text-muted flex-shrink-0">Value:</span>
                  <span className="truncate text-rf-crimson font-medium">
                    {verifData?.txt_record_value || `rankforge-verification=${project.verification_token}`}
                  </span>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        verifData?.txt_record_value || `rankforge-verification=${project.verification_token}`,
                        "txt_val"
                      )
                    }
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy Value"
                  >
                    {copiedKey === "txt_val" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
              <div className="text-[11px] text-rf-text-muted flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                <span>DNS record propagation may take from 1 to 15 minutes depending on your TTL settings.</span>
              </div>
            </div>
          )}

          {/* HTML File Instructions */}
          {verifMethod === "file_upload" && (
            <div className="space-y-3 text-xs">
              <p className="text-rf-text-secondary">
                Upload the verification file to the following path on your web server:
              </p>
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface font-mono text-[11px] space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-rf-text-muted flex-shrink-0">Required URL:</span>
                  <span className="truncate text-rf-text">
                    https://{project.domain}/.well-known/rankforge-verification.txt
                  </span>
                  <button
                    onClick={() =>
                      copyToClipboard(`https://${project.domain}/.well-known/rankforge-verification.txt`, "file_url")
                    }
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy URL"
                  >
                    {copiedKey === "file_url" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-rf-border/40">
                  <span className="text-rf-text-muted flex-shrink-0">File Content:</span>
                  <span className="truncate text-rf-crimson font-medium">
                    {verifData?.file_content || `rankforge-verification=${project.verification_token}`}
                  </span>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        verifData?.file_content || `rankforge-verification=${project.verification_token}`,
                        "file_val"
                      )
                    }
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy Content"
                  >
                    {copiedKey === "file_val" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between pt-1">
                <div className="text-[11px] text-rf-text-muted flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5" />
                  <span>The file must return an HTTP 200 status code with exact text content.</span>
                </div>
                <Button
                  variant="outline"
                  onClick={handleDownloadVerificationFile}
                  className="text-xs h-7 flex items-center gap-1.5"
                >
                  <Download className="w-3 h-3" />
                  <span>Download .txt File</span>
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Live Active Crawl Monitor Card */}
      {activeCrawl && (
        <Card className="border-rf-crimson/50 bg-rf-surface/40">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <CardTitle className="text-sm flex items-center gap-2">
                  <RotateCw className="w-4 h-4 text-rf-crimson animate-spin" />
                  <span>Website Crawler Running</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Active crawl in progress for {project.domain}. Live metrics refresh automatically.
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => handleCancelCrawl(activeCrawl.id)}
                className="text-xs h-7 text-red-400 hover:text-red-300 border-red-500/30 hover:bg-red-500/10 flex items-center gap-1.5"
              >
                <StopCircle className="w-3.5 h-3.5" />
                <span>Cancel Crawl</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Progress bar */}
            <div className="w-full bg-rf-bg h-2 rounded-full overflow-hidden border border-rf-border">
              <div
                className="bg-rf-crimson h-full transition-all duration-500"
                style={{
                  width: `${Math.min(100, Math.round((activeCrawl.pages_crawled / Math.max(1, activeCrawl.max_pages)) * 100))}%`,
                }}
              />
            </div>
            {/* Metrics tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2 rounded bg-rf-surface border border-rf-border">
                <span className="text-rf-text-muted text-[10px] uppercase font-mono block">Crawled</span>
                <span className="text-base font-bold font-mono text-rf-text">
                  {activeCrawl.pages_crawled} / {activeCrawl.max_pages}
                </span>
              </div>
              <div className="p-2 rounded bg-rf-surface border border-rf-border">
                <span className="text-rf-text-muted text-[10px] uppercase font-mono block">Discovered</span>
                <span className="text-base font-bold font-mono text-rf-text">{activeCrawl.pages_discovered}</span>
              </div>
              <div className="p-2 rounded bg-rf-surface border border-rf-border">
                <span className="text-rf-text-muted text-[10px] uppercase font-mono block">Robots Blocked</span>
                <span className="text-base font-bold font-mono text-amber-400">{activeCrawl.pages_blocked}</span>
              </div>
              <div className="p-2 rounded bg-rf-surface border border-rf-border">
                <span className="text-rf-text-muted text-[10px] uppercase font-mono block">Failed</span>
                <span className="text-base font-bold font-mono text-red-400">{activeCrawl.pages_failed}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Crawl History & Inventory Explorer */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle className="text-base">Website Crawl History & Discovered Pages</CardTitle>
              <CardDescription className="text-xs">
                Inspect structured technical SEO attributes discovered during crawls
              </CardDescription>
            </div>
            {crawls.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-rf-text-muted font-mono">Job:</span>
                <select
                  value={selectedCrawlId || ""}
                  onChange={(e) => setSelectedCrawlId(e.target.value)}
                  className="h-8 px-2.5 rounded border border-rf-border bg-rf-surface text-xs text-rf-text font-mono focus:border-rf-crimson focus:outline-none"
                >
                  {crawls.map((c) => (
                    <option key={c.id} value={c.id}>
                      {new Date(c.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} — {c.status.toUpperCase()} ({c.pages_crawled} pages)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {crawls.length === 0 ? (
            <div className="py-8 text-center text-xs text-rf-text-muted">
              No crawl jobs executed yet. Ensure domain ownership is verified, then click "Start Website Crawl".
            </div>
          ) : (
            <>
              {/* Search and Status Filters */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                <div className="relative flex-1 max-w-sm">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-rf-text-muted" />
                  <input
                    type="text"
                    placeholder="Search URL or title..."
                    value={pageSearch}
                    onChange={(e) => setPageSearch(e.target.value)}
                    className="w-full h-8 pl-8 pr-3 rounded border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
                  {[
                    { id: "all", label: "All Pages" },
                    { id: "200", label: "200 OK" },
                    { id: "4xx", label: "4xx Client Errors" },
                    { id: "5xx", label: "5xx Server Errors" },
                    { id: "blocked", label: "Robots Blocked" },
                  ].map((flt) => (
                    <button
                      key={flt.id}
                      onClick={() => setStatusFilter(flt.id)}
                      className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                        statusFilter === flt.id
                          ? "bg-rf-crimson text-white"
                          : "border border-rf-border bg-rf-surface text-rf-text-secondary hover:text-rf-text"
                      }`}
                    >
                      {flt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Pages Table */}
              <div className="rounded border border-rf-border overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-rf-surface/80 text-rf-text-secondary font-mono text-[11px] border-b border-rf-border">
                      <tr>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Page URL & Title</th>
                        <th className="py-2.5 px-3">Latency</th>
                        <th className="py-2.5 px-3">Depth</th>
                        <th className="py-2.5 px-3">Links</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rf-border/40 font-mono text-[11px]">
                      {isLoadingPages ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-rf-text-muted">
                            Loading crawled pages...
                          </td>
                        </tr>
                      ) : pages.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-rf-text-muted">
                            No pages found matching filter.
                          </td>
                        </tr>
                      ) : (
                        pages.map((p) => {
                          const isSuccess = p.status_code >= 200 && p.status_code < 300;
                          const isBlocked = p.error_details && p.error_details.includes("robots.txt");
                          const isError = !isSuccess && !isBlocked;

                          return (
                            <tr key={p.id} className="hover:bg-rf-surface/40 transition-colors">
                              <td className="py-2.5 px-3 whitespace-nowrap">
                                <Badge
                                  variant="outline"
                                  className={`text-[10px] ${
                                    isSuccess
                                      ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
                                      : isBlocked
                                      ? "border-amber-500/40 text-amber-400 bg-amber-500/10"
                                      : "border-red-500/40 text-red-400 bg-red-500/10"
                                  }`}
                                >
                                  {p.status_code || (isBlocked ? "BLOCKED" : "ERR")}
                                </Badge>
                              </td>
                              <td className="py-2.5 px-3 max-w-md">
                                <div className="space-y-0.5">
                                  <div className="font-sans font-medium text-rf-text truncate">
                                    {p.title || <span className="text-rf-text-muted italic">No title</span>}
                                  </div>
                                  <div className="text-rf-text-secondary truncate flex items-center gap-1">
                                    <span className="truncate">{p.url}</span>
                                    <a
                                      href={p.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-rf-text-muted hover:text-rf-text"
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  </div>
                                </div>
                              </td>
                              <td className="py-2.5 px-3 whitespace-nowrap text-rf-text-secondary">
                                {p.response_time_ms ? `${p.response_time_ms.toFixed(0)} ms` : "—"}
                              </td>
                              <td className="py-2.5 px-3 whitespace-nowrap text-rf-text-secondary">
                                {p.depth}
                              </td>
                              <td className="py-2.5 px-3 whitespace-nowrap text-rf-text-secondary">
                                <span title="Internal links">{p.internal_links_count} int</span> •{" "}
                                <span title="External links">{p.external_links_count} ext</span>
                              </td>
                              <td className="py-2.5 px-3 text-right whitespace-nowrap">
                                <button
                                  onClick={() => handleInspectPage(p.id)}
                                  className="text-rf-crimson hover:text-rf-crimson-hover font-sans text-xs hover:underline"
                                >
                                  Inspect
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Footer Count */}
                <div className="p-2.5 bg-rf-surface/50 border-t border-rf-border text-xs text-rf-text-muted flex items-center justify-between font-mono text-[11px]">
                  <span>Total Pages: {totalPages}</span>
                  <span>Max Budget: 50–100 URLs</span>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Page Inspection Drawer / Modal */}
      {selectedPageDetail && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-rf-bg-secondary border border-rf-border rounded-lg shadow-2xl p-5 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <div className="space-y-0.5">
                <h3 className="font-semibold text-sm text-rf-text">Page Technical SEO Metadata</h3>
                <p className="text-xs text-rf-text-secondary font-mono truncate max-w-lg">
                  {selectedPageDetail.url}
                </p>
              </div>
              <button
                onClick={() => setSelectedPageDetail(null)}
                className="text-rf-text-muted hover:text-rf-text text-sm p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              {/* Meta Attributes Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 rounded bg-rf-surface border border-rf-border font-mono text-[11px]">
                <div>
                  <span className="text-rf-text-muted block">Status Code:</span>
                  <span className="text-rf-text font-bold">{selectedPageDetail.status_code}</span>
                </div>
                <div>
                  <span className="text-rf-text-muted block">Response Time:</span>
                  <span className="text-rf-text font-bold">{selectedPageDetail.response_time_ms} ms</span>
                </div>
                <div>
                  <span className="text-rf-text-muted block">Crawl Depth:</span>
                  <span className="text-rf-text font-bold">{selectedPageDetail.depth}</span>
                </div>
                <div>
                  <span className="text-rf-text-muted block">Discovery Method:</span>
                  <span className="text-rf-text font-bold capitalize">{selectedPageDetail.discovery_method}</span>
                </div>
                <div>
                  <span className="text-rf-text-muted block">Content Type:</span>
                  <span className="text-rf-text truncate block">{selectedPageDetail.content_type || "text/html"}</span>
                </div>
                <div>
                  <span className="text-rf-text-muted block">Byte Size:</span>
                  <span className="text-rf-text font-bold">{(selectedPageDetail.byte_size / 1024).toFixed(1)} KB</span>
                </div>
              </div>

              {/* Title & Description */}
              <div className="space-y-1.5 p-3 rounded bg-rf-surface/50 border border-rf-border">
                <span className="text-rf-text-muted text-[11px] font-mono block">Document Title:</span>
                <p className="text-rf-text font-medium">{selectedPageDetail.title || "None"}</p>
              </div>

              <div className="space-y-1.5 p-3 rounded bg-rf-surface/50 border border-rf-border">
                <span className="text-rf-text-muted text-[11px] font-mono block">Meta Description:</span>
                <p className="text-rf-text text-[11px] leading-relaxed">
                  {selectedPageDetail.meta_description || "None specified in HTML"}
                </p>
              </div>

              {/* Canonical & Robots */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div className="p-3 rounded bg-rf-surface/50 border border-rf-border space-y-1">
                  <span className="text-rf-text-muted text-[11px] font-mono block">Canonical URL:</span>
                  <p className="text-rf-text font-mono text-[10px] truncate">
                    {selectedPageDetail.canonical_url || "Self / None"}
                  </p>
                </div>
                <div className="p-3 rounded bg-rf-surface/50 border border-rf-border space-y-1">
                  <span className="text-rf-text-muted text-[11px] font-mono block">Meta Robots:</span>
                  <p className="text-rf-text font-mono text-[10px]">
                    {selectedPageDetail.meta_robots || "index, follow (default)"}
                  </p>
                </div>
              </div>

              {/* Heading Metrics */}
              <div className="p-3 rounded bg-rf-surface/50 border border-rf-border flex items-center justify-between font-mono text-[11px]">
                <span className="text-rf-text-muted">H1 Heading Elements Count:</span>
                <span className="text-rf-text font-bold">{selectedPageDetail.h1_count}</span>
              </div>

              {/* SHA-256 Fingerprint */}
              {selectedPageDetail.content_hash && (
                <div className="p-2.5 rounded bg-rf-surface border border-rf-border font-mono text-[10px] truncate text-rf-text-muted">
                  <span>SHA-256: </span>
                  <span className="text-rf-text">{selectedPageDetail.content_hash}</span>
                </div>
              )}

              {/* Discovered Outbound Links */}
              {selectedPageDetail.links_json && selectedPageDetail.links_json.length > 0 && (
                <div className="space-y-2 pt-2">
                  <div className="font-semibold text-rf-text flex items-center justify-between">
                    <span>Discovered Outbound Links ({selectedPageDetail.links_json.length})</span>
                    <span className="text-[11px] font-mono text-rf-text-muted">
                      {selectedPageDetail.internal_links_count} Internal • {selectedPageDetail.external_links_count} External
                    </span>
                  </div>
                  <div className="max-h-48 overflow-y-auto rounded border border-rf-border divide-y divide-rf-border/40 font-mono text-[10px]">
                    {selectedPageDetail.links_json.map((lnk, idx) => (
                      <div key={idx} className="p-2 flex items-center justify-between gap-2 hover:bg-rf-surface">
                        <span className="truncate text-rf-text flex-1">{lnk.url}</span>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          <Badge
                            variant="outline"
                            className={`text-[9px] uppercase ${
                              lnk.type === "internal" ? "border-rf-border text-rf-text-secondary" : "border-blue-500/40 text-blue-400"
                            }`}
                          >
                            {lnk.type}
                          </Badge>
                          {lnk.rel && (
                            <Badge variant="outline" className="text-[9px] text-rf-text-muted">
                              {lnk.rel}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                variant="outline"
                onClick={() => setSelectedPageDetail(null)}
                className="text-xs h-8"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Details Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-rf-bg-secondary border border-rf-border rounded-lg shadow-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <h3 className="font-semibold text-sm text-rf-text">Edit Website Project</h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-rf-text-muted hover:text-rf-text"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveMetadata} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="editName">
                  Website Display Name
                </label>
                <input
                  id="editName"
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="editDesc">
                  Description
                </label>
                <textarea
                  id="editDesc"
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={2}
                  className="w-full p-2.5 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowEditModal(false)}
                  className="text-xs h-8"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSaving}
                  className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8"
                >
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
