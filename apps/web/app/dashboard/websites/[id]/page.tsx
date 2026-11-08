"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Globe,
  ArrowLeft,
  ExternalLink,
  ShieldAlert,
  Clock,
  CheckCircle2,
  Copy,
  Check,
  SearchCode,
  Archive,
  RotateCcw,
  Trash2,
  Edit2,
  AlertCircle,
  FileCode,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type WebsiteProject, type Organization } from "@/lib/api-client";

export default function WebsiteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const websiteId = params?.id as string;

  const [project, setProject] = useState<WebsiteProject | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string>("");
  const [verificationData, setVerificationData] = useState<any | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<"dns_txt" | "meta_tag" | "file_upload">("dns_txt");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Edit metadata modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Audit trigger state
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState<any | null>(null);

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

        // Find the organization that owns this website
        for (const org of orgs) {
          try {
            const p = await api.getWebsite(org.id, websiteId);
            if (p) {
              setProject(p);
              setCurrentOrgId(org.id);
              setEditName(p.name);
              setEditDescription(p.description || "");

              // Load verification instructions
              const verif = await api.getVerificationInstructions(p.id, selectedMethod).catch(() => null);
              setVerificationData(verif);
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

  const handleMethodChange = async (method: "dns_txt" | "meta_tag" | "file_upload") => {
    setSelectedMethod(method);
    if (project) {
      const verif = await api.getVerificationInstructions(project.id, method).catch(() => null);
      setVerificationData(verif);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
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

  const handleTriggerAudit = async () => {
    if (!project) return;
    setIsAuditing(true);
    setError(null);

    try {
      const job = await api.triggerAudit(project.id);
      // Poll result
      setTimeout(async () => {
        try {
          const res = await api.getAuditResult(job.job_id);
          setAuditResult(res);
        } catch {}
        setIsAuditing(false);
      }, 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate preflight audit");
      setIsAuditing(false);
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
    <div className="space-y-6 max-w-5xl">
      {/* Navigation and Top Bar */}
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
                    project.archived_at
                      ? "border-amber-500/50 text-amber-400 bg-amber-500/10"
                      : "border-rf-border text-rf-text-secondary bg-rf-surface/50"
                  }`}
                >
                  {project.archived_at ? "Archived" : "Pending Verification"}
                </Badge>
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

            <Button
              onClick={handleTriggerAudit}
              disabled={isAuditing}
              className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5"
            >
              <SearchCode className="w-3.5 h-3.5" />
              <span>{isAuditing ? "Scanning Site..." : "Run Preflight Audit"}</span>
            </Button>
          </div>
          {project.description && (
            <CardDescription className="text-xs pt-2">{project.description}</CardDescription>
          )}
        </CardHeader>
      </Card>

      {/* Audit Result Display if run */}
      {auditResult && (
        <Card className="border-rf-crimson/40">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Preflight Audit Complete</span>
              </CardTitle>
              <span className="text-sm font-mono font-bold text-rf-crimson">
                Health Score: {auditResult.score}/100
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded bg-rf-surface border border-rf-border font-mono text-[11px]">
              <div>
                <span className="text-rf-text-muted">Target:</span> {auditResult.url}
              </div>
              <div>
                <span className="text-rf-text-muted">Latency:</span> {auditResult.response_time_ms.toFixed(1)}ms
              </div>
              <div>
                <span className="text-rf-text-muted">Issues:</span> {auditResult.issues_count}
              </div>
            </div>

            {auditResult.issues && auditResult.issues.length > 0 && (
              <div className="space-y-1.5">
                <div className="font-medium text-rf-text">Discovered Security & Architecture Items:</div>
                <div className="space-y-1">
                  {auditResult.issues.map((issue: any) => (
                    <div
                      key={issue.id}
                      className="p-2 rounded border border-rf-border bg-rf-surface/60 flex items-center justify-between text-[11px]"
                    >
                      <span className="text-rf-text">{issue.title}</span>
                      <Badge variant="outline" className="capitalize font-mono text-[9px]">
                        {issue.severity}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Verification Instructions Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Domain Ownership Verification</CardTitle>
              <CardDescription>
                Prove administrative control of {project.domain} before configuring write integrations
              </CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-[10px] text-amber-400 border-amber-500/40">
              Phase 3 Live Checks
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-md border border-rf-border bg-rf-surface/40 text-xs text-rf-text-secondary flex items-start gap-2.5">
            <Clock className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-medium text-rf-text">Verification tokens are generated and ready.</span>
              <p className="text-[11px]">
                In Phase 2, token generation, cryptographic storage, and verification instructions are active. Automated live DNS and crawler verification checks will be executed in Phase 3.
              </p>
            </div>
          </div>

          {/* Verification Method Tabs */}
          <div className="flex items-center gap-2 border-b border-rf-border pb-2 text-xs">
            {[
              { id: "dns_txt", label: "DNS TXT Record" },
              { id: "meta_tag", label: "HTML <meta> Tag" },
              { id: "file_upload", label: "Verification File" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleMethodChange(tab.id as any)}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  selectedMethod === tab.id
                    ? "bg-rf-crimson text-white"
                    : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Method Content */}
          {selectedMethod === "dns_txt" && (
            <div className="space-y-3 text-xs">
              <p className="text-rf-text-secondary">
                Add the following TXT record to the DNS configuration of <span className="font-mono text-rf-text">{project.domain}</span>:
              </p>
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface font-mono text-[11px] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">Record Type:</span>
                  <span className="text-rf-text font-bold">TXT</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">Host / Name:</span>
                  <span className="text-rf-text">@ (or root)</span>
                </div>
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-rf-border/40">
                  <span className="text-rf-text-muted flex-shrink-0">Value:</span>
                  <span className="truncate text-rf-crimson">{verificationData?.dns_txt_record || project.verification_token}</span>
                  <button
                    onClick={() => copyToClipboard(verificationData?.dns_txt_record || project.verification_token, "dns")}
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy record"
                  >
                    {copiedKey === "dns" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {selectedMethod === "meta_tag" && (
            <div className="space-y-3 text-xs">
              <p className="text-rf-text-secondary">
                Insert this meta tag inside the <span className="font-mono text-rf-text">&lt;head&gt;</span> section of your website's home page:
              </p>
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface font-mono text-[11px] flex items-center justify-between gap-2">
                <span className="truncate text-rf-text">{verificationData?.meta_tag_snippet || `<meta name="rankforge-site-verification" content="${project.verification_token}" />`}</span>
                <button
                  onClick={() => copyToClipboard(verificationData?.meta_tag_snippet || `<meta name="rankforge-site-verification" content="${project.verification_token}" />`, "meta")}
                  className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                  title="Copy snippet"
                >
                  {copiedKey === "meta" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          )}

          {selectedMethod === "file_upload" && (
            <div className="space-y-3 text-xs">
              <p className="text-rf-text-secondary">
                Upload a plain text verification file to the root of your web server:
              </p>
              <div className="p-3 rounded-md border border-rf-border bg-rf-surface font-mono text-[11px] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-rf-text-muted">File Path:</span>
                  <span className="text-rf-text">{verificationData?.file_upload_path || `/${project.verification_token}.txt`}</span>
                </div>
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-rf-border/40">
                  <span className="text-rf-text-muted flex-shrink-0">File Content:</span>
                  <span className="truncate text-rf-crimson">{verificationData?.file_upload_content || project.verification_token}</span>
                  <button
                    onClick={() => copyToClipboard(verificationData?.file_upload_content || project.verification_token, "file")}
                    className="p-1 rounded hover:bg-rf-border/50 text-rf-text-muted hover:text-rf-text flex-shrink-0"
                    title="Copy content"
                  >
                    {copiedKey === "file" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

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
