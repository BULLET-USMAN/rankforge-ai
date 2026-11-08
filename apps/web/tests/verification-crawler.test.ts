import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, setApiAuthToken } from "@/lib/api-client";

describe("Domain Verification & Crawler API Client Methods", () => {
  beforeEach(() => {
    setApiAuthToken("test-auth-token");
    vi.restoreAllMocks();
  });

  it("should request verification status for a website", async () => {
    const mockData = {
      project_id: "site-1",
      domain: "example.com",
      method: "dns_txt",
      status: "pending",
      token: "mock-token-123",
      txt_record_name: "_rankforge-challenge.example.com",
      txt_record_value: "rankforge-verification=mock-token-123",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    });

    const res = await api.getVerificationStatus("org-1", "site-1", "dns_txt");
    expect(res.status).toBe("pending");
    expect(res.txt_record_name).toBe("_rankforge-challenge.example.com");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/websites/site-1/verification?method=dns_txt"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-auth-token",
        }),
      })
    );
  });

  it("should trigger live verification check", async () => {
    const mockCheckResult = {
      is_verified: true,
      status: "verified",
      message: "Domain verified via DNS TXT record",
      verified_at: "2026-11-08T20:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockCheckResult,
    });

    const res = await api.checkVerification("org-1", "site-1", "dns_txt");
    expect(res.is_verified).toBe(true);
    expect(res.status).toBe("verified");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/websites/site-1/verification/check?method=dns_txt"),
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("should dispatch crawl job with configuration", async () => {
    const mockJob = {
      id: "crawl-job-99",
      project_id: "site-1",
      organization_id: "org-1",
      status: "queued",
      pages_crawled: 0,
      pages_discovered: 1,
      max_pages: 75,
      max_depth: 3,
      created_at: "2026-11-08T20:00:00Z",
      updated_at: "2026-11-08T20:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockJob,
    });

    const res = await api.startCrawl("org-1", "site-1", { max_pages: 75, max_depth: 3 });
    expect(res.id).toBe("crawl-job-99");
    expect(res.max_pages).toBe(75);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/websites/site-1/crawls"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ max_pages: 75, max_depth: 3 }),
      })
    );
  });

  it("should list crawled pages with filters", async () => {
    const mockPagesList = {
      items: [
        {
          id: "page-1",
          job_id: "crawl-job-99",
          project_id: "site-1",
          url: "https://example.com/",
          normalized_url: "https://example.com/",
          status_code: 200,
          response_time_ms: 124.5,
          depth: 0,
          discovery_method: "seed",
          title: "Home",
          internal_links_count: 5,
          external_links_count: 2,
          created_at: "2026-11-08T20:00:00Z",
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockPagesList,
    });

    const res = await api.listCrawledPages("org-1", "crawl-job-99", {
      search: "Home",
      status_filter: "200",
      page: 1,
      page_size: 50,
    });

    expect(res.total).toBe(1);
    expect(res.items[0].url).toBe("https://example.com/");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/organizations/org-1/crawls/crawl-job-99/pages?search=Home&status_filter=200&page=1&page_size=50"),
      expect.any(Object)
    );
  });
});
