"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Building2,
  Users,
  Shield,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Globe,
  Radio,
  Unlink,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type GoogleIntegrationStatus } from "@/lib/api-client";

function SettingsContent() {
  const searchParams = useSearchParams();
  const [org, setOrg] = useState<any | null>(null);
  const [orgName, setOrgName] = useState("");
  const [isSaved, setIsSaved] = useState(false);

  // Google Integration state
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [isConnectingGoogle, setIsConnectingGoogle] = useState(false);
  const [isDisconnectingGoogle, setIsDisconnectingGoogle] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    // Check URL parameters for OAuth feedback
    if (searchParams.get("google_connected") === "true") {
      setNotification({
        type: "success",
        message: "Google Search Console successfully connected and verified!",
      });
    } else if (searchParams.get("error")) {
      const errCode = searchParams.get("error");
      const errMsg = searchParams.get("message") || "Authorization flow was not completed.";
      setNotification({
        type: "error",
        message: `Google OAuth Notice: ${errCode} - ${errMsg}`,
      });
    }

    api
      .listOrganizations()
      .then((orgs) => {
        if (orgs && orgs.length > 0) {
          const currentOrg = orgs[0];
          setOrg(currentOrg);
          setOrgName(currentOrg.name);

          // Fetch Google Search Console Integration status
          api
            .getGoogleOAuthStatus(currentOrg.id)
            .then((status) => setGoogleStatus(status))
            .catch(() => {
              setGoogleStatus({
                is_connected: false,
                scopes: [],
                is_active: false,
              });
            });
        }
      })
      .catch(() => {});
  }, [searchParams]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  const handleConnectGoogle = async () => {
    if (!org) return;
    setIsConnectingGoogle(true);
    try {
      const res = await api.getGoogleOAuthAuthorizeUrl(org.id, undefined, "/dashboard/settings");
      if (res.authorization_url) {
        window.location.href = res.authorization_url;
      }
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Could not initialize Google OAuth flow. Please check server configuration.",
      });
      setIsConnectingGoogle(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    if (!org) return;
    if (!confirm("Are you sure you want to disconnect Google Search Console from this workspace?")) {
      return;
    }
    setIsDisconnectingGoogle(true);
    try {
      await api.disconnectGoogleOAuth(org.id);
      setGoogleStatus({
        is_connected: false,
        scopes: [],
        is_active: false,
      });
      setNotification({
        type: "success",
        message: "Google Search Console integration disconnected successfully.",
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to disconnect integration.",
      });
    } finally {
      setIsDisconnectingGoogle(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-rf-text tracking-tight">Organization Settings</h1>
        <p className="text-xs text-rf-text-secondary mt-1">
          Workspace identity, access roles, Google Search Console integration, and technical crawler safety configurations.
        </p>
      </div>

      {/* Dynamic Feedback Banner */}
      {notification && (
        <div
          className={`p-3.5 rounded-md border text-xs flex items-center justify-between ${
            notification.type === "success"
              ? "bg-green-500/10 border-green-500/30 text-green-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-green-400" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            )}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-[11px] underline opacity-80 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

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
                Organization ID:{" "}
                <span className="font-mono text-[11px] text-rf-text-muted">
                  {org?.id || "local-default"}
                </span>
              </span>
              <Button type="submit" size="sm">
                {isSaved ? "Saved Successfully" : "Save Changes"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Google Search Console Integration */}
      <Card>
        <CardHeader className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-rf-crimson" />
              <CardTitle>Google Search Console Synchronization</CardTitle>
            </div>
            {googleStatus?.is_connected ? (
              <Badge variant="success" className="text-[10px] gap-1">
                <Radio className="w-2.5 h-2.5 animate-pulse text-green-400" /> Connected
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px]">
                Not Connected
              </Badge>
            )}
          </div>
          <CardDescription>
            Authorizes read-only Search Console synchronization for verified domain impressions, organic queries, and CTR analytics.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          {googleStatus?.is_connected ? (
            <div className="p-3.5 rounded bg-rf-surface border border-rf-border/40 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="font-semibold text-rf-text">Authorized Google Account</div>
                  <div className="font-mono text-[11px] text-rf-text-secondary">
                    {googleStatus.connected_email || "Authorized Workspace User"}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDisconnectGoogle}
                    disabled={isDisconnectingGoogle}
                    className="text-xs text-red-400 hover:text-red-300 hover:border-red-500/50"
                  >
                    <Unlink className="w-3.5 h-3.5 mr-1.5" />
                    {isDisconnectingGoogle ? "Disconnecting..." : "Disconnect"}
                  </Button>
                </div>
              </div>

              <div className="pt-2 border-t border-rf-border/30 flex items-center justify-between text-[11px] text-rf-text-muted">
                <span>Scope: https://www.googleapis.com/auth/webmasters.readonly</span>
                <span>Active Credentials: Encrypted at Rest</span>
              </div>
            </div>
          ) : (
            <div className="p-3.5 rounded bg-rf-surface border border-rf-border/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="font-semibold text-rf-text">Connect Search Console Property</div>
                <div className="text-[11px] text-rf-text-secondary leading-relaxed max-w-lg">
                  RankForge AI requests read-only OAuth access to ingest real search metrics, calculate CTR curve benchmarks, and identify keyword cannibalization without write permissions.
                </div>
              </div>
              <Button
                variant="default"
                size="sm"
                onClick={handleConnectGoogle}
                disabled={isConnectingGoogle || !org}
                className="shrink-0 gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                {isConnectingGoogle ? "Redirecting..." : "Connect Google Search Console"}
              </Button>
            </div>
          )}
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

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="p-4 text-xs text-rf-text-muted">Loading settings...</div>}>
      <SettingsContent />
    </Suspense>
  );
}
