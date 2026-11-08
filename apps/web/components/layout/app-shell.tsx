"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Globe,
  SearchCode,
  KeyRound,
  Users2,
  Sparkles,
  FileBarChart2,
  CreditCard,
  Settings,
  Menu,
  X,
  ExternalLink,
  ChevronDown,
  Building2,
  Activity,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api-client";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Websites", href: "/dashboard/websites", icon: Globe },
  { name: "Technical Audits", href: "/dashboard/audits", icon: SearchCode },
  { name: "Keywords", href: "/dashboard/keywords", icon: KeyRound, tag: "P2" },
  { name: "Competitors", href: "/dashboard/competitors", icon: Users2, tag: "P2" },
  { name: "AI Optimization", href: "/dashboard/ai-optimization", icon: Sparkles, tag: "P2" },
  { name: "Reports", href: "/dashboard/reports", icon: FileBarChart2 },
  { name: "Billing", href: "/dashboard/billing", icon: CreditCard },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"checking" | "ready" | "offline">("checking");
  const [organizations, setOrganizations] = useState<Array<{ id: string; name: string; slug: string }>>([]);
  const [currentOrg, setCurrentOrg] = useState<{ id: string; name: string; slug: string } | null>(null);

  useEffect(() => {
    // Check real backend health status
    let isMounted = true;
    api
      .getLiveness()
      .then(() => {
        if (isMounted) setHealthStatus("ready");
      })
      .catch(() => {
        if (isMounted) setHealthStatus("offline");
      });

    // Fetch organizations from API
    api
      .listOrganizations()
      .then((orgs) => {
        if (isMounted && orgs && orgs.length > 0) {
          setOrganizations(orgs);
          setCurrentOrg(orgs[0]);
        }
      })
      .catch(() => {
        // Handled silently
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-rf-bg text-rf-text flex flex-col md:flex-row">
      {/* Mobile Top Navigation Bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-rf-border bg-rf-bg-secondary sticky top-0 z-40">
        <Logo size={22} compactText />
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-1.5 rounded-md border border-rf-border text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
          aria-label="Toggle navigation"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Desktop Sidebar & Mobile Drawer */}
      <aside
        className={cn(
          "w-64 flex-shrink-0 bg-rf-bg-secondary border-r border-rf-border flex flex-col justify-between z-30 transition-all duration-150",
          "md:min-h-screen md:sticky md:top-0",
          mobileOpen ? "block fixed inset-0 top-[53px] bg-rf-bg-secondary" : "hidden md:flex"
        )}
      >
        <div className="p-4 space-y-4">
          {/* Logo */}
          <div className="px-2 py-1">
            <Link href="/" className="inline-block">
              <Logo size={24} />
            </Link>
          </div>

          {/* Organization Workspace Pill */}
          <div className="p-2.5 rounded-md border border-rf-border bg-rf-surface/60 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 overflow-hidden">
              <Building2 className="w-3.5 h-3.5 text-rf-crimson flex-shrink-0" />
              <div className="truncate font-medium text-rf-text">
                {currentOrg ? currentOrg.name : "Acme Digital"}
              </div>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono py-0">
              Starter
            </Badge>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors",
                    isActive
                      ? "bg-rf-crimson/15 text-rf-text border-l-2 border-rf-crimson"
                      : "text-rf-text-secondary hover:text-rf-text hover:bg-rf-surface"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4",
                        isActive ? "text-rf-crimson" : "text-rf-text-muted"
                      )}
                    />
                    <span>{item.name}</span>
                  </div>
                  {item.tag && (
                    <span className="text-[9px] font-mono px-1 py-0.2 rounded border border-rf-border text-rf-text-muted">
                      {item.tag}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer info: API Health & Developer Mode */}
        <div className="p-4 border-t border-rf-border/50 space-y-2.5 text-xs text-rf-text-secondary">
          {/* Health probe indicator */}
          <div className="flex items-center justify-between px-2 py-1.5 rounded bg-rf-surface/40 border border-rf-border/40 font-mono text-[11px]">
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-rf-text-muted" />
              <span>Core API</span>
            </div>
            <div className="flex items-center gap-1">
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  healthStatus === "ready"
                    ? "bg-green-500"
                    : healthStatus === "checking"
                    ? "bg-amber-500 animate-pulse"
                    : "bg-red-500"
                )}
              />
              <span className="capitalize">{healthStatus}</span>
            </div>
          </div>

          <div className="px-2 flex items-center justify-between text-[11px] text-rf-text-muted">
            <span>Phase 1 Foundation</span>
            <span>v0.1.0</span>
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-rf-border bg-rf-bg-secondary/40 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-2 text-xs text-rf-text-secondary">
            <span className="text-rf-text-muted">RankForge</span>
            <span>/</span>
            <span className="text-rf-text font-medium capitalize">
              {pathname === "/dashboard"
                ? "Overview"
                : pathname.replace("/dashboard/", "").replace("-", " ")}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard/websites"
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-rf-surface border border-rf-border text-rf-text hover:bg-rf-border/50 transition-colors"
            >
              Manage Sites
            </Link>
            <Link
              href="/dashboard/audits"
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-rf-crimson text-white hover:bg-rf-crimson-hover transition-colors"
            >
              Run Audit
            </Link>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
