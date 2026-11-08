import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, setApiAuthToken } from "@/lib/api-client";

describe("Phase 4 SEO Technical Audit API Client Methods", () => {
  beforeEach(() => {
    setApiAuthToken("test-jwt-token");
    vi.restoreAllMocks();
  });

  it("should trigger an SEO technical audit run", async () => {
    const mockAudit = {
      id: "audit-101",
      organization_id: "org-1",
      website_project_id: "site-1",
      crawl_job_id: "crawl-1",
      status: "completed",
      score: 88,
      score_coverage: 1.0,
      pages_evaluated: 12,
      pages_not_evaluated: 0,
      findings_count: 3,
      critical_count: 0,
      high_count: 1,
      medium_count: 1,
      low_count: 1,
      info_count: 0,
      summary_json: {},
      created_at: "2026-11-08T21:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockAudit,
    });

    const res = await api.triggerSEOAudit("org-1", "site-1", { execute_sync: true });
    expect(res.id).toBe("audit-101");
    expect(res.score).toBe(88);
    expect(res.status).toBe("completed");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/websites/site-1/audits"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer test-jwt-token",
        }),
      })
    );
  });

  it("should list audit findings with category and severity filters", async () => {
    const mockFindings = {
      items: [
        {
          id: "find-1",
          audit_run_id: "audit-101",
          organization_id: "org-1",
          website_project_id: "site-1",
          rule_id: "META-001",
          rule_version: "v1.0.0",
          page_url: "https://example.com/missing-title",
          severity: "critical",
          category: "metadata",
          title: "Missing Page Title Tag",
          description: "Missing title",
          evidence_json: {},
          recommendation: "Add title tag",
          finding_fingerprint: "abc123hash",
          created_at: "2026-11-08T21:00:00Z",
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockFindings,
    });

    const res = await api.listSEOAuditFindings("org-1", "audit-101", {
      category: "metadata",
      severity: "critical",
    });

    expect(res.total).toBe(1);
    expect(res.items[0].rule_id).toBe("META-001");
    expect(res.items[0].severity).toBe("critical");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/audits/audit-101/findings?category=metadata&severity=critical"),
      expect.any(Object)
    );
  });

  it("should fetch 8 category scores breakdown", async () => {
    const mockScores = [
      {
        id: "score-1",
        audit_run_id: "audit-101",
        category: "indexability",
        score: 100,
        weight: 0.25,
        findings_count: 0,
        passed_checks_count: 10,
        details_json: {},
        created_at: "2026-11-08T21:00:00Z",
      },
      {
        id: "score-2",
        audit_run_id: "audit-101",
        category: "metadata",
        score: 75,
        weight: 0.15,
        findings_count: 2,
        passed_checks_count: 8,
        details_json: {},
        created_at: "2026-11-08T21:00:00Z",
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockScores,
    });

    const res = await api.getSEOAuditCategoryScores("org-1", "audit-101");
    expect(res.length).toBe(2);
    expect(res[0].category).toBe("indexability");
    expect(res[1].score).toBe(75);
  });

  it("should compare differential findings between two audit snapshots", async () => {
    const mockComparison = {
      id: "comp-1",
      organization_id: "org-1",
      website_project_id: "site-1",
      current_audit_id: "audit-2",
      previous_audit_id: "audit-1",
      score_change: 6,
      new_findings_count: 1,
      resolved_findings_count: 3,
      persisting_findings_count: 2,
      comparison_data_json: {
        score_change: 6,
        counts: { new: 1, resolved: 3, persisting: 2 },
      },
      created_at: "2026-11-08T21:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockComparison,
    });

    const res = await api.compareSEOAudits("org-1", "audit-2", "audit-1");
    expect(res.score_change).toBe(6);
    expect(res.resolved_findings_count).toBe(3);
    expect(res.new_findings_count).toBe(1);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/audits/audit-2/compare/audit-1"),
      expect.any(Object)
    );
  });
});
