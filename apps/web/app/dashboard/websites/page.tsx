"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Globe,
  Plus,
  Search,
  ExternalLink,
  Archive,
  RotateCcw,
  Trash2,
  AlertCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type WebsiteProject, type Organization } from "@/lib/api-client";

export default function WebsitesPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>("");
  const [websites, setWebsites] = useState<WebsiteProject[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add Website Dialog State
  const [showAddModal, setShowAddModal] = useState(false);
  const [siteName, setSiteName] = useState("");
  const [domainOrUrl, setDomainOrUrl] = useState("");
  const [siteDescription, setSiteDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Load organizations
  useEffect(() => {
    api
      .listOrganizations()
      .then((orgs) => {
        if (orgs && orgs.length > 0) {
          setOrganizations(orgs);
          setSelectedOrgId(orgs[0].id);
        } else {
          setIsLoading(false);
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to load organizations");
        setIsLoading(false);
      });
  }, []);

  // Fetch websites for selected organization
  const fetchWebsites = (orgId: string, search?: string, archived?: boolean) => {
    setIsLoading(true);
    api
      .listWebsites(orgId, search, archived)
      .then((data) => {
        setWebsites(data || []);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load websites");
        setIsLoading(false);
      });
  };

  useEffect(() => {
    if (!selectedOrgId) return;
    fetchWebsites(selectedOrgId, searchQuery, includeArchived);
  }, [selectedOrgId, includeArchived]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId) return;
    fetchWebsites(selectedOrgId, searchQuery, includeArchived);
  };

  const handleAddWebsite = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!siteName.trim()) {
      setFormError("Website name is required.");
      return;
    }
    if (!domainOrUrl.trim()) {
      setFormError("Domain or URL is required.");
      return;
    }

    // Client-side SSRF validation check
    const badTargets = ["127.0.0.1", "169.254.169.254", "localhost", "10.", "192.168."];
    if (badTargets.some((b) => domainOrUrl.includes(b))) {
      setFormError("Private IP addresses, loopback hosts, and cloud metadata endpoints are strictly prohibited.");
      return;
    }

    setIsSubmitting(true);

    try {
      await api.createWebsite(selectedOrgId, {
        name: siteName.trim(),
        domain_or_url: domainOrUrl.trim(),
        description: siteDescription.trim() || undefined,
      });

      setShowAddModal(false);
      setSiteName("");
      setDomainOrUrl("");
      setSiteDescription("");
      fetchWebsites(selectedOrgId, searchQuery, includeArchived);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add website project");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleArchive = async (websiteId: string) => {
    if (!selectedOrgId) return;
    try {
      await api.archiveWebsite(selectedOrgId, websiteId);
      fetchWebsites(selectedOrgId, searchQuery, includeArchived);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive website");
    }
  };

  const handleRestore = async (websiteId: string) => {
    if (!selectedOrgId) return;
    try {
      await api.restoreWebsite(selectedOrgId, websiteId);
      fetchWebsites(selectedOrgId, searchQuery, includeArchived);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to restore website");
    }
  };

  const handleDelete = async (websiteId: string) => {
    if (!selectedOrgId) return;
    if (!confirm("Are you sure you want to permanently delete this website project and its audit records?")) return;

    try {
      await api.deleteWebsite(selectedOrgId, websiteId);
      setWebsites(websites.filter((w) => w.id !== websiteId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete website");
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-rf-text">Website Projects</h1>
          <p className="text-xs text-rf-text-secondary mt-1">
            Manage your tracked domains, verify ownership, and initiate technical crawls
          </p>
        </div>
        <div className="flex items-center gap-2">
          {organizations.length > 1 && (
            <select
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
              className="h-8 px-2.5 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:outline-none"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          )}
          <Button
            onClick={() => {
              setFormError(null);
              setShowAddModal(true);
            }}
            className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Website</span>
          </Button>
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

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-rf-border bg-rf-bg-secondary">
        <form onSubmit={handleSearch} className="flex-1 max-w-md relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or domain (e.g. acme.com)..."
            className="w-full h-8 pl-8 pr-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
          />
          <Search className="w-3.5 h-3.5 text-rf-text-muted absolute left-2.5 top-2.5 pointer-events-none" />
        </form>

        <div className="flex items-center gap-4 text-xs text-rf-text-secondary">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => setIncludeArchived(e.target.checked)}
              className="rounded border-rf-border bg-rf-surface text-rf-crimson focus:ring-0"
            />
            <span>Include archived projects</span>
          </label>
          <span className="font-mono text-[11px] text-rf-text-muted">
            {websites.length} {websites.length === 1 ? "project" : "projects"}
          </span>
        </div>
      </div>

      {/* Website Projects Grid / Table */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-rf-text-muted">Loading website projects...</div>
      ) : websites.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent className="space-y-3">
            <div className="mx-auto w-12 h-12 rounded-full bg-rf-surface border border-rf-border flex items-center justify-center">
              <Globe className="w-6 h-6 text-rf-text-muted" />
            </div>
            <div className="space-y-1">
              <h3 className="font-semibold text-sm text-rf-text">No Website Projects Found</h3>
              <p className="text-xs text-rf-text-secondary max-w-sm mx-auto">
                {searchQuery
                  ? "No projects match your search criteria. Try a different query or clear the filter."
                  : "Add your first website to begin monitoring technical SEO health and crawl performance."}
              </p>
            </div>
            <Button
              onClick={() => setShowAddModal(true)}
              className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8 inline-flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Your First Website</span>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {websites.map((project) => (
            <Card
              key={project.id}
              className={`flex flex-col justify-between transition-all ${
                project.archived_at ? "opacity-60 border-dashed" : "hover:border-rf-border/80"
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <CardTitle className="text-sm font-semibold truncate text-rf-text">
                      {project.name}
                    </CardTitle>
                    <div className="flex items-center gap-1.5 text-xs font-mono text-rf-text-secondary">
                      <Globe className="w-3.5 h-3.5 text-rf-crimson flex-shrink-0" />
                      <span className="truncate">{project.domain}</span>
                      <a
                        href={project.primary_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-rf-text-muted hover:text-rf-text"
                        title="Open external website"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>

                  <Badge
                    variant="outline"
                    className={`font-mono text-[10px] whitespace-nowrap ${
                      project.archived_at
                        ? "border-amber-500/50 text-amber-400 bg-amber-500/10"
                        : "border-rf-border text-rf-text-secondary bg-rf-surface/50"
                    }`}
                  >
                    {project.archived_at ? "Archived" : "Pending Verification"}
                  </Badge>
                </div>
                {project.description && (
                  <CardDescription className="text-xs line-clamp-2 pt-1">
                    {project.description}
                  </CardDescription>
                )}
              </CardHeader>

              <CardContent className="pt-0 space-y-3">
                <div className="text-[11px] font-mono text-rf-text-muted flex items-center justify-between border-t border-rf-border/40 pt-2.5">
                  <span>Added {new Date(project.created_at).toLocaleDateString()}</span>
                  <span className="text-rf-crimson font-medium">Preflight Ready</span>
                </div>

                <div className="flex items-center justify-between gap-2 pt-1">
                  <Link
                    href={`/dashboard/websites/${project.id}`}
                    className="flex-1 h-7 rounded border border-rf-border bg-rf-surface hover:bg-rf-border/50 text-[11px] font-medium text-rf-text flex items-center justify-center gap-1 transition-colors"
                  >
                    <span>View Project</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>

                  {project.archived_at ? (
                    <button
                      onClick={() => handleRestore(project.id)}
                      className="p-1.5 rounded border border-rf-border hover:bg-rf-surface text-rf-text-muted hover:text-green-400 transition-colors"
                      title="Restore project"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleArchive(project.id)}
                      className="p-1.5 rounded border border-rf-border hover:bg-rf-surface text-rf-text-muted hover:text-amber-400 transition-colors"
                      title="Archive project"
                    >
                      <Archive className="w-3.5 h-3.5" />
                    </button>
                  )}

                  <button
                    onClick={() => handleDelete(project.id)}
                    className="p-1.5 rounded border border-rf-border hover:bg-rf-surface text-rf-text-muted hover:text-rf-crimson transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Website Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-rf-bg-secondary border border-rf-border rounded-lg shadow-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-rf-border pb-3">
              <h3 className="font-semibold text-sm text-rf-text">Add Website Project</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-rf-text-muted hover:text-rf-text"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddWebsite} className="space-y-4">
              {formError && (
                <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300 flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-rf-crimson flex-shrink-0 mt-0.5" />
                  <span>{formError}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="siteName">
                  Website Display Name
                </label>
                <input
                  id="siteName"
                  type="text"
                  value={siteName}
                  onChange={(e) => setSiteName(e.target.value)}
                  placeholder="e.g. Acme Online Store"
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-rf-text" htmlFor="domainOrUrl">
                    Target Domain or Canonical URL
                  </label>
                  <span className="text-[11px] text-rf-text-muted">Auto-normalized</span>
                </div>
                <input
                  id="domainOrUrl"
                  type="text"
                  value={domainOrUrl}
                  onChange={(e) => setDomainOrUrl(e.target.value)}
                  placeholder="e.g. acmestore.com or https://www.acme.com/shop"
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none font-mono"
                  required
                />
                <p className="text-[11px] text-rf-text-muted">
                  Input is safely normalized to its root host and canonical protocol. SSRF-vulnerable private addresses (127.0.0.1, 169.254.169.254) are rejected.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="siteDesc">
                  Description <span className="text-rf-text-muted font-normal">(optional)</span>
                </label>
                <textarea
                  id="siteDesc"
                  value={siteDescription}
                  onChange={(e) => setSiteDescription(e.target.value)}
                  placeholder="Primary e-commerce portal and blog..."
                  rows={2}
                  className="w-full p-2.5 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddModal(false)}
                  className="text-xs h-8"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-8"
                >
                  {isSubmitting ? "Validating & Adding..." : "Add Website"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
