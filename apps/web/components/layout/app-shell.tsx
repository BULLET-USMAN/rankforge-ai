"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  ChevronDown,
  Building2,
  Activity,
  Check,
  Plus,
  LogOut,
  User,
  Shield,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { api, setApiAuthToken, type Organization, type Profile } from "@/lib/api-client";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

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
  { name: "Team & Access", href: "/dashboard/team", icon: Users2 },
  { name: "Keywords", href: "/dashboard/keywords", icon: KeyRound, tag: "P3" },
  { name: "Competitors", href: "/dashboard/competitors", icon: Shield, tag: "P3" },
  { name: "AI Optimization", href: "/dashboard/ai-optimization", icon: Sparkles, tag: "P3" },
  { name: "Reports", href: "/dashboard/reports", icon: FileBarChart2 },
  { name: "Billing", href: "/dashboard/billing", icon: CreditCard },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"checking" | "ready" | "offline">("checking");
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  // Dropdown states
  const [workspaceMenuOpen, setWorkspaceMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const workspaceRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (workspaceRef.current && !workspaceRef.current.contains(event.target as Node)) {
        setWorkspaceMenuOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    let isMounted = true;

    // Check backend health
    api
      .getLiveness()
      .then(() => {
        if (isMounted) setHealthStatus("ready");
      })
      .catch(() => {
        if (isMounted) setHealthStatus("offline");
      });

    // Fetch user profile
    api
      .getMe()
      .then((p) => {
        if (isMounted) setProfile(p);
      })
      .catch(() => {});

    // Fetch user's organizations
    api
      .listOrganizations()
      .then((orgs) => {
        if (isMounted && orgs && orgs.length > 0) {
          setOrganizations(orgs);
          // Retrieve stored org or default to first
          const savedOrgId = typeof window !== "undefined" ? localStorage.getItem("rf_active_org") : null;
          const found = orgs.find((o) => o.id === savedOrgId);
          setCurrentOrg(found || orgs[0]);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelectOrg = (org: Organization) => {
    setCurrentOrg(org);
    setWorkspaceMenuOpen(false);
    if (typeof window !== "undefined") {
      localStorage.setItem("rf_active_org", org.id);
    }
  };

  const handleSignOut = async () => {
    try {
      const supabase = getSupabaseBrowserClient();
      await supabase.auth.signOut();
    } catch {}
    setApiAuthToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("rf_active_org");
    }
    router.push("/login");
  };

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

          {/* Organization Workspace Switcher Dropdown */}
          <div className="relative" ref={workspaceRef}>
            <button
              type="button"
              onClick={() => setWorkspaceMenuOpen(!workspaceMenuOpen)}
              className="w-full p-2.5 rounded-md border border-rf-border bg-rf-surface/60 hover:bg-rf-surface flex items-center justify-between text-xs transition-colors"
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <Building2 className="w-3.5 h-3.5 text-rf-crimson flex-shrink-0" />
                <div className="truncate font-medium text-rf-text">
                  {currentOrg ? currentOrg.name : "Select Workspace"}
                </div>
              </div>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <Badge variant="outline" className="text-[10px] font-mono py-0 capitalize">
                  {currentOrg?.plan_tier || "Starter"}
                </Badge>
                <ChevronDown className="w-3 h-3 text-rf-text-muted" />
              </div>
            </button>

            {workspaceMenuOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-rf-bg-secondary border border-rf-border rounded-md shadow-xl py-1 z-50 text-xs">
                <div className="px-3 py-1.5 text-[10px] font-mono text-rf-text-muted border-b border-rf-border/40">
                  Switch Workspace
                </div>
                <div className="max-h-48 overflow-y-auto divide-y divide-rf-border/30">
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      type="button"
                      onClick={() => handleSelectOrg(org)}
                      className="w-full px-3 py-2 text-left hover:bg-rf-surface flex items-center justify-between transition-colors"
                    >
                      <span className="truncate text-rf-text">{org.name}</span>
                      {currentOrg?.id === org.id && <Check className="w-3.5 h-3.5 text-rf-crimson flex-shrink-0" />}
                    </button>
                  ))}
                </div>
                <div className="border-t border-rf-border/50 pt-1 mt-1">
                  <Link
                    href="/onboarding"
                    onClick={() => setWorkspaceMenuOpen(false)}
                    className="w-full px-3 py-2 text-left text-rf-crimson hover:bg-rf-surface flex items-center gap-1.5 transition-colors font-medium"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create New Workspace</span>
                  </Link>
                </div>
              </div>
            )}
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

        {/* Footer Info: Core API Status & Authenticated User */}
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

          {/* User Profile & Logout */}
          <div className="pt-1 flex items-center justify-between px-2">
            <Link
              href="/dashboard/profile"
              className="flex items-center gap-2 overflow-hidden hover:text-rf-text transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-rf-surface border border-rf-border flex items-center justify-center font-mono text-[10px] font-bold text-rf-text flex-shrink-0">
                {(profile?.display_name || profile?.full_name || profile?.email || "U")[0].toUpperCase()}
              </div>
              <div className="truncate text-[11px] font-medium text-rf-text">
                {profile?.display_name || profile?.full_name || "Account Profile"}
              </div>
            </Link>

            <button
              onClick={handleSignOut}
              className="p-1 rounded hover:bg-rf-surface text-rf-text-muted hover:text-rf-crimson transition-colors"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
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
              href="/dashboard/team"
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-rf-surface border border-rf-border text-rf-text hover:bg-rf-border/50 transition-colors"
            >
              Workspace Team
            </Link>
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
