"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Building2, Globe, ArrowRight, ShieldCheck, Check } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api } from "@/lib/api-client";

export default function OnboardingPage() {
  const router = useRouter();
  const [orgName, setOrgName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [initialWebsite, setInitialWebsite] = useState("");
  const [planTier, setPlanTier] = useState<"starter" | "professional" | "agency">("starter");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNameChange = (val: string) => {
    setOrgName(val);
    if (!slugEdited) {
      const generated = val
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      setSlug(generated);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!orgName.trim()) {
      setError("Please provide a workspace name.");
      return;
    }
    if (!slug.trim()) {
      setError("Please provide a URL slug for your workspace.");
      return;
    }

    setIsLoading(true);

    try {
      const org = await api.createOrganization({
        name: orgName.trim(),
        slug: slug.trim().toLowerCase(),
        plan_tier: planTier,
      });

      // If initial website was provided, add it
      if (initialWebsite.trim()) {
        try {
          await api.createWebsite(org.id, {
            name: `${orgName.trim()} Main`,
            domain_or_url: initialWebsite.trim(),
          });
        } catch {
          // Website error is non-fatal for onboarding
        }
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create organization";
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-rf-bg flex flex-col justify-center items-center p-6 selection:bg-rf-crimson selection:text-white">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block">
            <Logo size={32} />
          </Link>
          <p className="text-xs text-rf-text-secondary">
            Set up your organization workspace to begin tracking and optimizing search performance
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rf-crimson/15 text-rf-crimson border border-rf-crimson/30">
                Step 1 of 1
              </span>
            </div>
            <CardTitle>Create Your Workspace</CardTitle>
            <CardDescription>
              Workspaces isolate your websites, technical audits, and team members.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 rounded bg-rf-crimson/10 border border-rf-crimson/30 text-xs text-red-300">
                  {error}
                </div>
              )}

              {/* Workspace Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-rf-text" htmlFor="orgName">
                  Workspace or Agency Name
                </label>
                <div className="relative">
                  <input
                    id="orgName"
                    type="text"
                    value={orgName}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Acme Digital Agency"
                    className="w-full h-9 pl-9 pr-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                    required
                  />
                  <Building2 className="w-4 h-4 text-rf-text-muted absolute left-3 top-2.5 pointer-events-none" />
                </div>
              </div>

              {/* Workspace Slug */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-rf-text" htmlFor="slug">
                    Workspace URL Slug
                  </label>
                  <span className="text-[11px] text-rf-text-muted">Unique identifier</span>
                </div>
                <div className="flex rounded-md border border-rf-border bg-rf-surface overflow-hidden focus-within:border-rf-crimson transition-colors">
                  <span className="px-3 py-2 bg-rf-bg-secondary border-r border-rf-border text-xs text-rf-text-muted font-mono select-none">
                    rankforge.ai/
                  </span>
                  <input
                    id="slug"
                    type="text"
                    value={slug}
                    onChange={(e) => {
                      setSlug(e.target.value);
                      setSlugEdited(true);
                    }}
                    placeholder="acme-digital"
                    className="flex-1 h-9 px-3 bg-transparent text-xs text-rf-text font-mono placeholder:text-rf-text-muted focus:outline-none"
                    required
                  />
                </div>
              </div>

              {/* Initial Website (Optional) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-rf-text" htmlFor="website">
                    Primary Website Domain <span className="text-rf-text-muted font-normal">(optional)</span>
                  </label>
                  <span className="text-[11px] text-rf-text-muted">Can add later</span>
                </div>
                <div className="relative">
                  <input
                    id="website"
                    type="text"
                    value={initialWebsite}
                    onChange={(e) => setInitialWebsite(e.target.value)}
                    placeholder="https://acmedigital.com"
                    className="w-full h-9 pl-9 pr-3 rounded-md border border-rf-border bg-rf-surface text-xs text-rf-text placeholder:text-rf-text-muted focus:border-rf-crimson focus:outline-none transition-colors"
                  />
                  <Globe className="w-4 h-4 text-rf-text-muted absolute left-3 top-2.5 pointer-events-none" />
                </div>
              </div>

              {/* Plan Selection */}
              <div className="space-y-2 pt-2">
                <label className="text-xs font-medium text-rf-text">Evaluation Tier</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "starter", name: "Starter", desc: "Up to 3 sites" },
                    { id: "professional", name: "Professional", desc: "Up to 10 sites" },
                    { id: "agency", name: "Agency", desc: "Unlimited sites" },
                  ].map((tier) => (
                    <button
                      key={tier.id}
                      type="button"
                      onClick={() => setPlanTier(tier.id as any)}
                      className={`p-2.5 rounded-md border text-left transition-all ${
                        planTier === tier.id
                          ? "border-rf-crimson bg-rf-crimson/10 text-rf-text"
                          : "border-rf-border bg-rf-surface/50 text-rf-text-secondary hover:border-rf-border/80"
                      }`}
                    >
                      <div className="flex items-center justify-between font-medium text-xs text-rf-text">
                        <span>{tier.name}</span>
                        {planTier === tier.id && <Check className="w-3 h-3 text-rf-crimson" />}
                      </div>
                      <div className="text-[10px] text-rf-text-muted mt-0.5">{tier.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-rf-crimson hover:bg-rf-crimson-hover text-white text-xs h-9 flex items-center justify-center gap-1.5"
                >
                  {isLoading ? (
                    <span>Initializing Workspace...</span>
                  ) : (
                    <>
                      <span>Launch Workspace Console</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
