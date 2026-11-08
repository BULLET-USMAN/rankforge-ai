import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Terminal,
  Search,
  CheckCircle2,
  Lock,
  GitBranch,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-rf-bg text-rf-text flex flex-col justify-between selection:bg-rf-crimson selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-rf-border/80 bg-rf-bg/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo size={26} />
          </Link>

          <nav className="hidden md:flex items-center gap-7 text-xs font-medium text-rf-text-secondary">
            <a href="#architecture" className="hover:text-rf-text transition-colors">
              Architecture
            </a>
            <a href="#capabilities" className="hover:text-rf-text transition-colors">
              Platform Capabilities
            </a>
            <a href="#security" className="hover:text-rf-text transition-colors">
              Security
            </a>
            <Link href="/dashboard" className="hover:text-rf-text transition-colors">
              Product Console
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm">
                Access Platform
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-16 px-6 max-w-5xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-rf-border bg-rf-bg-secondary text-xs text-rf-text-secondary">
          <span className="w-2 h-2 rounded-full bg-rf-crimson" />
          <span>RankForge AI Phase 1 Foundation</span>
          <span className="text-rf-text-muted">|</span>
          <span className="font-mono text-[11px] text-rf-text">v0.1.0 Ready</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-rf-text max-w-4xl mx-auto leading-[1.12]">
          Search intelligence.
          <br />
          <span className="text-rf-text-secondary font-normal">Engineered for growth.</span>
        </h1>

        <p className="text-base sm:text-lg text-rf-text-secondary max-w-2xl mx-auto leading-relaxed">
          RankForge AI is a multi-tenant SEO intelligence and website optimization platform
          delivering automated technical audits, verified organic search diagnostics, and safe,
          approval-driven remediations.
        </p>

        <div className="pt-3 flex flex-wrap items-center justify-center gap-3">
          <Link href="/dashboard">
            <Button size="lg" className="h-11 px-6">
              Launch Overview Dashboard
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <Link href="/dashboard/audits">
            <Button variant="secondary" size="lg" className="h-11 px-6">
              Run Preflight Audit
            </Button>
          </Link>
        </div>

        {/* Phase 1 Verification Status Banner */}
        <div className="pt-8 max-w-3xl mx-auto">
          <div className="p-4 rounded-lg border border-rf-border bg-rf-bg-secondary/60 text-left grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="space-y-1">
              <div className="text-rf-text-muted uppercase tracking-wider font-mono text-[10px]">
                Isolation Model
              </div>
              <div className="font-medium text-rf-text">Strict Multi-Tenant Boundaries</div>
              <div className="text-rf-text-secondary text-[11px]">
                RLS defense-in-depth architecture
              </div>
            </div>
            <div className="space-y-1 sm:border-l sm:border-rf-border/60 sm:pl-4">
              <div className="text-rf-text-muted uppercase tracking-wider font-mono text-[10px]">
                Execution Core
              </div>
              <div className="font-medium text-rf-text">FastAPI & Celery Workers</div>
              <div className="text-rf-text-secondary text-[11px]">
                Redis-backed background queues
              </div>
            </div>
            <div className="space-y-1 sm:border-l sm:border-rf-border/60 sm:pl-4">
              <div className="text-rf-text-muted uppercase tracking-wider font-mono text-[10px]">
                Integrity Principle
              </div>
              <div className="font-medium text-rf-text">Zero Fabricated Metrics</div>
              <div className="text-rf-text-secondary text-[11px]">
                Real HTTP status, SSL, and DNS diagnostics
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Pillars */}
      <section id="capabilities" className="py-16 border-t border-rf-border bg-rf-bg-secondary/30">
        <div className="max-w-6xl mx-auto px-6 space-y-10">
          <div className="max-w-xl space-y-2">
            <Badge variant="outline" className="font-mono text-[11px]">
              Engineered Capabilities
            </Badge>
            <h2 className="text-2xl font-bold text-rf-text">
              Four Core Pillars of SEO Intelligence
            </h2>
            <p className="text-sm text-rf-text-secondary leading-relaxed">
              Every system is built on maintainable abstractions without decorative mockups.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pillar 1 */}
            <div className="p-6 rounded-lg border border-rf-border bg-rf-surface/40 space-y-3">
              <div className="w-8 h-8 rounded-md bg-rf-bg border border-rf-border flex items-center justify-center text-rf-crimson">
                <Search className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-rf-text">
                1. Technical SEO Auditing
              </h3>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Objective crawl evaluation checking HTTP status codes, response latencies, SSL
                certificates, robots.txt directives, sitemap completeness, and canonical tags.
                Guarded against SSRF vulnerabilities.
              </p>
              <div className="pt-2 text-[11px] font-mono text-rf-text-muted">
                Status: Operational Preflight Engine (Phase 1)
              </div>
            </div>

            {/* Pillar 2 */}
            <div className="p-6 rounded-lg border border-rf-border bg-rf-surface/40 space-y-3">
              <div className="w-8 h-8 rounded-md bg-rf-bg border border-rf-border flex items-center justify-center text-rf-text-secondary">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-rf-text">
                2. Search Console & Keyword Intelligence
              </h3>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Direct integration with authorized Google Search Console properties to monitor true
                impressions, CTR curves, query positions, and keyword cannibalization without
                guessing.
              </p>
              <div className="pt-2 text-[11px] font-mono text-rf-text-muted">
                Status: Phase 2 Pipeline Specification Prepared
              </div>
            </div>

            {/* Pillar 3 */}
            <div className="p-6 rounded-lg border border-rf-border bg-rf-surface/40 space-y-3">
              <div className="w-8 h-8 rounded-md bg-rf-bg border border-rf-border flex items-center justify-center text-rf-text-secondary">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-rf-text">
                3. AI Optimization Engine
              </h3>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Synthesizes audit findings into prioritized remediation plans. Every recommendation
                includes concrete technical rationale, schema snippets, and risk ratings rather
                than generic filler.
              </p>
              <div className="pt-2 text-[11px] font-mono text-rf-text-muted">
                Status: Phase 2 LLM Dispatch Architecture Prepared
              </div>
            </div>

            {/* Pillar 4 */}
            <div className="p-6 rounded-lg border border-rf-border bg-rf-surface/40 space-y-3">
              <div className="w-8 h-8 rounded-md bg-rf-bg border border-rf-border flex items-center justify-center text-rf-text-secondary">
                <GitBranch className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-rf-text">
                4. Safe Approval & Automated Rollback
              </h3>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Authorized CMS integrations apply approved meta tags and redirects through
                immutable change tracking, enabling immediate single-click rollbacks should search
                metrics shift.
              </p>
              <div className="pt-2 text-[11px] font-mono text-rf-text-muted">
                Status: Phase 3 Automated Remediation Protocol
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture & Security Section */}
      <section id="architecture" className="py-16 border-t border-rf-border">
        <div className="max-w-6xl mx-auto px-6 space-y-8">
          <div className="max-w-xl space-y-2">
            <Badge variant="outline" className="font-mono text-[11px]">
              Security & Infrastructure
            </Badge>
            <h2 className="text-2xl font-bold text-rf-text">
              Built on Enterprise SaaS Principles
            </h2>
            <p className="text-sm text-rf-text-secondary leading-relaxed">
              Designed from day one to safeguard user data, enforce tenant boundaries, and prevent
              network abuse.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-lg border border-rf-border bg-rf-bg-secondary space-y-2">
              <div className="flex items-center gap-2 text-rf-text font-medium text-xs">
                <ShieldCheck className="w-4 h-4 text-rf-crimson" />
                SSRF Defense System
              </div>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Crawler engine resolves and rejects RFC 1918 private subnets, loopback addresses,
                and cloud metadata endpoints (169.254.169.254).
              </p>
            </div>

            <div className="p-5 rounded-lg border border-rf-border bg-rf-bg-secondary space-y-2">
              <div className="flex items-center gap-2 text-rf-text font-medium text-xs">
                <Lock className="w-4 h-4 text-rf-crimson" />
                Multi-Tenant Isolation
              </div>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Organizations strictly isolate projects, audit runs, recommendations, and usage
                quotas across relational boundaries and RLS policies.
              </p>
            </div>

            <div className="p-5 rounded-lg border border-rf-border bg-rf-bg-secondary space-y-2">
              <div className="flex items-center gap-2 text-rf-text font-medium text-xs">
                <Terminal className="w-4 h-4 text-rf-crimson" />
                Deterministic Testing
              </div>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Full test coverage across Pytest backend integration, Celery task verification,
                Vitest component tests, and Playwright smoke checks.
              </p>
            </div>

            <div className="p-5 rounded-lg border border-rf-border bg-rf-bg-secondary space-y-2">
              <div className="flex items-center gap-2 text-rf-text font-medium text-xs">
                <CheckCircle2 className="w-4 h-4 text-rf-crimson" />
                Truthful State Design
              </div>
              <p className="text-xs text-rf-text-secondary leading-relaxed">
                Explicit feature states prevent deceptive placeholders. If an integration is
                pending Phase 2, the UI honestly explains its status.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-rf-border bg-rf-bg-secondary py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-rf-text-secondary">
          <div className="flex items-center gap-3">
            <Logo size={20} compactText />
            <span className="text-rf-text-muted">|</span>
            <span>Search intelligence. Engineered for growth.</span>
          </div>
          <div className="flex items-center gap-4 text-rf-text-muted">
            <span>Phase 1 SaaS Foundation</span>
            <span>PostgreSQL &bull; FastAPI &bull; Next.js &bull; Celery</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
