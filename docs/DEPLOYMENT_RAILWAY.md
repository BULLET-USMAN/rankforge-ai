# RankForge AI — Railway Deployment Guide (API, Worker & Redis)

## 1. Architectural Architecture on Railway

RankForge AI leverages Railway for three distinct services:
1. **API Service (`rankforge-api`):** FastAPI web server running under Uvicorn with multi-worker concurrency, behind Railway's HTTPS edge proxy.
2. **Worker Service (`rankforge-worker`):** Celery background daemon processing async crawler jobs, SEO audit pipelines, and Gemini AI optimization tasks.
3. **Redis Service (`rankforge-redis`):** Railway's managed Redis instance providing task queuing and cache storage.

---

## 2. API Service Configuration (`rankforge-api`)

### Dockerfile & Directory
- **Dockerfile Path:** `infrastructure/docker/Dockerfile.api`
- **Context Directory:** Repository root (`.`)

### Start Command & Port Binding
Railway dynamically assigns an HTTP routing port via the `$PORT` environment variable. The production Dockerfile CMD handles this automatically:
```bash
sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'"
```

### Key Start Command Options
- `--host 0.0.0.0`: Binds to all network interfaces within the container.
- `--port ${PORT:-8000}`: Uses Railway's allocated port dynamically.
- `--workers ${WEB_CONCURRENCY:-2}`: Spawns independent worker processes for production throughput.
- `--proxy-headers`: Instructs Uvicorn to parse `X-Forwarded-For` and `X-Forwarded-Proto`.
- `--forwarded-allow-ips='*'`: Trusts proxy headers sent by Railway's edge router.
- **NO `--reload`:** Debug reload is strictly disabled in production.

### Healthcheck Configuration
In Railway Service Settings -> **Healthcheck**:
- **Healthcheck Path:** `/health/live`
- **Healthcheck Timeout:** `30 seconds`
- **Alternative alias:** `/health` (also returns HTTP 200 `{"status":"alive"}`)

### Trusted Reverse Proxy Handling
In `apps/api/app/main.py`:
```python
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
```
This guarantees that `request.url` uses the `https://` scheme and client IPs are recorded accurately in security audit trails.

---

## 3. Worker Service Configuration (`rankforge-worker`)

### Dockerfile & Directory
- **Dockerfile Path:** `infrastructure/docker/Dockerfile.worker`
- **Context Directory:** Repository root (`.`)

### Process Execution & Public Networking
- **Public Networking / Domain:** **NONE** (Do NOT generate a public domain for the worker).
- **Start Command:**
  ```bash
  sh -c "celery -A celery_app.celery_app worker --loglevel=${CELERY_LOG_LEVEL:-INFO} --concurrency=${CELERY_CONCURRENCY:-2}"
  ```

### Reliability & Graceful Shutdown Settings
In `services/worker/celery_app.py`:
- `task_acks_late = True`: Tasks are acknowledged only after execution completes, preventing task loss on node restarts.
- `task_reject_on_worker_lost = True`: Tasks are rejected and requeued if a worker process is terminated.
- `worker_max_tasks_per_child = 50`: Prevents memory fragmentation by cycling child processes periodically.
- `worker_prefetch_multiplier = 1`: Enforces fair dispatch across concurrency workers.
- `task_time_limit = 300`: 5-minute hard timeout per task.
- `task_soft_time_limit = 240`: 4-minute soft timeout allowing clean resource cleanup.

---

## 4. Railway Redis Setup

1. In your Railway project, click **+ New** -> **Database** -> **Add Redis**.
2. Railway creates a managed Redis service and defines private environment variables.
3. In both `rankforge-api` and `rankforge-worker`, reference the private Redis connection:
   ```bash
   REDIS_URL=${{Redis.REDIS_URL}}
   ```
   *(Or `${{Redis.REDISPRIVATEURL}}` for internal mesh routing).*
4. The application and worker automatically handle `redis://` or `rediss://` (TLS) schemes.

---

## 5. Supabase PostgreSQL Connection

RankForge AI uses your existing Supabase PostgreSQL instance.

### Connection Method Selection
1. **Supabase Transaction Pooler (Recommended for Serverless / Cloud containers):**
   - Port: `6543` (Transaction mode) or `5432` (Session mode)
   - Connection URL:
     `postgresql+psycopg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require`
2. **Direct Connection:**
   - Port: `5432`
   - Connection URL:
     `postgresql+psycopg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres?sslmode=require`

### Automatic Dialect Normalization
If the raw URL copied from Supabase begins with `postgres://` or `postgresql://`, RankForge's `Settings` validator automatically normalizes it to `postgresql+psycopg://` to use the installed `psycopg` v3 driver.

### Connection Pool Configuration
In `apps/api/app/db/session.py`:
- `pool_pre_ping=True`: Detects stale connections and reconnects automatically.
- `pool_size=10`: Baseline connection pool.
- `max_overflow=20`: Burst connection buffer.
- `pool_recycle=300`: Recycles idle connections every 5 minutes to prevent dropped sockets by Supabase firewall.

---

## 6. Database Migrations Execution (`alembic upgrade head`)

Migrations should be run safely without automated destructive operations.

### Option A: Railway Deploy Command (Release Phase — Recommended)
In Railway Service Settings for `rankforge-api` -> **Deploy** -> **Pre-deploy Command**:
```bash
cd apps/api && alembic upgrade head
```
This runs migrations automatically whenever a new build is deployed. If the migration fails, Railway aborts the deployment before routing traffic.

### Option B: Railway CLI One-Off Execution
You can run migrations manually from your local terminal using the Railway CLI:
```bash
railway run --service rankforge-api "cd apps/api && alembic upgrade head"
```

### Option C: Container Entrypoint Script
Run migrations inside container startup before Uvicorn:
```bash
sh -c "cd apps/api && alembic upgrade head && cd /app && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --proxy-headers --forwarded-allow-ips='*'"
```

---

## 7. Structured & Secret-Safe Logging

In `apps/api/app/core/logging.py`:
- All log lines are formatted as single-line JSON objects with ISO timestamps, log level, request ID, status code, and latency.
- A regex sanitization pipeline masks sensitive credentials from message bodies:
  - `Bearer [token]` -> `Bearer [REDACTED]`
  - `password=...` / `token=...` / `secret=...` -> `[REDACTED]`
  - Database URLs `postgresql://user:pass@host` -> `postgresql://user:[REDACTED]@host`
  - Redis URLs `redis://user:pass@host` -> `redis://user:[REDACTED]@host`
