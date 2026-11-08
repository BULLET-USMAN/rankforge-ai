import React from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Lock, Clock, AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";

interface FeatureGateProps {
  title: string;
  badgeText: string;
  state: "coming_soon" | "not_configured" | "available" | "failed";
  targetPhase: string;
  description: string;
  architectureHighlights: Array<{
    title: string;
    detail: string;
  }>;
  roadmapDependencies: string[];
}

export function FeatureGate({
  title,
  badgeText,
  state,
  targetPhase,
  description,
  architectureHighlights,
  roadmapDependencies,
}: FeatureGateProps) {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header Banner */}
      <div className="p-6 rounded-lg border border-rf-border bg-rf-bg-secondary flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-semibold text-rf-text">{title}</h1>
            <Badge variant={state === "coming_soon" ? "crimson" : "secondary"}>
              {badgeText}
            </Badge>
            <Badge variant="outline" className="font-mono text-[11px]">
              {targetPhase}
            </Badge>
          </div>
          <p className="text-sm text-rf-text-secondary leading-relaxed max-w-2xl">
            {description}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/audits"
            className="text-xs text-rf-text-secondary hover:text-rf-text flex items-center gap-1 transition-colors"
          >
            Run Active Audit
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Architectural Blueprint Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-rf-text">
            <Clock className="w-4 h-4 text-rf-crimson" />
            <CardTitle>Architecture & Implementation Specification</CardTitle>
          </div>
          <CardDescription>
            Engineered capabilities designed for this module in the upcoming release cycle.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {architectureHighlights.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-md border border-rf-border/60 bg-rf-surface/50 space-y-1.5"
              >
                <div className="text-xs font-medium text-rf-text flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-rf-crimson flex-shrink-0" />
                  {item.title}
                </div>
                <div className="text-xs text-rf-text-secondary leading-relaxed pl-3.5">
                  {item.detail}
                </div>
              </div>
            ))}
          </div>

          {/* Dependencies checklist */}
          <div className="pt-3 border-t border-rf-border/40">
            <div className="text-xs font-semibold uppercase tracking-wider text-rf-text-muted mb-2.5">
              Prerequisite Foundations Completed in Phase 1
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {roadmapDependencies.map((dep, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs text-rf-text-secondary font-mono"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  <span>{dep}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
