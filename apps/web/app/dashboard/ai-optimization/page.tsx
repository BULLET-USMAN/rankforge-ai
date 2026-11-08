"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Globe, RotateCw, Sparkles } from "lucide-react";
import { api, type Organization, type WebsiteProject } from "@/lib/api-client";
import { AIOptimizationDashboard } from "@/components/ai/ai-optimization-dashboard";
import Link from "next/link";
import { Button } from "@/components/ui/button";

function AIOptimizationContent() {
  const searchParams = useSearchParams();
  const initialWebsiteId = searchParams.get("website_id") || searchParams.get("project_id");

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string>("");
  const [websites, setWebsites] = useState<WebsiteProject[]>([]);
  const [selectedWebsiteId, setSelectedWebsiteId] = useState<string>(initialWebsiteId || "");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadWorkspaces() {
      try {
        const orgs = await api.listOrganizations();
        setOrganizations(orgs || []);
        if (orgs && orgs.length > 0) {
          const orgId = orgs[0].id;
          setCurrentOrgId(orgId);

          const sites = await api.listWebsites(orgId);
          setWebsites(sites || []);

          if (sites && sites.length > 0) {
            const activeId =
              initialWebsiteId && sites.some((s) => s.id === initialWebsiteId)
                ? initialWebsiteId
                : sites[0].id;
            setSelectedWebsiteId(activeId);
          }
        }
      } catch (err) {
        console.error("Failed to load workspace websites:", err);
      } finally {
        setLoading(false);
      }
    }
    loadWorkspaces();
  }, [initialWebsiteId]);

  const selectedWebsite = websites.find((s) => s.id === selectedWebsiteId) || websites[0];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-muted-foreground gap-3">
        <RotateCw className="w-6 h-6 animate-spin text-purple-400" />
        <p className="text-sm">Connecting to SEO Optimization Engine...</p>
      </div>
    );
  }

  if (websites.length === 0) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center space-y-4 bg-[#121216] border border-white/10 rounded-xl mt-8">
        <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 mx-auto">
          <Globe className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">No Websites In Workspace</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Add and verify a website project to begin generating grounded AI SEO recommendations.
          </p>
        </div>
        <Link href="/dashboard/websites">
          <Button className="bg-purple-600 hover:bg-purple-700 text-white text-sm">
            Add Website Project
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Website Switcher Bar */}
      {websites.length > 1 && (
        <div className="flex items-center gap-3 p-3 bg-[#121216] border border-white/10 rounded-lg">
          <Globe className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground font-medium">Selected Website:</span>
          <select
            value={selectedWebsite?.id || ""}
            onChange={(e) => setSelectedWebsiteId(e.target.value)}
            className="bg-[#1c1c24] border border-white/10 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-purple-500"
          >
            {websites.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name} ({w.domain})
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedWebsite && (
        <AIOptimizationDashboard
          orgId={currentOrgId}
          websiteId={selectedWebsite.id}
          domain={selectedWebsite.domain}
          websites={websites}
          onSelectWebsite={(id) => setSelectedWebsiteId(id)}
        />
      )}
    </div>
  );
}

export default function AIOptimizationPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center p-16 text-muted-foreground gap-2">
          <RotateCw className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading AI Engine...</span>
        </div>
      }
    >
      <AIOptimizationContent />
    </Suspense>
  );
}
