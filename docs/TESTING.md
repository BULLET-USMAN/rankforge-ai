# RankForge AI — Quality Assurance & Testing Suite
**Document Version:** 3.0.0  
**Phase:** 3 (Domain Verification & Intelligent Website Crawler)  

---

## 1. Quality Gates & Test Suites Overview

RankForge AI maintains strict quality gates across the backend API, crawler worker, frontend web client, and full-stack integration:

| Suite | Runner / Tool | Target | Test Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Unit & Integration** | Pytest | FastAPI + SQLAlchemy + Celery + Crawler | 42 tests | **100% Passed** |
| **Backend Linting & Style** | Ruff | `apps/api` & `services/worker` | 0 errors | **100% Passed** |
| **Frontend Unit & Component** | Vitest | Next.js components & lib utilities | 16 tests | **100% Passed** |
| **Frontend Static Typecheck** | TypeScript (`tsc --noEmit`) | Next.js 15 App Router | 0 errors | **100% Passed** |
| **End-to-End Smoke Tests** | Playwright | Full Next.js app on Chromium & Mobile | 26 tests | **100% Passed** |

---

## 2. Test Execution Commands

### Run Backend Pytest Suite
```powershell
.\.venv\Scripts\pytest.exe apps/api/tests
```

### Run Backend Ruff Linter
```powershell
.\.venv\Scripts\ruff.exe check apps/api services/worker
```

### Run Frontend Vitest Unit Tests
```powershell
npm.cmd run test --workspace=apps/web
```

### Run Frontend TypeScript Strict Typecheck
```powershell
npm.cmd run typecheck --workspace=apps/web
```

### Run Playwright E2E Master Smoke Suite
```powershell
npx.cmd playwright test
```

---

## 3. Test Coverage Breakdown

### Backend Tests (`apps/api/tests/`)
- `test_health.py`: Liveness, readiness, and dependency health checks.
- `test_organizations.py`: Organization creation, duplicate slug conflict rejection, listing.
- `test_projects.py`: Website project creation, verification instructions retrieval, deletion.
- `test_ssrf_guard.py`: Comprehensive SSRFGuard rejection of private IPs, loopback, link-local, cloud metadata.
- `test_audits.py`: Preflight technical audit execution, scoring calculation, SSRF rejection.
- `test_worker.py`: Celery worker task execution and status verification.
- `test_auth_security.py`: Unauthenticated 401 rejection, forged secret JWT rejection, profile retrieval, profile updates.
- `test_rbac.py`: 4-tier role hierarchy permissions, privilege escalation prevention, self-role modification blocking, final owner demotion protection.
- `test_cross_tenant_isolation.py`: Cross-tenant boundary enforcement, preventing unauthorized cross-workspace data access.
- `test_websites_lifecycle.py`: Workspace website CRUD, URL normalization, domain validation, soft-delete archiving, restoring, and deletion.
- `test_safe_fetcher.py` *(New in Phase 3)*: SSRF validation against loopback, private RFC 1918 networks, link-local, cloud metadata (`169.254.169.254`), prohibited schemes, non-web ports, and response size limits.
- `test_domain_verification.py` *(New in Phase 3)*: DNS TXT and HTML verification challenges, cryptographic nonce generation, 7-day expiration, DNS resolution mock, HTML file fetch validation, and verification revocation.
- `test_crawler_engine.py` *(New in Phase 3)*: URL normalization, trap detection, RFC 9309 robots.txt compliance, `defusedxml` sitemap parsing, HTML SEO metadata extraction, verification prerequisite gate (403 for unverified), synchronous crawl execution, and page inventory API.

### Frontend Tests (`apps/web/tests/`)
- `button.test.tsx`: Component styling variants, sizes, and event handlers.
- `logo.test.tsx`: Brand visual display, size props, and tagline rendering.
- `feature-gate.test.tsx`: Explicit feature state handling (available, coming-soon, locked).
- `auth-validation.test.ts`: Client-side email validation and password strength scoring.
- `api-client.test.ts`: Auth token cookie storage, clearing, and `ApiError` formatting.
- `verification-crawler.test.ts` *(New in Phase 3)*: Verification status fetching, live check execution, crawl job dispatch, and crawled pages filtering.

### Playwright E2E Suite (`tests/e2e/smoke.spec.ts`)
- 13 comprehensive end-to-end scenarios covering landing page, auth forms, password recovery, onboarding, dashboard metrics, team management, account profile, website projects, preflight audits, website verification and crawler detail page, and roadmap routes. Tested across Desktop Chromium and Mobile Chrome (26 total test runs).
