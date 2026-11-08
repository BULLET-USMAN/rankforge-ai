"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  Plus,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Trash2,
  Copy,
  ExternalLink,
  SearchCode,
  X,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

export default function WebsitesPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [verificationData, setVerificationData] = useState<any | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<"dns_txt" | "meta_tag" | "file_upload">("dns_txt");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [primaryUrl, setPrimaryUrl] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadProjects = async () => {
    try {
      const orgs = await api.listOrganizations().catch(() => []);
      setOrganizations(orgs);
      const defaultOrgId = orgs[0]?.id;
      const projs = await api.listProjects(defaultOrgId).catch(() => []);
      setProjects(projs || []);
      if (projs && projs.length > 0 && !selectedProject) {
        handleSelectProject(projs[0]);
      }
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleSelectProject = async (project: any) => {
    setSelectedProject(project);
    try {
      const verif = await api.getVerificationInstructions(project.id, selectedMethod);
      setVerificationData(verif);
    } catch {
      // Error handling
    }
  };

  const handleMethodChange = async (method: "dns_txt" | "meta_tag" | "file_upload") => {
    setSelectedMethod(method);
    if (selectedProject) {
      try {
        const verif = await api.getVerificationInstructions(selectedProject.id, method);
        setVerificationData(verif);
      } catch {}
    }
  };

  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError("Project name is required.");
      return;
    }
    if (!domain.trim() || !domain.includes(".")) {
      setFormError("A valid domain (e.g. example.com) is required.");
      return;
    }
    if (!primaryUrl.startsWith("http://") && !primaryUrl.startsWith("https://")) {
      setFormError("Primary URL must begin with http:// or https://");
      return;
    }

    setIsSubmitting(true);
    try {
      // Create organization if none exists
      let orgId = organizations[0]?.id;
      if (!orgId) {
        const newOrg = await api.createOrganization({
          name: "Acme Digital",
          slug: "acme-digital",
        });
        orgId = newOrg.id;
      }

      const created = await api.createProject({
        organization_id: orgId,
        name: name.trim(),
        domain: domain.trim(),
        primary_url: primaryUrl.trim(),
      });

      setName("");
      setDomain("");
      setPrimaryUrl("");
      setIsAddOpen(false);
      await loadProjects();
      handleSelectProject(created);
    } catch (err: any) {
      setFormError(err.message || "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (projectId: string) => {
    if (!confirm("Are you sure you want to delete this website project?")) return;
    try {
      await api.deleteProject(projectId);
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
        setVerificationData(null);
      }
      await loadProjects();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-rf-text tracking-tight">Website Projects</h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Manage monitored domains, ownership verification protocols, and project scopes.
          </p>
        </div>
        <Button onClick={() => setIsAddOpen(true)} size="sm">
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          Add Website Project
        </Button>
      </div>

      {/* Add Project Modal / Card */}
      {isAddOpen && (
        <Card className="border-rf-crimson/50 bg-rf-surface/90">
          <CardHeader className="flex flex-row items-center justify-between py-4">
            <div>
              <CardTitle>Register Website Project</CardTitle>
              <CardDescription>
                Configure the target website domain for technical auditing.
              </CardDescription>
            </div>
            <button
              onClick={() => setIsAddOpen(false)}
              className="text-rf-text-secondary hover:text-rf-text"
            >
              <X className="w-4 h-4" />
            </button>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddProject} className="space-y-4">
              {formError && (
                <div className="p-2.5 rounded bg-rf-error/15 border border-rf-error/30 text-xs text-red-300">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text">Project Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Acme Production"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-bg text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text">Domain</label>
                  <input
                    type="text"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    placeholder="acme.com"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-bg text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-rf-text">Primary URL</label>
                  <input
                    type="url"
                    value={primaryUrl}
                    onChange={(e) => setPrimaryUrl(e.target.value)}
                    placeholder="https://acme.com"
                    className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-bg text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsAddOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={isSubmitting}>
                  {isSubmitting ? "Registering..." : "Create Project"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Main Grid: Projects List + Verification Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Project List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-rf-text-muted">
            Configured Projects ({projects.length})
          </div>

          {projects.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-xs text-rf-text-secondary">
                No website projects registered. Click &ldquo;Add Website Project&rdquo; to begin.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {projects.map((proj) => {
                const isSelected = selectedProject?.id === proj.id;
                return (
                  <div
                    key={proj.id}
                    onClick={() => handleSelectProject(proj)}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                      isSelected
                        ? "border-rf-crimson bg-rf-surface"
                        : "border-rf-border bg-rf-bg-secondary hover:border-rf-border/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-rf-text">{proj.name}</span>
                      <Badge variant={proj.is_verified ? "success" : "warning"} className="text-[10px]">
                        {proj.is_verified ? "Verified" : "Pending"}
                      </Badge>
                    </div>
                    <div className="text-xs font-mono text-rf-text-secondary mt-1 truncate">
                      {proj.domain}
                    </div>
                    <div className="text-[11px] text-rf-text-muted mt-2">
                      Added: {formatDate(proj.created_at)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Selected Project Ownership Verification & Actions */}
        <div className="lg:col-span-2 space-y-4">
          {selectedProject ? (
            <Card>
              <CardHeader className="py-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle>{selectedProject.name}</CardTitle>
                    <CardDescription>{selectedProject.primary_url}</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/dashboard/audits?project_id=${selectedProject.id}`}>
                      <Button size="sm" className="text-xs">
                        <SearchCode className="w-3.5 h-3.5 mr-1.5" />
                        Run Audit
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(selectedProject.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Site Ownership Verification Box */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-semibold text-rf-text flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-rf-crimson" />
                      Domain Ownership Verification
                    </div>
                    <Badge variant={selectedProject.is_verified ? "success" : "warning"}>
                      {selectedProject.is_verified ? "Ownership Confirmed" : "Verification Required"}
                    </Badge>
                  </div>

                  <p className="text-xs text-rf-text-secondary leading-relaxed">
                    To enable automated remediation and authorized search index synchronization,
                    verify domain ownership using any of the three secure verification protocols.
                  </p>

                  {/* Method Tabs */}
                  <div className="flex border-b border-rf-border text-xs">
                    <button
                      onClick={() => handleMethodChange("dns_txt")}
                      className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                        selectedMethod === "dns_txt"
                          ? "border-rf-crimson text-rf-text"
                          : "border-transparent text-rf-text-secondary hover:text-rf-text"
                      }`}
                    >
                      DNS TXT Record
                    </button>
                    <button
                      onClick={() => handleMethodChange("meta_tag")}
                      className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                        selectedMethod === "meta_tag"
                          ? "border-rf-crimson text-rf-text"
                          : "border-transparent text-rf-text-secondary hover:text-rf-text"
                      }`}
                    >
                      HTML Meta Tag
                    </button>
                    <button
                      onClick={() => handleMethodChange("file_upload")}
                      className={`pb-2 px-3 font-medium transition-colors border-b-2 ${
                        selectedMethod === "file_upload"
                          ? "border-rf-crimson text-rf-text"
                          : "border-transparent text-rf-text-secondary hover:text-rf-text"
                      }`}
                    >
                      File Upload
                    </button>
                  </div>

                  {/* Method Instructions */}
                  {verificationData && (
                    <div className="p-4 rounded-md border border-rf-border bg-rf-surface/60 space-y-3 text-xs">
                      {selectedMethod === "dns_txt" && (
                        <div className="space-y-2">
                          <div className="text-rf-text font-medium">
                            Add a TXT record to your DNS configuration:
                          </div>
                          <div className="space-y-1 font-mono text-[11px] text-rf-text-secondary bg-rf-bg p-3 rounded border border-rf-border/40 flex items-center justify-between">
                            <span className="select-all">{verificationData.dns_txt_record}</span>
                            <button
                              onClick={() => copyToClipboard(verificationData.dns_txt_record, "dns")}
                              className="text-rf-text-muted hover:text-rf-text ml-2"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {copiedKey === "dns" && (
                            <span className="text-[10px] text-green-400">Copied to clipboard</span>
                          )}
                        </div>
                      )}

                      {selectedMethod === "meta_tag" && (
                        <div className="space-y-2">
                          <div className="text-rf-text font-medium">
                            Insert this meta tag inside the &lt;head&gt; element of your homepage:
                          </div>
                          <div className="space-y-1 font-mono text-[11px] text-rf-text-secondary bg-rf-bg p-3 rounded border border-rf-border/40 flex items-center justify-between">
                            <span className="select-all">{verificationData.meta_tag_snippet}</span>
                            <button
                              onClick={() => copyToClipboard(verificationData.meta_tag_snippet, "meta")}
                              className="text-rf-text-muted hover:text-rf-text ml-2"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {copiedKey === "meta" && (
                            <span className="text-[10px] text-green-400">Copied to clipboard</span>
                          )}
                        </div>
                      )}

                      {selectedMethod === "file_upload" && (
                        <div className="space-y-2">
                          <div className="text-rf-text font-medium">
                            Upload a plain text file to your server root at:
                          </div>
                          <div className="font-mono text-[11px] text-rf-text-secondary bg-rf-bg p-2 rounded border border-rf-border/40">
                            {verificationData.file_upload_path}
                          </div>
                          <div className="text-rf-text font-medium mt-2">File content:</div>
                          <div className="font-mono text-[11px] text-rf-text-secondary bg-rf-bg p-2 rounded border border-rf-border/40 flex items-center justify-between">
                            <span>{verificationData.file_upload_content}</span>
                            <button
                              onClick={() => copyToClipboard(verificationData.file_upload_content, "file")}
                              className="text-rf-text-muted hover:text-rf-text ml-2"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-xs text-rf-text-secondary">
                Select a website project from the left panel to inspect domain settings.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
