# RankForge AI — Quality Assurance & Testing Suite
**Document Version:** 2.0.0  
**Phase:** 2  

---

## 1. Quality Gates & Test Suites Overview

RankForge AI maintains strict quality gates across the backend API, frontend web client, and full-stack integration:

| Suite | Runner / Tool | Target | Test Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Unit & Integration** | Pytest | FastAPI + SQLAlchemy + Celery | 25 tests | **100% Passed** |
| **Backend Linting & Style** | Ruff | `apps/api` | 0 errors | **100% Passed** |
| **Frontend Unit & Component** | Vitest | Next.js components & lib utilities | 12 tests | **100% Passed** |
| **Frontend Static Typecheck** | TypeScript (`tsc --noEmit`) | Next.js 15 App Router | 0 errors | **100% Passed** |
| **End-to-End Smoke Tests** | Playwright | Full Next.js app on Chromium & Mobile | 24 tests | **100% Passed** |

---

## 2. Test Execution Commands

### Run Backend Pytest Suite
```powershell
.\.venv\Scripts\pytest.exe apps/api/tests
```

### Run Backend Ruff Linter
```powershell
.\.venv\Scripts\ruff.exe check apps/api
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
- `test_ssrf_guard.py`: Comprehensive SSRFGuard rejection of private IPs, loopback, link-local, cloud metadata, control characters.
- `test_audits.py`: Preflight technical audit execution, scoring calculation, SSRF rejection.
- `test_worker.py`: Celery worker task execution and status verification.
- `test_auth_security.py`: Unauthenticated 401 rejection, forged secret JWT rejection, profile retrieval, profile updates.
- `test_rbac.py`: 4-tier role hierarchy permissions, privilege escalation prevention, self-role modification blocking, final owner demotion protection.
- `test_cross_tenant_isolation.py`: Cross-tenant boundary enforcement between User A/Org A and User B/Org B across websites, members, and invitations.
- `test_invitations.py`: Token generation, SHA-256 token hashing, revocation, mismatched email rejection, single-use acceptance.
- `test_websites_lifecycle.py`: Domain normalization, SSRF rejection, duplicate domain rejection, pending verification status, search, archive, restore, and permanent deletion.

### Frontend Tests (`apps/web/tests/`)
- `auth-validation.test.ts`: Client-side domain validation, private IP detection, password complexity scoring.
- `api-client.test.ts`: Bearer token management, cookie persistence, ApiError handling.
- `logo.test.tsx`, `button.test.tsx`, `feature-gate.test.tsx`: Component visual styling and variant tests.

### Playwright E2E Tests (`tests/e2e/smoke.spec.ts`)
- 12 comprehensive scenarios tested across both **Desktop Chromium** and **Mobile Chrome (Pixel 5)**:
  1. Landing page branding and tagline
  2. Login page Supabase form and demo login
  3. Register page account creation and password strength
  4. Email verification page
  5. Password recovery and update pages
  6. Onboarding workspace setup and tier picker
  7. Dashboard Overview metrics and health probe
  8. Team & Workspace Access member roster and invitation modal
  9. Account Profile user details and verified email
  10. Website Projects list, search, and Add Website modal with SSRF guard
  11. Technical Audits preflight runner
  12. Settings and Billing roadmap pages
