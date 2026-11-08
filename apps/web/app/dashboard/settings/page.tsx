"use client";

import React, { useState, useEffect } from "react";
import { Settings, Building2, Users, Shield, Key, CheckCircle2, Lock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";

export default function SettingsPage() {
  const [org, setOrg] = useState<any | null>(null);
  const [orgName, setOrgName] = useState("");
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    api.listOrganizations().then((orgs) => {
      if (orgs && orgs.length > 0) {
        setOrg(orgs[0]);
        setOrgName(orgs[0].name);
      }
    }).catch(() => {});
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-rf-text tracking-tight">Organization Settings</h1>
        <p className="text-xs text-rf-text-secondary mt-1">
          Workspace identity, access roles, and technical crawler safety configurations.
        </p>
      </div>

      {/* Organization Profile */}
      <Card>
        <CardHeader className="py-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-rf-crimson" />
            <CardTitle>Workspace Profile</CardTitle>
          </div>
          <CardDescription>Primary organization metadata and tenant identifier</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text">Organization Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Acme Digital"
                  className="w-full h-9 px-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text focus:border-rf-crimson focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text">Tenant Slug</label>
                <input
                  type="text"
                  value={org?.slug || "acme-digital"}
                  disabled
                  className="w-full h-9 px-3 rounded-md border border-rf-border/40 bg-rf-bg text-xs font-mono text-rf-text-muted cursor-not-allowed"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-rf-text-secondary">
                Organization ID: <span className="font-mono text-[11px] text-rf-text-muted">{org?.id || "local-default"}</span>
              </span>
              <Button type="submit" size="sm">
                {isSaved ? "Saved Successfully" : "Save Changes"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Team Members List */}
      <Card>
        <CardHeader className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-rf-crimson" />
              <CardTitle>Team Members & Roles</CardTitle>
            </div>
            <Badge variant="outline" className="font-mono text-[10px]">
              RBAC Enabled
            </Badge>
          </div>
          <CardDescription>Role-based access permissions within this organization</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-rf-border/40 text-xs">
            <div className="p-4 flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="font-semibold text-rf-text flex items-center gap-2">
                  <span>Workspace Administrator</span>
                  <Badge variant="crimson" className="text-[10px] py-0">Owner</Badge>
                </div>
                <div className="text-[11px] font-mono text-rf-text-secondary">
                  admin@rankforge.ai
                </div>
              </div>
              <span className="text-[11px] text-green-400">Active</span>
            </div>

            <div className="p-4 flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="font-semibold text-rf-text flex items-center gap-2">
                  <span>SEO Technical Lead</span>
                  <Badge variant="secondary" className="text-[10px] py-0">Admin</Badge>
                </div>
                <div className="text-[11px] font-mono text-rf-text-secondary">
                  auditor@rankforge.ai
                </div>
              </div>
              <span className="text-[11px] text-rf-text-muted">Invited</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security & Crawler Engine Policy */}
      <Card>
        <CardHeader className="py-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-rf-crimson" />
            <CardTitle>Crawler Engine Security Policy</CardTitle>
          </div>
          <CardDescription>Immutable safeguards preventing network abuse and SSRF vulnerabilities</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-xs">
          <div className="p-3 rounded bg-rf-surface border border-rf-border/40 flex items-center justify-between">
            <div>
              <div className="font-semibold text-rf-text">SSRF Defense Layer</div>
              <div className="text-[11px] text-rf-text-secondary">
                Blocks RFC 1918 private subnets, loopbacks, and cloud metadata (169.254.169.254)
              </div>
            </div>
            <Badge variant="success">Strictly Enforced</Badge>
          </div>

          <div className="p-3 rounded bg-rf-surface border border-rf-border/40 flex items-center justify-between">
            <div>
              <div className="font-semibold text-rf-text">Crawler User-Agent Identification</div>
              <div className="text-[11px] font-mono text-rf-text-secondary">
                RankForgeAI-Auditor/1.0 (+https://rankforge.ai/bot)
              </div>
            </div>
            <Badge variant="secondary">Compliant</Badge>
          </div>

          <div className="p-3 rounded bg-rf-surface border border-rf-border/40 flex items-center justify-between">
            <div>
              <div className="font-semibold text-rf-text">Response Size Limit</div>
              <div className="text-[11px] text-rf-text-secondary">
                5MB payload ceiling per inspected URL
              </div>
            </div>
            <Badge variant="secondary">Active</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
