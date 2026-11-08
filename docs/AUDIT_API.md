# Technical SEO Audit REST API Specification

All Phase 4 endpoints are scoped by organization workspace (`/api/v1/organizations/{org_id}/...`) and require valid Bearer token authentication.

---

## 1. Trigger SEO Audit Run

- **Endpoint:** `POST /api/v1/organizations/{org_id}/websites/{website_id}/audits`
- **Minimum Role:** `editor` (or `admin`, `owner`)
- **Verification Gate:** Website must have `is_verified == true`.
- **Query Parameters:** `execute_sync=true|false`
- **Request Body:**
```json
{
  "crawl_job_id": "optional-crawl-job-id-uuid",
  "execute_sync": false
}
```
- **Response (201 Created):**
```json
{
  "id": "audit-uuid",
  "organization_id": "org-uuid",
  "website_project_id": "site-uuid",
  "crawl_job_id": "crawl-uuid",
  "status": "completed",
  "ruleset_version": "v1.0.0",
  "scoring_version": "v1.0.0",
  "score": 85,
  "score_coverage": 1.0,
  "pages_evaluated": 25,
  "pages_not_evaluated": 0,
  "findings_count": 6,
  "critical_count": 0,
  "high_count": 2,
  "medium_count": 3,
  "low_count": 1,
  "info_count": 0,
  "summary_json": { ... },
  "created_at": "2026-11-08T21:00:00Z"
}
```

---

## 2. List Website Historical Audits

- **Endpoint:** `GET /api/v1/organizations/{org_id}/websites/{website_id}/audits`
- **Minimum Role:** `viewer`
- **Query Parameters:** `page=1`, `page_size=20`
- **Response (200 OK):**
```json
{
  "items": [ ... ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

## 3. Retrieve Single Audit Details

- **Endpoint:** `GET /api/v1/organizations/{org_id}/audits/{audit_id}`
- **Minimum Role:** `viewer`
- **Response (200 OK):** Full `SEOAuditRunRead` record.

---

## 4. List Audit Findings (with Rich Filtering)

- **Endpoint:** `GET /api/v1/organizations/{org_id}/audits/{audit_id}/findings`
- **Minimum Role:** `viewer`
- **Query Parameters:**
  - `category`: Filter by category (e.g. `metadata`, `headings`, `links_http`)
  - `severity`: Filter by severity (`critical`, `high`, `medium`, `low`, `informational`)
  - `rule_id`: Filter by rule ID (e.g. `META-001`)
  - `page_url`: Filter by exact page URL
  - `search`: Case-insensitive substring search in title, description, recommendation, or URL
  - `page`: Page index (default 1)
  - `page_size`: Findings per page (default 50, max 200)
- **Response (200 OK):**
```json
{
  "items": [
    {
      "id": "finding-uuid",
      "audit_run_id": "audit-uuid",
      "rule_id": "META-001",
      "rule_version": "v1.0.0",
      "page_url": "https://example.com/about",
      "severity": "critical",
      "category": "metadata",
      "title": "Missing Page Title Tag",
      "description": "Page at https://example.com/about is missing an HTML <title> tag in the document head.",
      "evidence_json": { "url": "https://example.com/about", "status_code": 200 },
      "recommendation": "Add a descriptive <title> tag inside the <head> element.",
      "finding_fingerprint": "8f3b...64hex",
      "created_at": "2026-11-08T21:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

## 5. Retrieve Category Scores Breakdown

- **Endpoint:** `GET /api/v1/organizations/{org_id}/audits/{audit_id}/scores`
- **Minimum Role:** `viewer`
- **Response (200 OK):** Array of 8 `SEOAuditCategoryScoreRead` records with weights, scores, and issue counts.

---

## 6. Differential Audit Comparison

- **Endpoint:** `GET /api/v1/organizations/{org_id}/audits/{audit_id}/compare/{previous_audit_id}`
- **Minimum Role:** `viewer`
- **Response (200 OK):**
```json
{
  "id": "comparison-uuid",
  "current_audit_id": "audit-2-uuid",
  "previous_audit_id": "audit-1-uuid",
  "score_change": 7,
  "new_findings_count": 1,
  "resolved_findings_count": 3,
  "persisting_findings_count": 2,
  "comparison_data_json": {
    "score_change": 7,
    "counts": { "new": 1, "resolved": 3, "persisting": 2 },
    "new_findings": [ ... ],
    "resolved_findings": [ ... ],
    "persisting_findings": [ ... ]
  }
}
```

---

## 7. Cancel Active Audit

- **Endpoint:** `POST /api/v1/organizations/{org_id}/audits/{audit_id}/cancel`
- **Minimum Role:** `editor`
- **Response (200 OK):** Updated `SEOAuditRun` record with status `"cancelled"`.

---

## 8. List Audited Pages Inventory

- **Endpoint:** `GET /api/v1/organizations/{org_id}/audits/{audit_id}/pages`
- **Minimum Role:** `viewer`
- **Response (200 OK):** Array of `AuditedPageRead` records showing status code, response latency, depth, canonical URL, heading counts, and total finding counts for each page.
