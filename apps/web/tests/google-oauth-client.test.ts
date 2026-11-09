import { describe, it, expect, vi, beforeEach } from "vitest";
import { api } from "../lib/api-client";

describe("Google Search Console OAuth2 Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("requests Google OAuth authorization URL with correct parameters", async () => {
    const mockAuthResp = {
      authorization_url: "https://accounts.google.com/o/oauth2/v2/auth?client_id=xyz",
      state: "signed_state_token.signature",
      redirect_uri: "http://localhost:8000/api/v1/integrations/google/callback",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockAuthResp,
    } as Response);

    const result = await api.getGoogleOAuthAuthorizeUrl("org-123", "proj-456", "/dashboard/settings");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/integrations/google/authorize?organization_id=org-123&website_project_id=proj-456&return_url=%2Fdashboard%2Fsettings"),
      expect.any(Object)
    );
    expect(result.authorization_url).toBe(mockAuthResp.authorization_url);
    expect(result.state).toBe(mockAuthResp.state);
  });

  it("fetches Google Search Console connection status", async () => {
    const mockStatusResp = {
      is_connected: true,
      connected_email: "auditor@domain.com",
      scopes: ["https://www.googleapis.com/auth/webmasters.readonly"],
      is_active: true,
      organization_id: "org-123",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockStatusResp,
    } as Response);

    const status = await api.getGoogleOAuthStatus("org-123");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/integrations/google/status?organization_id=org-123"),
      expect.any(Object)
    );
    expect(status.is_connected).toBe(true);
    expect(status.connected_email).toBe("auditor@domain.com");
  });

  it("disconnects Google Search Console integration", async () => {
    const mockDisconnectResp = {
      success: true,
      message: "Google Search Console integration successfully disconnected.",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockDisconnectResp,
    } as Response);

    const res = await api.disconnectGoogleOAuth("org-123");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/integrations/google/disconnect?organization_id=org-123"),
      expect.objectContaining({ method: "POST" })
    );
    expect(res.success).toBe(true);
  });
});
