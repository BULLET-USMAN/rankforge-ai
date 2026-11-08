"use client";

import React, { useState, useEffect } from "react";
import { FileBarChart2, Download, FileText, CheckCircle2, Clock, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default function ReportsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [isExporting, setIsExporting] = useState(false);
  const [lastExport, setLastExport] = useState<string | null>(null);

  useEffect(() => {
    api.listProjects().then((p) => setProjects(p || [])).catch(() => {});
  }, []);

  const handleExportJSON = () => {
    setIsExporting(true);
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(projects, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `rankforge_projects_export_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    setIsExporting(false);
    setLastExport(new Date().toISOString());
  };

  const handleExportCSV = () => {
    setIsExporting(true);
    const headers = ["ID", "Name", "Domain", "Primary URL", "Is Verified", "Created At"];
    const rows = projects.map((p) => [
      p.id,
      `"${p.name.replace(/"/g, '""')}"`,
      p.domain,
      p.primary_url,
      p.is_verified ? "Yes" : "No",
      p.created_at,
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", encodeURI(csvContent));
    downloadAnchor.setAttribute("download", `rankforge_projects_${Date.now()}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    setIsExporting(false);
    setLastExport(new Date().toISOString());
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-rf-text tracking-tight">Reports & Exports</h1>
        <p className="text-xs text-rf-text-secondary mt-1">
          Extract verified project configurations and technical diagnostic findings in standard formats.
        </p>
      </div>

      {/* Export Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-rf-crimson" />
              <CardTitle>Structured JSON Export</CardTitle>
            </div>
            <CardDescription>
              Export full workspace project metadata and verification keys as machine-readable JSON.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-xs text-rf-text-secondary">
              Contains: Project IDs, domain mappings, ownership verification states, and configuration timestamps.
            </div>
            <Button onClick={handleExportJSON} variant="secondary" size="sm" disabled={isExporting || projects.length === 0}>
              <Download className="w-3.5 h-3.5 mr-1.5" />
              Download Projects JSON ({projects.length})
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-rf-crimson" />
              <CardTitle>Tabular CSV Export</CardTitle>
            </div>
            <CardDescription>
              Export website projects and domain verification statuses for spreadsheet analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-xs text-rf-text-secondary">
              Compatible with Excel, Google Sheets, and agency reporting dashboards.
            </div>
            <Button onClick={handleExportCSV} variant="secondary" size="sm" disabled={isExporting || projects.length === 0}>
              <Download className="w-3.5 h-3.5 mr-1.5" />
              Download Projects CSV ({projects.length})
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* PDF Engine Status Specification */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-rf-text-muted" />
              <CardTitle>Automated PDF Audit Delivery</CardTitle>
            </div>
            <Badge variant="outline" className="font-mono text-[10px]">
              Phase 2 Pipeline
            </Badge>
          </div>
          <CardDescription>
            High-resolution client-ready PDF generation with scheduled weekly email dispatches.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-xs text-rf-text-secondary">
          <p leading-relaxed>
            In Phase 2, a headless Chromium worker task will render executive audit reports complete with
            historical comparison charts, Core Web Vitals graphs, and white-label agency branding.
          </p>
          {lastExport && (
            <div className="p-2.5 rounded bg-rf-surface border border-rf-border/40 font-mono text-[11px] text-rf-text">
              Last local export generated: {formatDate(lastExport)}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
