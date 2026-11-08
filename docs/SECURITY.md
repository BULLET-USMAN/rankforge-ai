# RankForge AI — Security Architecture & Hardening
**Document Version:** 2.0.0  
**Phase:** 2  

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
   Database queries for website projects, audit records, and invitations filter on both resource ID AND `organization_id`.
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

## 4. Domain Normalization & SSRF Defense (`SSRFGuard` & `DomainNormalizer`)
RankForge AI analyzes external websites. To prevent Server-Side Request Forgery (SSRF), all user-submitted domains and URLs undergo strict validation before persistence:
- **Private Networks (RFC 1918)**: Rejects `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Loopback & Zero Addresses**: Rejects `127.0.0.1`, `localhost`, `0.0.0.0`, `::1`.
- **Cloud Metadata Protection**: Strictly blocks `169.254.169.254` (AWS, GCP, Azure metadata services).
- **Reserved / Internal TLDs**: Blocks `.local`, `.internal`, `.lan`, `.corp`, `.test`, `.invalid`, `.onion`.
- **Credential Stripping**: Rejects URLs with embedded credentials (`user:pass@host`).
- **Port Restrictions**: Permits only web ports (80, 443, 8080, 8443).
