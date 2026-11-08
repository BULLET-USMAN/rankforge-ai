import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, setApiAuthToken } from "@/lib/api-client";

describe("Phase 5 AI Recommendation Engine API Client Methods", () => {
  beforeEach(() => {
    setApiAuthToken("test-jwt-token");
    vi.restoreAllMocks();
  });

  it("should generate a single AI recommendation", async () => {
    const mockRec = {
      id: "rec-101",
      organization_id: "org-1",
      website_project_id: "site-1",
      page_url: "https://example.com/services",
      recommendation_type: "title_optimization",
      status: "needs_review",
      priority: "high",
      current_value: "Old Generic Title",
      suggested_value: "Enterprise SEO Intelligence | Example",
      explanation: "Aligns title with primary heading.",
      evidence_json: { supporting_evidence: ["Primary H1 observed"] },
      current_version_number: 1,
      created_at: "2026-11-08T22:00:00Z",
      updated_at: "2026-11-08T22:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockRec,
    });

    const res = await api.generateAIRecommendation("org-1", "site-1", {
      page_url: "https://example.com/services",
      recommendation_type: "title_optimization",
    });

    expect(res.id).toBe("rec-101");
    expect(res.status).toBe("needs_review");
    expect(res.suggested_value).toContain("Enterprise SEO Intelligence");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/websites/site-1/ai/generate"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer test-jwt-token",
        }),
      })
    );
  });

  it("should trigger bulk AI recommendation generation", async () => {
    const mockJob = {
      id: "job-555",
      organization_id: "org-1",
      website_project_id: "site-1",
      status: "queued",
      recommendation_types: ["title_optimization", "meta_description"],
      total_items: 0,
      completed_items: 0,
      failed_items: 0,
      created_at: "2026-11-08T22:00:00Z",
      updated_at: "2026-11-08T22:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => mockJob,
    });

    const res = await api.bulkGenerateAIRecommendations("org-1", "site-1", {
      recommendation_types: ["title_optimization", "meta_description"],
      page_limit: 10,
    });

    expect(res.id).toBe("job-555");
    expect(res.status).toBe("queued");
  });

  it("should list AI recommendations with filters", async () => {
    const mockList = {
      items: [
        {
          id: "rec-1",
          page_url: "https://example.com/p1",
          recommendation_type: "title_optimization",
          status: "needs_review",
          priority: "high",
          suggested_value: "Title 1",
          current_version_number: 1,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockList,
    });

    const res = await api.listAIRecommendations("org-1", "site-1", {
      status: "needs_review",
      priority: "high",
    });

    expect(res.total).toBe(1);
    expect(res.items[0].suggested_value).toBe("Title 1");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("status=needs_review&priority=high"),
      expect.anything()
    );
  });

  it("should handle review lifecycle: approve, edit, and history", async () => {
    // Approve
    const mockApproved = {
      id: "rec-1",
      status: "approved",
      approved_by: "user-1",
      approved_at: "2026-11-08T22:05:00Z",
      current_version_number: 1,
      suggested_value: "Approved Value",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApproved,
    });

    const approved = await api.approveAIRecommendation("org-1", "rec-1");
    expect(approved.status).toBe("approved");

    // Edit (creates v2)
    const mockEdited = {
      id: "rec-1",
      status: "needs_review",
      current_version_number: 2,
      suggested_value: "Edited Value",
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockEdited,
    });

    const edited = await api.editAIRecommendation("org-1", "rec-1", {
      suggested_value: "Edited Value",
    });
    expect(edited.current_version_number).toBe(2);
    expect(edited.status).toBe("needs_review");

    // History
    const mockHistory = [
      { id: "v2", version_number: 2, suggested_value: "Edited Value", created_at: "2026-11-08T22:06:00Z" },
      { id: "v1", version_number: 1, suggested_value: "Approved Value", created_at: "2026-11-08T22:00:00Z" },
    ];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockHistory,
    });

    const history = await api.getAIRecommendationHistory("org-1", "rec-1");
    expect(history.length).toBe(2);
    expect(history[0].version_number).toBe(2);
  });

  it("should fetch usage summary and quota details", async () => {
    const mockUsage = {
      daily_requests_used: 14,
      daily_requests_limit: 100,
      monthly_tokens_used: 28400,
      monthly_tokens_limit: 500000,
      monthly_estimated_cost_usd: 0.0078,
      quota_status: "normal",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUsage,
    });

    const usage = await api.getAIUsageSummary("org-1");
    expect(usage.daily_requests_used).toBe(14);
    expect(usage.quota_status).toBe("normal");
  });
});
