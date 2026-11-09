# RankForge AI — Production Environment Variables Catalog

This document defines all required and optional environment variables across each deployment target.

> [!CAUTION]
> **Secret Hygiene Rules:**
> 1. NEVER commit `.env`, `.env.production`, or real API credentials to Git.
> 2. Keep frontend variables strictly limited to public keys (`NEXT_PUBLIC_*`).
> 3. Database passwords, Redis credentials, and Google OAuth secrets must remain exclusively on the Railway backend and worker containers.

---

## 1. Vercel Frontend (`apps/web`)

Configure these in **Vercel Project Settings -> Environment Variables**:

| Variable Name | Required | Safe for Public Bundle? | Example / Value Description |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Yes** | Yes (Client runtime) | `https://api.rankforge.ai` or Railway public API domain |
| `NEXT_PUBLIC_SUPABASE_URL` | **Yes** | Yes (Client runtime) | `https://[your-project-ref].supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **Yes** | Yes (Client runtime) | Supabase `anon` / `public` JWT token |
| `NEXT_PUBLIC_SITE_URL` | **Yes** | Yes (Client runtime) | Canonical frontend domain, e.g., `https://rankforge.ai` |

---

## 2. Railway API Service (`rankforge-api`)

Configure these in **Railway Service Settings -> Variables** for the API container:

| Variable Name | Required | Default / Value | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | **Injected by Railway** | Dynamic | Railway dynamically allocates container port |
| `ENVIRONMENT` | **Yes** | `production` | Enables production security safeguards |
| `DEBUG` | **Yes** | `false` | Disables verbose debug responses and stack trace leaks |
| `SECRET_KEY` | **Yes** | *(Generate 64+ char random hex)* | Used for JWT hashing, OAuth state signatures, and Fernet encryption |
| `ALLOWED_ORIGINS` | **Yes** | `https://rankforge.ai,https://rankforge.vercel.app` | Comma-separated list of allowed CORS origins |
| `DATABASE_URL` | **Yes** | `postgresql+psycopg://...` | Supabase PostgreSQL connection string with `?sslmode=require` |
| `REDIS_URL` | **Yes** | `${{Redis.REDIS_URL}}` | Railway Redis connection URL |
| `CELERY_BROKER_URL` | No | *(Defaults to REDIS_URL)* | Celery broker URL |
| `CELERY_RESULT_BACKEND` | No | *(Defaults to REDIS_URL)* | Celery task result backend |
| `WEB_CONCURRENCY` | No | `2` | Uvicorn worker process count |
| `PUBLIC_API_URL` | **Yes** | `https://api.rankforge.ai` | Canonical public URL used for Google OAuth callback generation |
| `FRONTEND_URL` | **Yes** | `https://rankforge.ai` | Base URL used to redirect users after OAuth authorization |
| `SUPABASE_URL` | **Yes** | `https://[project-ref].supabase.co` | Supabase project URL |
| `SUPABASE_ANON_KEY` | **Yes** | `[anon-key]` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | `[service-role-key]` | Supabase service role key (backend only) |
| `SUPABASE_JWT_SECRET` | **Yes** | `[jwt-secret]` | Supabase JWT verification secret |
| `SUPABASE_JWT_AUDIENCE` | No | `authenticated` | Expected audience claim in JWT |
| `GEMINI_API_KEY` | **Yes** | `[gemini-api-key]` | Google AI Studio or Vertex API key for Gemini 2.5 Flash |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Selected Gemini model |
| `AI_PROVIDER` | No | `gemini` | `gemini` for live production, `mock` for dry run testing |
| `GOOGLE_CLIENT_ID` | **Yes** | `[google-oauth-client-id]` | Google Cloud Web Application Client ID |
| `GOOGLE_CLIENT_SECRET` | **Yes** | `[google-oauth-client-secret]` | Google Cloud Web Application Client Secret |
| `GOOGLE_REDIRECT_URI` | No | *(Auto-generated from PUBLIC_API_URL)* | Explicit callback URI override if needed |

---

## 3. Railway Worker Service (`rankforge-worker`)

Configure these in **Railway Service Settings -> Variables** for the background worker:

| Variable Name | Required | Default / Value | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `production` | Worker environment mode |
| `DATABASE_URL` | **Yes** | `postgresql+psycopg://...` | Supabase PostgreSQL connection string with `?sslmode=require` |
| `REDIS_URL` | **Yes** | `${{Redis.REDIS_URL}}` | Railway Redis connection URL |
| `CELERY_BROKER_URL` | No | *(Defaults to REDIS_URL)* | Celery broker URL |
| `CELERY_RESULT_BACKEND` | No | *(Defaults to REDIS_URL)* | Celery result backend |
| `CELERY_CONCURRENCY` | No | `2` | Number of concurrent task workers |
| `CELERY_LOG_LEVEL` | No | `INFO` | Worker log verbosity |
| `SECRET_KEY` | **Yes** | *(Same as API SECRET_KEY)* | Used for decrypting integration tokens |
| `GEMINI_API_KEY` | **Yes** | `[gemini-api-key]` | Required for asynchronous batch recommendation generation |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model |
| `AI_PROVIDER` | No | `gemini` | AI provider |

---

## 4. Railway Redis Service (`rankforge-redis`)

Managed automatically by Railway. Accessible via:
- `REDIS_URL`: Public or internal connection URL
- `REDISPRIVATEURL`: High-performance internal private network mesh URL (recommended for API & Worker)

---

## 5. Supabase Configuration Reference

In Supabase Project Settings:

| Parameter | Location in Supabase Dashboard | Target Usage |
| :--- | :--- | :--- |
| **Direct Database URL** | Settings -> Database -> Connection string (URI) | Direct PostgreSQL connection (`port 5432`) |
| **Transaction Pooler URL** | Settings -> Database -> Connection pooling -> Mode: Transaction | PgBouncer / Supavisor connection (`port 6543`) |
| **Session Pooler URL** | Settings -> Database -> Connection pooling -> Mode: Session | Session mode pooling (`port 5432`) |
| **Project URL** | Settings -> API -> Project URL | `NEXT_PUBLIC_SUPABASE_URL` & `SUPABASE_URL` |
| **Anon Public Key** | Settings -> API -> Project API keys (`anon` / `public`) | `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| **Service Role Secret** | Settings -> API -> Project API keys (`service_role` / `secret`) | `SUPABASE_SERVICE_ROLE_KEY` |
| **JWT Secret** | Settings -> API -> JWT Settings -> JWT Secret | `SUPABASE_JWT_SECRET` |

---

## 6. Google Cloud Console Credentials Reference

In Google Cloud Console -> APIs & Services -> Credentials:

| Parameter | Console Field | Target Usage |
| :--- | :--- | :--- |
| **Client ID** | OAuth 2.0 Client IDs -> Client ID | `GOOGLE_CLIENT_ID` (Railway API only) |
| **Client Secret** | OAuth 2.0 Client IDs -> Client Secret | `GOOGLE_CLIENT_SECRET` (Railway API only) |
| **Authorized Javascript Origins** | Web client -> Authorized JavaScript origins | Add Vercel domain & localhost |
| **Authorized Redirect URIs** | Web client -> Authorized redirect URIs | Add Railway API `/api/v1/integrations/google/callback` |
