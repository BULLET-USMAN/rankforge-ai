import { describe, it, expect } from "vitest";

describe("Domain and Credential Validation Rules", () => {
  it("rejects private IPs and loopback addresses", () => {
    const badTargets = ["127.0.0.1", "169.254.169.254", "localhost", "10.0.0.1", "192.168.1.1"];
    const isForbidden = (target: string) =>
      badTargets.some((bad) => target.includes(bad));

    expect(isForbidden("127.0.0.1")).toBe(true);
    expect(isForbidden("169.254.169.254")).toBe(true);
    expect(isForbidden("https://169.254.169.254/latest")).toBe(true);
    expect(isForbidden("https://example.com")).toBe(false);
    expect(isForbidden("growthforge.io")).toBe(false);
  });

  it("calculates password complexity accurately", () => {
    const checkStrength = (pw: string) => {
      const length = pw.length >= 8;
      const hasUpper = /[A-Z]/.test(pw);
      const hasLower = /[a-z]/.test(pw);
      const hasNumber = /[0-9]/.test(pw);
      const hasSpecial = /[^A-Za-z0-9]/.test(pw);
      return (
        (length ? 1 : 0) +
        (hasUpper && hasLower ? 1 : 0) +
        (hasNumber ? 1 : 0) +
        (hasSpecial ? 1 : 0)
      );
    };

    expect(checkStrength("weak")).toBe(0);
    expect(checkStrength("password123")).toBe(2);
    expect(checkStrength("Password123")).toBe(3);
    expect(checkStrength("P@ssw0rd!2026#Secure")).toBe(4);
  });
});
