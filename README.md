# RankForge AI
> **Search intelligence. Engineered for growth.**

[![CI Quality Gate](https://github.com/BULLET-USMAN/rankforge-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/BULLET-USMAN/rankforge-ai/actions)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](#)
[![Phase: 1 Complete](https://img.shields.io/badge/Phase-1%20Foundation-emerald.svg)](#)

RankForge AI is a multi-tenant SEO intelligence and website optimization platform engineered for marketing teams, website operators, and agencies. It delivers automated technical audits, verified organic search diagnostics, and safe, approval-driven remediations with immutable rollback safeguards.

---

## Key Features in Phase 1

- **Enterprise Design System:** Minimal, dark-first editorial aesthetic with charcoal surfaces (`#111215`, `#191A1E`, `#202126`), restrained primary crimson accents (`#9F1733`), and tabular numerals.
- **FastAPI Backend:** Fully typed API with Pydantic v2, structured JSON logging, request tracing (`X-Request-ID`), size safeguards, and `/health/live` & `/health/ready` probes.
- **PostgreSQL 16 & Alembic:** Relational schema featuring 11 tables with foreign keys, indexes, and Row-Level Security (RLS) planning for multi-tenant isolation.
- **Celery Worker & Redis:** Asynchronous background task queue with automated retries and verified smoke task execution.
- **SSRF Defense Engine:** Strict IP and DNS inspection blocking RFC 1918 private subnets, loopbacks, and cloud metadata targets (`169.254.169.254`).
- **Deterministic Preflight Auditing:** Real HTTP status codes, true response latencies, SSL validation, robots.txt, and sitemap detection without fabricated metrics.
- **Domain Ownership Verification:** Protocols for DNS TXT records, HTML meta tags, and file uploads.
- **Next.js 15 App Router Frontend:** 12 production-grade routes with honest feature states and zero fake mockups.

---

## Monorepo Architecture

```
RANKFORGE/
├── apps/
│   ├── web/                     # Next.js 15 App Router frontend (TypeScript, Tailwind, Radix)
│   └── api/                     # FastAPI backend (Pydantic v2, SQLAlchemy 2.0, Alembic)
├── services/
│   └── worker/                  # Celery worker service (Redis broker & backend)
├── packages/
│   └── shared/                  # Shared TypeScript types, design tokens, and schemas
├── infrastructure/
│   └── docker/                  # Production Dockerfiles for API, Worker, and Web
├── docs/                        # Comprehensive technical documentation
│   ├── ARCHITECTURE.md          # System architecture and dataflow
│   ├── ROADMAP.md               # Phase 1, 2, and 3 capabilities and boundaries
│   ├── DATABASE.md              # 11-table relational schema and RLS policies
│   ├── SECURITY.md              # SSRF guard and ingress security controls
│   ├── DESIGN_SYSTEM.md         # Exact color palette tokens and styling rules
│   ├── TESTING.md               # Test pyramid and quality assurance runbook
│   └── PHASE_1_REPORT.md        # Verifiable Phase 1 completion report
├── tests/
│   └── e2e/                     # Playwright browser smoke tests
├── scripts/                     # Local developer run scripts
├── docker-compose.yml           # Full container orchestration
└── README.md                    # Platform overview and quickstart
```

---

## Quickstart & Local Development

### Prerequisites
- Node.js 20+ (Node 24 tested) and npm 10+
- Python 3.12+
- Docker & Docker Compose (optional for local containers)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/BULLET-USMAN/rankforge-ai.git
cd rankforge-ai
cp .env.example .env
```

### 2. Run Entire Stack with Docker Compose
```bash
docker compose up -d
```
- **Web Console:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Probe:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)

### 3. Local Native Development (Without Docker)

#### Backend Setup:
```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r apps/api/requirements-dev.txt
.\.venv\Scripts\uvicorn.exe app.main:app --app-dir apps/api --reload --port 8000
```

#### Frontend Setup:
```powershell
npm install
npm run dev --workspace=apps/web
```

---

## Running the Quality Assurance Suite

Every implemented feature is verified through automated tests:

```powershell
# 1. Run Python Backend Unit & Integration Tests (17 tests)
.\.venv\Scripts\pytest.exe apps/api/tests -v

# 2. Run Python Code Style & Ruff Linter
.\.venv\Scripts\ruff.exe check apps/api services/worker

# 3. Test Database Migrations (SQL Generation)
cd apps/api; ..\..\.venv\Scripts\alembic.exe upgrade head --sql; cd ../..

# 4. Run Frontend Component Tests (Vitest)
npm run test --workspace=apps/web

# 5. Run Strict TypeScript Type Check
npm run typecheck --workspace=apps/web

# 6. Verify Production Next.js Build
npm run build --workspace=apps/web

# 7. Run Playwright Browser Smoke Tests
npx playwright test
```

---

## License
Proprietary. All rights reserved.
