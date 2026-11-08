import React from "react";
import { FeatureGate } from "@/components/ui/feature-gate";

export default function KeywordsPage() {
  return (
    <FeatureGate
      title="Keyword Intelligence & Search Analytics"
      badgeText="Phase 2 Release"
      state="coming_soon"
      targetPhase="Milestone P2-01"
      description="Direct Google Search Console synchronization, real search query analytics, CTR curve optimization, and automatic keyword cannibalization detection."
      architectureHighlights={[
        {
          title: "Google Search Console OAuth2 Ingestion",
          detail:
            "Automated background workers syncing verified domain query rankings, impressions, clicks, and average positions on a 24-hour cadence.",
        },
        {
          title: "Keyword Cannibalization Matrix",
          detail:
            "Identifies instances where multiple internal pages compete in search results for identical queries, causing rank degradation.",
        },
        {
          title: "SERP Feature Detection",
          detail:
            "Tracks snippet inclusions, people-also-ask rankings, video cards, and knowledge panel occurrences across tracked search intent terms.",
        },
        {
          title: "CTR Curve Anomaly Alerting",
          detail:
            "Calculates expected click-through rate vs actual CTR across SERP positions 1-10 to spot title/meta description underperformance.",
        },
      ]}
      roadmapDependencies={[
        "Multi-Tenant Isolation",
        "Celery Task Worker",
        "Website Domain Verification",
        "PostgreSQL Usage Events",
        "Deterministic Data Ingestion Schema",
      ]}
    />
  );
}
