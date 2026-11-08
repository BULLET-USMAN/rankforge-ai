import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { FeatureGate } from "@/components/ui/feature-gate";

describe("FeatureGate Component", () => {
  it("renders feature title, badge, and architectural highlights", () => {
    render(
      <FeatureGate
        title="Keyword Intelligence"
        badgeText="Phase 2 Release"
        state="coming_soon"
        targetPhase="Milestone P2"
        description="Search console integration."
        architectureHighlights={[
          { title: "Query Sync", detail: "Syncs Google Search Console data" },
        ]}
        roadmapDependencies={["PostgreSQL Multi-Tenant", "Celery Queue"]}
      />
    );

    expect(screen.getByText("Keyword Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Phase 2 Release")).toBeInTheDocument();
    expect(screen.getByText("Milestone P2")).toBeInTheDocument();
    expect(screen.getByText("Query Sync")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL Multi-Tenant")).toBeInTheDocument();
  });
});
