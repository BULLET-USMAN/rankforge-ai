import { describe, it, expect, beforeEach } from "vitest";
import { setApiAuthToken, getApiAuthToken, ApiError } from "@/lib/api-client";

describe("API Client & Auth Token Utilities", () => {
  beforeEach(() => {
    setApiAuthToken(null);
  });

  it("should set and retrieve authentication token", () => {
    expect(getApiAuthToken()).toBeNull();
    setApiAuthToken("test-jwt-token-12345");
    expect(getApiAuthToken()).toBe("test-jwt-token-12345");
  });

  it("should clear token when set to null", () => {
    setApiAuthToken("temporary-token");
    expect(getApiAuthToken()).toBe("temporary-token");
    setApiAuthToken(null);
    expect(getApiAuthToken()).toBeNull();
  });

  it("should format ApiError with status and code", () => {
    const err = new ApiError(403, "FORBIDDEN", "Access denied", { role: "viewer" });
    expect(err.status).toBe(403);
    expect(err.code).toBe("FORBIDDEN");
    expect(err.message).toBe("Access denied");
    expect(err.name).toBe("ApiError");
  });
});
