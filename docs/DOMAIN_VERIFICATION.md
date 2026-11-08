# Domain Ownership Verification Architecture

## 1. Overview
RankForge AI enforces mandatory domain ownership verification before any technical crawler operations, audit schedules, or automated SEO integrations can execute against a website project. Merely creating a project record does not authorize network scanning.

Verification establishes administrative control of the target domain by the organization workspace, preventing unauthorized crawling, resource exhaustion, and data leakage across tenants.

---

## 2. Supported Verification Mechanisms

### Method A: DNS TXT Record Challenge (Recommended)
- **Host / Name:** `_rankforge-challenge.<domain>` (with fallback lookup on root `<domain>`)
- **Record Type:** `TXT`
- **Expected Value:** `rankforge-verification=<token>`
- **Resolution Engine:** `dnspython` (`dns.resolver.Resolver`)
- **Timeout Budget:** 4.0s query timeout, 6.0s lifetime.
- **Propagation Awareness:** Returns detailed DNS status if records have not yet propagated across nameservers.

### Method B: HTML Verification File Challenge
- **Required Path:** `https://<domain>/.well-known/rankforge-verification.txt` (with fallback to `http://<domain>/.well-known/rankforge-verification.txt`)
- **Expected Content:** `rankforge-verification=<token>`
- **HTTP Status:** Must return HTTP 200 OK.
- **Fetch Engine:** `SafeHttpFetcher` (connection-bound SSRF protection, max 16 KB response budget).

---

## 3. Cryptographic Nonce & Lifecycle

```
[ Project Created ] 
       │ (status: pending, is_verified: false)
       ▼
[ Generate Challenge ] ──> Secrets.token_hex(16) [32 hex chars]
       │                  Expires in 7 days
       ▼
[ Verification Check ]
       ├── Match found ───> [ Verified ] (is_verified: true, verified_at: now)
       │                        │
       │                        └── Authorized for Crawler & Audits
       │
       └── Mismatch/Timeout > [ Failed / Expired ] (failure_reason persisted)
```

1. **Unpredictable Challenge Tokens:** Generated using Python's cryptographically strong `secrets.token_hex(16)`.
2. **7-Day Expiry:** Pending challenges expire after 7 days. Stale challenges cannot be validated and must be refreshed.
3. **Multi-Tenant Challenge Isolation:** If two organizations register identical domains, each organization workspace receives a unique, distinct cryptographic challenge token. Ownership cannot be claimed by Tenant B using Tenant A's token.
4. **Revocation Support:** Workspace Admins and Owners can revoke verification status at any time, immediately disabling crawler execution.

---

## 4. SSRF & Network Boundary Defense
During HTML verification file fetching:
1. URL syntax and schemes are restricted exclusively to `http` and `https`.
2. Ports are restricted to standard web ports (`80`, `443`, `8080`, `8443`).
3. Hostnames are resolved to IP addresses before initiating socket connections.
4. All resolved IPs are validated against `ipaddress.is_loopback`, `ipaddress.is_private`, `ipaddress.is_link_local`, `ipaddress.is_multicast`, and cloud metadata (`169.254.169.254`, `metadata.google.internal`).
5. Redirects are followed manually up to a maximum of 3 hops; every hop is resolved and re-validated against SSRF policies before the connection is established.
6. Payloads exceeding 16 KB are aborted to prevent memory exhaustion attacks.
