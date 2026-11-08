# RankForge AI — Quality Assurance & Testing Suite
**Document Version:** 5.0.0  
**Phase:** 5 (AI-Powered SEO Optimization & Recommendation Engine)

---

## 1. Quality Gates & Test Suites Overview

RankForge AI maintains zero-tolerance quality gates across all layers:

| Suite | Runner / Tool | Target | Test Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Unit & Integration** | Pytest | FastAPI + SQLAlchemy + Celery + Audit + AI Engine | 82 tests | **100% Passed** |
| **Backend Linting & Style** | Ruff | `apps/api` & `services/worker` | 0 errors | **100% Passed** |
| **Frontend Unit & Component** | Vitest | Next.js components & AI client | 25 tests | **100% Passed** |
| **Frontend Static Typecheck** | TypeScript (`tsc --noEmit`) | Next.js 15 App Router | 0 errors | **100% Passed** |
| **Production Build** | Next.js Build | Static prerendering & bundle validation | 23/23 routes | **100% Passed** |
| **End-to-End Smoke Tests** | Playwright | Full Next.js app on Chromium & Mobile | 28 tests | **100% Passed** |

---

## 2. Test Execution Commands

### Run Backend Pytest Suite
```powershell
.\.venv\Scripts\pytest.exe apps/api/tests
```

### Run Backend Ruff Linter
```powershell
.\.venv\Scripts\ruff.exe check apps/api services
```

### Run Frontend Vitest Unit Tests
```powershell
npm.cmd run test --workspace=apps/web
```

### Run Frontend TypeScript Strict Typecheck
```powershell
npm.cmd run typecheck --workspace=apps/web
```

### Run Next.js Production Build
```powershell
npm.cmd run build --workspace=apps/web
```

### Run Playwright E2E Master Smoke Suite
```powershell
npx.cmd playwright test
```

---

## 3. Phase 5 Specific Test Suites

1. **`tests/test_ai_provider.py`**:
   - Evaluates `MockAIProvider` generation for all 6 recommendation types.
   - Verifies structured JSON serialization and Pydantic validation.
   - Tests `GeminiProvider` configuration error handling when `GEMINI_API_KEY` is missing.
   - Tests `get_ai_provider()` runtime selection and test override.

2. **`tests/test_ai_security_and_injection.py`**:
   - Tests delimiter boundary isolation: text closing tags inside page content are escaped.
   - Tests oversized payload truncation.
   - Tests user guidance sanitization.
   - Tests output value HTML sanitization (stripping `<script>`, `<iframe>`, `onclick`, `javascript:`).

3. **`tests/test_ai_context_and_validation.py`**:
   - Rejection of empty suggestion outputs.
   - Internal linking validator removes/flags hallucinated destination URLs not in the crawl dataset.
   - Deterministic prioritization based on audit finding severity.

4. **`tests/test_ai_usage_and_quotas.py`**:
   - Estimated cost calculation using configurable per-million token rates.
   - Organization-level usage recording and real-time summary aggregation.
   - Concurrency-safe atomic quota reservations (`active` -> `committed` / `released`).
   - Daily request quota enforcement (raises `AIQuotaExhaustedError`).

5. **`tests/test_ai_review_workflow.py`**:
   - Proposal approval records user ID and timestamp without touching customer website.
   - Manual editing increments version number, updates suggested value, and resets approved status to `needs_review`.
   - Immutable version history timeline.
   - Proposal rejection with reason.
   - Proposal saving as draft.

6. **`tests/test_ai_api_endpoints.py`**:
   - End-to-end REST API integration testing.
   - Asynchronous bulk optimization job queueing and cancellation.
   - Strict cross-tenant isolation: User B from Org B cannot read, edit, or approve Org A's recommendations (HTTP 403 / 404).
   - Usage and quota query endpoints.

7. **`apps/web/tests/ai-client.test.ts`**:
   - Tests frontend API client methods, JWT bearer token attachment, error wrapping, and state transitions.
