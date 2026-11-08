# RankForge AI — Security Architecture & Hardening
**Document Version:** 3.0.0  
**Phase:** 3 (Domain Verification & Intelligent Website Crawler)  

---

## 1. Authentication Security & JWT Verification
The FastAPI backend strictly enforces cryptographic validation of all inbound authentication tokens.
- **Never Trust Client Claims**: Raw unverified JWT strings from headers or cookies are never accepted.
- **Signature Verification**:
  - HMAC-SHA256 (`HS256`) checked against `SUPABASE_JWT_SECRET`.
  - Asymmetric keys (`RS256`, `ES256`) validated against Supabase JWKS with cached key retrieval and rotation.
- **Claim Enforcement**: Validates standard claims:
  - `exp`: Reject expired signatures.
  - `aud`: Require `authenticated` audience.
  - `sub`: Require valid user UUID matching `profiles.id`.

---

## 2. Multi-Tenant Cross-Isolation Guarantees
1. **Endpoint-Level Workspace Verification (`RequireOrgRole`)**:
   Every tenant-scoped endpoint validates that the caller has an active row in `organization_members` for the specific `org_id` in the request path.
2. **Resource-Level Tenant Binding**:
   Database queries for website projects, crawl jobs, crawled pages, audit records, and invitations filter on both resource ID AND `organization_id`.
   Accessing another workspace's resource returns `HTTP 403 Forbidden` or `HTTP 404 Not Found`.
3. **No Workspace ID Guessing**:
   Users can only list workspaces they have joined. Workspace enumerations are completely segregated per authenticated profile.

---

## 3. Cryptographic Invitation Security
1. **Token Generation**: Invitations generate a 32-byte cryptographically secure URL-safe token via `secrets.token_urlsafe(32)`.
2. **Hash-Only Database Storage**: Only the `SHA-256` digest of the token is saved in `organization_invitations.token_hash`. Even if the database is leaked, raw invitation tokens cannot be extracted.
3. **Strict Expiry & Single-Use**:
   - Expire after 7 days (`INVITATION_EXPIRY_DAYS = 7`).
   - Acceptance records `accepted_at = utc_now()`. Re-acceptance is blocked.
   - Revocation records `revoked_at = utc_now()`. Revoked tokens are blocked.
4. **Email Recipient Verification**:
   The accepting user's email address must strictly match `invited_email`. An imposter or mismatched authenticated user cannot hijack the invitation.

---

## 4. Connection-Level SSRF Hardening (`SafeHttpFetcher`)
RankForge AI crawls external customer websites. To prevent Server-Side Request Forgery (SSRF) and DNS rebinding attacks:
- **Pre-Connection Resolution**: Hostnames are resolved to IP addresses prior to opening any socket connection.
- **Private Networks (RFC 1918)**: Rejects `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Loopback & Zero Addresses**: Rejects `127.0.0.0/8`, `localhost`, `0.0.0.0`, `::1`.
- **Cloud Metadata Protection**: Strictly blocks `169.254.169.254` and `metadata.google.internal` (AWS, GCP, Azure metadata services).
- **Link-Local & Multicast**: Blocks `169.254.0.0/16`, `fe80::/10`, and multicast addresses.
- **Per-Hop Redirect Validation**: Client auto-redirects are disabled. Every redirect `Location` header (up to 3 hops) is independently parsed, resolved, and validated against the SSRF policy before connecting.
- **Port Restrictions**: Permits only web ports (80, 443, 8080, 8443).
- **Embedded Credentials**: Rejects URLs containing userinfo (`user:pass@host`).

---

## 5. DoS & Payload Budget Protections
- **HTML Document Budget**: Limited to 2 MB per document. Excess bytes immediately abort the connection.
- **Sitemap Document Budget**: Limited to 5 MB per XML document.
- **Verification Token Budget**: Limited to 16 KB per check.
- **XML Entity Expansion / Billion Laughs Defense**: XML sitemaps are parsed exclusively with `defusedxml.ElementTree`, neutralizing DTD expansion and external entity injection.
- **Crawl Budget Cap**: Hard-capped at 100 pages per crawl job and maximum depth of 5.

---

## 6. Verification Prerequisite Gate
Crawl jobs and scheduled technical audits cannot be initiated against unverified domains. Attempting to start a crawl job on an unverified project returns `HTTP 403 Forbidden`.
Verification challenges expire in 7 days, and revocation immediately disables crawl execution.
