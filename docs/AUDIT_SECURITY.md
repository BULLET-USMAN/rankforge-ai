# Technical SEO Audit Security & Multi-Tenant Enforcement

## 1. Domain Ownership Verification Gate

Technical SEO audits may only be executed against websites whose ownership has been verified (`is_verified == true` with an active `WebsiteVerification` record):
- If an unverified website is targeted, the API returns `HTTP 403 Forbidden` with the error:
  `"Website ownership must be verified before running technical SEO audits."`
- This prevents unauthorized users from leveraging RankForge AI to inspect or probe third-party websites without confirmed authority.

---

## 2. Multi-Tenant Boundary Isolation

- **Scoped Queries:** All audit queries strictly include `organization_id == org_id` and `website_project_id == website_id`.
- **Role-Based Access Control (RBAC):**
  - Triggering or cancelling an audit requires at minimum the `editor` role in the target organization.
  - Viewing audits, findings, category scores, and comparisons requires at minimum the `viewer` role in the target organization.
- **Cross-Tenant Prevention:** Any request from a member of Organization B attempting to inspect Organization A's audits or findings is rejected with `HTTP 403 Forbidden` by the `RequireOrgRole` dependency before any business logic executes.
- **Comparison Tenant Check:** When comparing two audit snapshots (`current_audit_id` and `previous_audit_id`), `AuditComparisonService` validates that **both** audit snapshots belong to the same `organization_id` and `website_project_id`.

---

## 3. Crawler Separation & SSRF Protection

- The Audit Engine **never** performs outbound HTTP requests directly.
- It strictly consumes data already safely fetched and validated by the Phase 3 Safe Crawler (which enforces private IP blocks, cloud metadata exclusions, and RFC 9309 robots.txt compliance).
- Re-analyzing audits can never trigger SSRF or network egress attacks.
