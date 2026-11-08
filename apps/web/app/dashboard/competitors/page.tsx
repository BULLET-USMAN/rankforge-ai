import React from "react";
import { FeatureGate } from "@/components/ui/feature-gate";

export default function CompetitorsPage() {
  return (
    <FeatureGate
      title="Public Competitor SEO Insights"
      badgeText="Phase 2 Release"
      state="coming_soon"
      targetPhase="Milestone P2-03"
      description="Comparative technical benchmarking and content gap evaluation against authorized or public industry competitors without fabricated data."
      architectureHighlights={[
        {
          title: "Public Core Web Vitals Benchmark",
          detail:
            "Evaluates public LCP, INP, and CLS performance curves against competing market leaders using real Chrome User Experience (CrUX) data.",
        },
        {
          title: "Content & Header Hierarchy Comparison",
          detail:
            "Side-by-side structural comparison of target page headings, word counts, schema implementations, and internal link ratios.",
        },
        {
          title: "Organic Keyword Gap Analysis",
          detail:
            "Discovers high-value queries where competitors index within top 5 positions but your verified properties remain unindexed or trailing.",
        },
        {
          title: "Indexation Velocity Tracking",
          detail:
            "Monitors the rate at which competitor domains publish, update, and re-index new subpaths and sitemaps over time.",
        },
      ]}
      roadmapDependencies={[
        "PostgreSQL 11 Tables Schema",
        "SSRF Protected Crawling Engine",
        "FastAPI Service Mesh",
        "Domain Token Verification",
      ]}
    />
  );
}
