"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  RotateCw,
  Search,
  Filter,
  ExternalLink,
  ChevronRight,
  Copy,
  Check,
  Edit3,
  ThumbsUp,
  ThumbsDown,
  Layers,
  FileText,
  Link2,
  Image as ImageIcon,
  Heading,
  Zap,
  Info,
  X,
  History,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  api,
  type AIRecommendation,
  type AIRecommendationVersion,
  type AIGenerationJob,
  type AIUsageSummary,
  type AIQuotaDetails,
  type RecommendationType,
  type RecommendationStatus,
  type RecommendationPriority,
  type WebsiteProject,
} from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

interface AIOptimizationDashboardProps {
  orgId: string;
  websiteId: string;
  domain: string;
  websites?: WebsiteProject[];
  onSelectWebsite?: (websiteId: string) => void;
}

const TYPE_CONFIG: Record<
  RecommendationType,
  { label: string; icon: React.ElementType; color: string; bg: string }
> = {
  title_optimization: {
    label: "Title Tag",
    icon: Heading,
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
  },
  meta_description: {
    label: "Meta Description",
    icon: FileText,
    color: "text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/20",
  },
  heading_structure: {
    label: "Heading Hierarchy",
    icon: Layers,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
  content_structure: {
    label: "Content Advisory",
    icon: Edit3,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/20",
  },
  internal_linking: {
    label: "Internal Linking",
    icon: Link2,
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
  image_alt_guidance: {
    label: "Image Accessibility",
    icon: ImageIcon,
    color: "text-rose-400",
    bg: "bg-rose-500/10 border-rose-500/20",
  },
};

export function AIOptimizationDashboard({
  orgId,
  websiteId,
  domain,
  websites = [],
  onSelectWebsite,
}: AIOptimizationDashboardProps) {
  // State
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [usageSummary, setUsageSummary] = useState<AIUsageSummary | null>(null);
  const [quotaDetails, setQuotaDetails] = useState<AIQuotaDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Selected for review/editor drawer
  const [selectedRec, setSelectedRec] = useState<AIRecommendation | null>(null);
  const [versions, setVersions] = useState<AIRecommendationVersion[]>([]);
  const [editableValue, setEditableValue] = useState("");
  const [userGuidance, setUserGuidance] = useState("");
  const [copied, setCopied] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  // Modals
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [showSingleModal, setShowSingleModal] = useState(false);
  const [singlePageUrl, setSinglePageUrl] = useState("");
  const [singleRecType, setSingleRecType] = useState<RecommendationType>("title_optimization");
  const [selectedBulkTypes, setSelectedBulkTypes] = useState<RecommendationType[]>([
    "title_optimization",
    "meta_description",
  ]);

  // Load recommendations & usage
  const loadData = useCallback(async () => {
    if (!orgId || !websiteId) return;
    setLoading(true);
    setError(null);
    try {
      const [recsRes, usageRes, quotasRes] = await Promise.all([
        api.listAIRecommendations(orgId, websiteId, {
          status: statusFilter === "all" ? undefined : statusFilter,
          recommendation_type: typeFilter === "all" ? undefined : typeFilter,
          priority: priorityFilter === "all" ? undefined : priorityFilter,
          page: 1,
          page_size: 50,
        }),
        api.getAIUsageSummary(orgId).catch(() => null),
        api.getAIQuotaDetails(orgId).catch(() => null),
      ]);

      setRecommendations(recsRes.items || []);
      setTotalCount(recsRes.total || 0);
      setUsageSummary(usageRes);
      setQuotaDetails(quotasRes);
    } catch (err: any) {
      console.error("Failed to load AI recommendations:", err);
      setError(err?.message || "Failed to load AI recommendations.");
    } finally {
      setLoading(false);
    }
  }, [orgId, websiteId, statusFilter, typeFilter, priorityFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Open Recommendation Drawer & Load History
  const handleOpenReview = async (rec: AIRecommendation) => {
    setSelectedRec(rec);
    setEditableValue(rec.suggested_value);
    setUserGuidance("");
    setShowRejectInput(false);
    setCopied(false);
    try {
      const history = await api.getAIRecommendationHistory(orgId, rec.id);
      setVersions(history);
    } catch (err) {
      console.error("Failed to load history:", err);
      setVersions([]);
    }
  };

  // Approve
  const handleApprove = async () => {
    if (!selectedRec) return;
    setActionLoading(true);
    try {
      const updated = await api.approveAIRecommendation(orgId, selectedRec.id);
      setSelectedRec(updated);
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setSuccessMessage("Recommendation proposal marked as approved for editorial review.");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to approve recommendation.");
    } finally {
      setActionLoading(false);
    }
  };

  // Reject
  const handleReject = async () => {
    if (!selectedRec) return;
    setActionLoading(true);
    try {
      const updated = await api.rejectAIRecommendation(orgId, selectedRec.id, {
        reason: rejectReason || undefined,
      });
      setSelectedRec(updated);
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setShowRejectInput(false);
      setRejectReason("");
      setSuccessMessage("Recommendation proposal rejected.");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to reject recommendation.");
    } finally {
      setActionLoading(false);
    }
  };

  // Save manual edit
  const handleSaveEdit = async () => {
    if (!selectedRec || !editableValue.trim()) return;
    setActionLoading(true);
    try {
      const updated = await api.editAIRecommendation(orgId, selectedRec.id, {
        suggested_value: editableValue.trim(),
        user_guidance: "Manual human edit",
      });
      setSelectedRec(updated);
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      const history = await api.getAIRecommendationHistory(orgId, updated.id);
      setVersions(history);
      setSuccessMessage(`Changes saved. Proposal is now version v${updated.current_version_number}.`);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to save edited recommendation.");
    } finally {
      setActionLoading(false);
    }
  };

  // Save as draft
  const handleSaveDraft = async () => {
    if (!selectedRec) return;
    setActionLoading(true);
    try {
      const updated = await api.editAIRecommendation(orgId, selectedRec.id, {
        status: "draft",
      });
      setSelectedRec(updated);
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setSuccessMessage("Recommendation saved as draft.");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to save draft.");
    } finally {
      setActionLoading(false);
    }
  };

  // Regenerate with user guidance
  const handleRegenerate = async () => {
    if (!selectedRec) return;
    setActionLoading(true);
    try {
      const updated = await api.regenerateAIRecommendation(orgId, selectedRec.id, {
        user_guidance: userGuidance.trim() || undefined,
      });
      setSelectedRec(updated);
      setEditableValue(updated.suggested_value);
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      const history = await api.getAIRecommendationHistory(orgId, updated.id);
      setVersions(history);
      setUserGuidance("");
      setSuccessMessage(`Regenerated proposal v${updated.current_version_number} using AI guidance.`);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to regenerate recommendation.");
    } finally {
      setActionLoading(false);
    }
  };

  // Copy to clipboard
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Single page generation submit
  const handleSingleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singlePageUrl.trim()) return;
    setActionLoading(true);
    setError(null);
    try {
      const rec = await api.generateAIRecommendation(orgId, websiteId, {
        page_url: singlePageUrl.trim(),
        recommendation_type: singleRecType,
      });
      setShowSingleModal(false);
      setSinglePageUrl("");
      await loadData();
      handleOpenReview(rec);
      setSuccessMessage("Generated AI proposal successfully.");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to generate recommendation.");
    } finally {
      setActionLoading(false);
    }
  };

  // Bulk generate submit
  const handleBulkGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedBulkTypes.length === 0) return;
    setActionLoading(true);
    setError(null);
    try {
      const job = await api.bulkGenerateAIRecommendations(orgId, websiteId, {
        recommendation_types: selectedBulkTypes,
        page_limit: 10,
      });
      setShowBulkModal(false);
      setSuccessMessage(`Queued background AI optimization job (Job ID: ${job.id.slice(0, 8)}).`);
      setTimeout(() => setSuccessMessage(null), 5000);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to queue bulk AI optimization.");
    } finally {
      setActionLoading(false);
    }
  };

  // Derived counts
  const needsReviewCount = recommendations.filter((r) => r.status === "needs_review").length;
  const approvedCount = recommendations.filter((r) => r.status === "approved").length;
  const rejectedCount = recommendations.filter((r) => r.status === "rejected").length;

  const filteredList = recommendations.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.page_url.toLowerCase().includes(q) ||
      r.suggested_value.toLowerCase().includes(q) ||
      (r.current_value && r.current_value.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {successMessage && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-400" />
              AI SEO Optimization Engine
            </h1>
            <Badge variant="outline" className="border-purple-500/30 text-purple-300 bg-purple-500/10 text-xs">
              Gemini 2.5 Flash
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Grounded technical SEO proposals synthesized from verified crawl and audit evidence.
            Proposals require human review and never auto-modify customer sites.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="border-white/10 hover:bg-white/5"
          >
            <RotateCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSingleModal(true)}
            className="border-purple-500/30 text-purple-300 hover:bg-purple-500/10"
          >
            <Zap className="w-4 h-4 mr-2 text-purple-400" />
            Optimize Page
          </Button>

          <Button
            size="sm"
            onClick={() => setShowBulkModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Bulk Optimization
          </Button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-[#121216] border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-medium">
              <span>Proposals Generated</span>
              <Sparkles className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-2">{totalCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Grounded from crawl snapshots</p>
          </CardContent>
        </Card>

        <Card className="bg-[#121216] border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-medium">
              <span>Awaiting Review</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400 mt-2">{needsReviewCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Pending editorial sign-off</p>
          </CardContent>
        </Card>

        <Card className="bg-[#121216] border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-medium">
              <span>Approved Proposals</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400 mt-2">{approvedCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Verified human approvals</p>
          </CardContent>
        </Card>

        <Card className="bg-[#121216] border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-medium">
              <span>AI Quota & Usage</span>
              <ShieldCheck className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-xl font-bold text-white mt-2">
              {usageSummary ? `${usageSummary.daily_requests_used} / ${usageSummary.daily_requests_limit}` : "--"}
              <span className="text-xs font-normal text-muted-foreground ml-1">reqs/day</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Monthly: {usageSummary ? `${(usageSummary.monthly_tokens_used / 1000).toFixed(1)}k tokens` : "0"} (~$
              {usageSummary ? usageSummary.monthly_estimated_cost_usd.toFixed(3) : "0.00"})
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#121216] p-3 rounded-lg border border-white/10">
        <div className="flex flex-wrap items-center gap-1">
          {[
            { id: "all", label: "All Statuses" },
            { id: "needs_review", label: "Awaiting Review" },
            { id: "approved", label: "Approved" },
            { id: "draft", label: "Drafts" },
            { id: "rejected", label: "Rejected" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                statusFilter === tab.id
                  ? "bg-purple-600 text-white"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* Type Select */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-[#1c1c24] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Types</option>
            <option value="title_optimization">Title Tags</option>
            <option value="meta_description">Meta Descriptions</option>
            <option value="heading_structure">Headings</option>
            <option value="content_structure">Content Structure</option>
            <option value="internal_linking">Internal Links</option>
            <option value="image_alt_guidance">Image Alt Guidance</option>
          </select>

          {/* Priority Select */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-[#1c1c24] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>

          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter by URL or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#1c1c24] border border-white/10 rounded-md pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-purple-500 w-48"
            />
          </div>
        </div>
      </div>

      {/* Recommendations List / Table */}
      {loading ? (
        <div className="p-12 text-center text-muted-foreground bg-[#121216] rounded-lg border border-white/10 flex flex-col items-center justify-center gap-3">
          <RotateCw className="w-6 h-6 animate-spin text-purple-400" />
          <p className="text-sm">Loading AI SEO recommendations...</p>
        </div>
      ) : filteredList.length === 0 ? (
        <Card className="bg-[#121216] border-white/10 p-12 text-center">
          <CardContent className="flex flex-col items-center justify-center space-y-4 max-w-md mx-auto">
            <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">No AI recommendations found</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {statusFilter !== "all" || typeFilter !== "all"
                  ? "No recommendations match the current filter criteria."
                  : "No AI recommendations have been generated for this website yet. Run bulk optimization or analyze a specific page from an audit finding."}
              </p>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <Button
                size="sm"
                onClick={() => setShowBulkModal(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Run Bulk Optimization
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSingleModal(true)}
                className="border-white/10 text-white hover:bg-white/5"
              >
                Optimize Specific Page
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredList.map((rec) => {
            const config = TYPE_CONFIG[rec.recommendation_type] || {
              label: rec.recommendation_type,
              icon: FileText,
              color: "text-muted-foreground",
              bg: "bg-white/5 border-white/10",
            };
            const Icon = config.icon;

            return (
              <div
                key={rec.id}
                onClick={() => handleOpenReview(rec)}
                className="p-4 bg-[#121216] hover:bg-[#181820] border border-white/10 rounded-lg transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${config.bg} ${config.color}`}
                    >
                      <Icon className="w-3 h-3" />
                      {config.label}
                    </span>

                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        rec.priority === "high"
                          ? "border-rose-500/40 text-rose-400 bg-rose-500/10"
                          : rec.priority === "medium"
                          ? "border-amber-500/40 text-amber-400 bg-amber-500/10"
                          : "border-slate-500/40 text-slate-400 bg-slate-500/10"
                      }`}
                    >
                      {rec.priority.toUpperCase()}
                    </Badge>

                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        rec.status === "approved"
                          ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
                          : rec.status === "rejected"
                          ? "border-rose-500/40 text-rose-400 bg-rose-500/10"
                          : rec.status === "draft"
                          ? "border-slate-500/40 text-slate-400 bg-slate-500/10"
                          : "border-amber-500/40 text-amber-400 bg-amber-500/10"
                      }`}
                    >
                      {rec.status.replace("_", " ").toUpperCase()}
                    </Badge>

                    <span className="text-xs text-muted-foreground font-mono">v{rec.current_version_number}</span>

                    <span className="text-xs text-muted-foreground ml-auto hidden sm:inline">
                      {formatDate(rec.created_at)}
                    </span>
                  </div>

                  <div className="font-mono text-xs text-muted-foreground truncate">{rec.page_url}</div>

                  <div className="text-sm text-foreground font-medium line-clamp-2 bg-[#0c0c10] p-2.5 rounded border border-white/5">
                    {rec.suggested_value}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-white/10 group-hover:border-purple-500/40 text-xs"
                  >
                    Review & Edit
                    <ChevronRight className="w-3.5 h-3.5 ml-1 text-muted-foreground group-hover:text-purple-400" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Review & Edit Drawer */}
      {selectedRec && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-2xl bg-[#0e0e12] border-l border-white/10 h-full overflow-y-auto flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[#121216] sticky top-0 z-10">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h2 className="text-base font-semibold text-white">Recommendation Proposal</h2>
                <Badge variant="outline" className="border-purple-500/30 text-purple-300 font-mono text-xs">
                  v{selectedRec.current_version_number}
                </Badge>
              </div>
              <button
                onClick={() => setSelectedRec(null)}
                className="text-muted-foreground hover:text-white p-1 rounded-md"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1">
              {/* Notice Banner */}
              <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-md text-xs text-purple-300 flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 text-purple-400 mt-0.5" />
                <span>
                  <strong>Safety Notice:</strong> RankForge AI produces proposals for editorial review. Approved
                  items are never pushed or applied to customer websites automatically.
                </span>
              </div>

              {/* URL & Meta */}
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Target Page</div>
                <div className="font-mono text-xs text-foreground bg-[#14141a] p-2 rounded border border-white/5 break-all flex items-center justify-between">
                  <span>{selectedRec.page_url}</span>
                  <a
                    href={selectedRec.page_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-muted-foreground hover:text-purple-400 ml-2"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>

              {/* Side-by-Side Before & After Diff */}
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                  Before & After Comparison
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Before */}
                  <div className="bg-[#121216] border border-white/5 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-rose-400">
                      <span>CURRENT VALUE (Crawl Snapshot)</span>
                      <span className="text-[10px] text-muted-foreground">
                        {selectedRec.current_value?.length || 0} chars
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono bg-[#0a0a0e] p-2.5 rounded min-h-[90px] whitespace-pre-wrap break-words">
                      {selectedRec.current_value || "[No existing value found on page]"}
                    </div>
                  </div>

                  {/* After */}
                  <div className="bg-[#121216] border border-purple-500/30 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-purple-300">
                      <span>PROPOSED AI VALUE</span>
                      <span className="text-[10px] text-muted-foreground">{editableValue.length} chars</span>
                    </div>
                    <textarea
                      value={editableValue}
                      onChange={(e) => setEditableValue(e.target.value)}
                      rows={4}
                      className="w-full text-xs text-foreground font-mono bg-[#0a0a0e] p-2.5 rounded border border-white/10 focus:outline-none focus:border-purple-500 resize-y"
                    />
                  </div>
                </div>

                {editableValue !== selectedRec.suggested_value && (
                  <div className="flex justify-end gap-2 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditableValue(selectedRec.suggested_value)}
                      className="text-xs"
                    >
                      Reset Edits
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveEdit}
                      disabled={actionLoading}
                      className="bg-purple-600 hover:bg-purple-700 text-white text-xs"
                    >
                      Save As New Version
                    </Button>
                  </div>
                )}
              </div>

              {/* Explanation & Evidence Accordion */}
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                  Technical SEO Explanation
                </div>
                <div className="bg-[#121216] border border-white/10 rounded-lg p-4 space-y-3">
                  <p className="text-xs text-foreground leading-relaxed">{selectedRec.explanation}</p>

                  {selectedRec.evidence_json?.supporting_evidence &&
                    selectedRec.evidence_json.supporting_evidence.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-white/5">
                        <div className="text-[11px] font-semibold text-muted-foreground uppercase">
                          Observed Evidence:
                        </div>
                        <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                          {selectedRec.evidence_json.supporting_evidence.map((ev, i) => (
                            <li key={i}>{ev}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {selectedRec.limitations && (
                    <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-300 flex items-start gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Reviewer Limitation:</strong> {selectedRec.limitations}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Regeneration Section with User Instructions */}
              <div className="space-y-2 bg-[#121216] border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <RotateCw className="w-3.5 h-3.5 text-purple-400" />
                    Regenerate With Guidance
                  </span>
                  <span className="text-[10px] text-muted-foreground">Creates new version</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Provide optional tone, length, or branding instructions (e.g. "Keep under 55 characters", "Use a direct
                  editorial tone").
                </p>
                <div className="flex gap-2 pt-1">
                  <input
                    type="text"
                    placeholder="e.g. Make it more concise and preserve the brand name..."
                    value={userGuidance}
                    onChange={(e) => setUserGuidance(e.target.value)}
                    className="flex-1 bg-[#0a0a0e] border border-white/10 rounded px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-purple-500"
                  />
                  <Button
                    size="sm"
                    onClick={handleRegenerate}
                    disabled={actionLoading}
                    className="bg-purple-600 hover:bg-purple-700 text-white text-xs shrink-0"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1" />
                    Regenerate
                  </Button>
                </div>
              </div>

              {/* Version History Timeline */}
              {versions.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5" />
                    Version History ({versions.length})
                  </div>
                  <div className="space-y-2">
                    {versions.map((ver) => (
                      <div
                        key={ver.id}
                        className={`p-3 rounded-lg border text-xs space-y-1 ${
                          ver.version_number === selectedRec.current_version_number
                            ? "bg-purple-500/10 border-purple-500/30 text-purple-200"
                            : "bg-[#121216] border-white/5 text-muted-foreground"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white">Version v{ver.version_number}</span>
                          <span className="text-[10px] text-muted-foreground">{formatDate(ver.created_at)}</span>
                        </div>
                        <div className="font-mono text-xs">{ver.suggested_value}</div>
                        {ver.user_guidance && (
                          <div className="text-[11px] italic text-muted-foreground">
                            Guidance: &ldquo;{ver.user_guidance}&rdquo;
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Drawer Actions Footer */}
            <div className="p-4 border-t border-white/10 bg-[#121216] sticky bottom-0 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(editableValue)}
                  className="border-white/10 text-xs"
                >
                  {copied ? <Check className="w-3.5 h-3.5 mr-1 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
                  {copied ? "Copied" : "Copy"}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveDraft}
                  disabled={actionLoading}
                  className="border-white/10 text-xs"
                >
                  Save Draft
                </Button>
              </div>

              <div className="flex items-center gap-2">
                {showRejectInput ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      placeholder="Rejection reason..."
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      className="bg-[#0a0a0e] border border-white/10 rounded px-2 py-1 text-xs text-foreground w-40"
                    />
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={handleReject}
                      disabled={actionLoading}
                      className="text-xs"
                    >
                      Confirm Reject
                    </Button>
                    <button
                      onClick={() => setShowRejectInput(false)}
                      className="text-muted-foreground hover:text-white p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRejectInput(true)}
                    disabled={actionLoading}
                    className="border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs"
                  >
                    <ThumbsDown className="w-3.5 h-3.5 mr-1" />
                    Reject
                  </Button>
                )}

                <Button
                  size="sm"
                  onClick={handleApprove}
                  disabled={actionLoading || selectedRec.status === "approved"}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium"
                >
                  <ThumbsUp className="w-3.5 h-3.5 mr-1" />
                  {selectedRec.status === "approved" ? "Approved" : "Approve Proposal"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Single Page Generation Modal */}
      {showSingleModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121216] border border-white/10 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-purple-400" />
                Generate AI Recommendation
              </h3>
              <button onClick={() => setShowSingleModal(false)} className="text-muted-foreground hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSingleGenerate} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Target Page URL</label>
                <input
                  type="url"
                  required
                  placeholder={`https://${domain}/example-page`}
                  value={singlePageUrl}
                  onChange={(e) => setSinglePageUrl(e.target.value)}
                  className="w-full bg-[#0a0a0e] border border-white/10 rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Recommendation Type</label>
                <select
                  value={singleRecType}
                  onChange={(e) => setSingleRecType(e.target.value as RecommendationType)}
                  className="w-full bg-[#0a0a0e] border border-white/10 rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:border-purple-500"
                >
                  <option value="title_optimization">Title Tag Optimization</option>
                  <option value="meta_description">Meta Description Optimization</option>
                  <option value="heading_structure">Heading Hierarchy</option>
                  <option value="content_structure">Content Structure Advisory</option>
                  <option value="internal_linking">Internal Linking Suggestions</option>
                  <option value="image_alt_guidance">Image Accessibility Guidance</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSingleModal(false)}
                  className="border-white/10 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading}
                  className="bg-purple-600 hover:bg-purple-700 text-white text-xs"
                >
                  {actionLoading ? <RotateCw className="w-3.5 h-3.5 animate-spin mr-1" /> : <Sparkles className="w-3.5 h-3.5 mr-1" />}
                  Generate
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Optimization Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121216] border border-white/10 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                Queue Bulk AI Optimization
              </h3>
              <button onClick={() => setShowBulkModal(false)} className="text-muted-foreground hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground">
              Analyzes up to 10 crawled pages on <strong>{domain}</strong> asynchronously using background Celery workers.
            </p>

            <form onSubmit={handleBulkGenerate} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Select Recommendation Types</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: "title_optimization", label: "Title Tags" },
                    { id: "meta_description", label: "Meta Descriptions" },
                    { id: "heading_structure", label: "Heading Hierarchy" },
                    { id: "content_structure", label: "Content Structure" },
                    { id: "internal_linking", label: "Internal Links" },
                    { id: "image_alt_guidance", label: "Image Alt Text" },
                  ].map((item) => {
                    const isChecked = selectedBulkTypes.includes(item.id as RecommendationType);
                    return (
                      <label
                        key={item.id}
                        className={`p-2.5 rounded border text-xs flex items-center gap-2 cursor-pointer transition-colors ${
                          isChecked
                            ? "bg-purple-500/10 border-purple-500/40 text-purple-300"
                            : "bg-[#0a0a0e] border-white/5 text-muted-foreground"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedBulkTypes((prev) => [...prev, item.id as RecommendationType]);
                            } else {
                              setSelectedBulkTypes((prev) => prev.filter((t) => t !== item.id));
                            }
                          }}
                          className="rounded border-white/20 text-purple-600 focus:ring-0"
                        />
                        <span>{item.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowBulkModal(false)}
                  className="border-white/10 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading || selectedBulkTypes.length === 0}
                  className="bg-purple-600 hover:bg-purple-700 text-white text-xs"
                >
                  {actionLoading ? <RotateCw className="w-3.5 h-3.5 animate-spin mr-1" /> : <Sparkles className="w-3.5 h-3.5 mr-1" />}
                  Queue Batch Job
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
