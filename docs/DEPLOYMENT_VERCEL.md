# RankForge AI — Vercel Production Deployment Guide

## 1. Architecture & Monorepo Overview

RankForge AI's frontend is a Next.js 15 (React 19) web application located in `apps/web`. It operates within an npm workspaces monorepo that shares type definitions and core domain models from `packages/shared`.

When deploying to Vercel, the application compiles to static and server-rendered edge-compatible routes that communicate securely with:
- **Backend API:** FastAPI hosted on Railway (`NEXT_PUBLIC_API_URL`)
- **Authentication:** Supabase Auth (`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`)

---

## 2. Vercel Project Configuration Settings

When importing the GitHub repository into Vercel:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Next.js` | Automatically detected by Vercel |
| **Root Directory** | `apps/web` | **Crucial:** Must point to `apps/web` |
| **Include source files outside Root Directory** | `Enabled` (Checked) | Required to resolve `@rankforge/shared` from `packages/shared` |
| **Build Command** | `next build` (Default) | Automatically handled by Vercel |
| **Output Directory** | `.next` (Default) | Automatically handled |
| **Install Command** | `npm install` (Default) | Vercel respects the root `package-lock.json` workspace graph |
| **Node.js Version** | `20.x` or `22.x` | Verified on Node >= 20.0.0 |

---

## 3. Monorepo Shared Package Resolution

`apps/web` depends on `@rankforge/shared`:
1. `packages/shared/package.json` provides direct exports:
   ```json
   {
     "name": "@rankforge/shared",
     "main": "./src/index.ts",
     "types": "./src/index.ts",
     "exports": {
       ".": {
         "types": "./src/index.ts",
         "import": "./src/index.ts",
         "default": "./src/index.ts"
       }
     }
   }
   ```
2. `apps/web/next.config.ts` includes `transpilePackages: ["@rankforge/shared"]`.
3. `apps/web/tsconfig.json` contains path aliases mapping `@rankforge/shared` to `../../packages/shared/src/index.ts`.

---

## 4. Required Production Environment Variables

Add the following environment variables in the **Vercel Project Settings -> Environment Variables**:

| Variable Name | Required | Target Environment | Purpose / Example Value |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Yes** | Production, Preview | Public HTTPS URL of the Railway FastAPI backend (e.g., `https://api.rankforge.ai` or `https://rankforge-api-production.up.railway.app`). |
| `NEXT_PUBLIC_SUPABASE_URL` | **Yes** | Production, Preview | Supabase project URL (e.g., `https://abcdefghijklm.supabase.co`). |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **Yes** | Production, Preview | Supabase public/anonymous API key (JWT format). Safe for browser exposure. |
| `NEXT_PUBLIC_SITE_URL` | **Yes** | Production, Preview | Canonical domain of the frontend (e.g., `https://rankforge.ai` or `https://rankforge.vercel.app`). Used for OAuth redirects and canonical links. |

> [!CAUTION]
> **Zero Server Secrets in Frontend Bundles:**
> NEVER add `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `SECRET_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, or `REDIS_URL` to Vercel environment variables. All data mutations, token decryption, and AI prompting run strictly on the Railway backend.

---

## 5. Supabase Auth Redirects Configuration

In the **Supabase Dashboard -> Authentication -> URL Configuration**:
1. **Site URL:** Set to `https://rankforge.ai` (or your primary Vercel production domain).
2. **Redirect URLs:** Add the following wildcard and exact callback URLs:
   - `https://rankforge.ai/auth/callback`
   - `https://rankforge.vercel.app/auth/callback`
   - `https://*-bullet-usmans-projects.vercel.app/auth/callback` (for Vercel preview deployments)
   - `http://localhost:3000/auth/callback` (for local development)

### Reverse Proxy & Edge Host Resolution
`apps/web/app/auth/callback/route.ts` detects reverse-proxy headers automatically:
```ts
const forwardedHost = request.headers.get("x-forwarded-host");
const forwardedProto = request.headers.get("x-forwarded-proto") || "https";
const effectiveOrigin = process.env.NEXT_PUBLIC_SITE_URL
  ? process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, "")
  : (forwardedHost ? `${forwardedProto}://${forwardedHost}` : origin);
```
This guarantees that after Supabase email verification or OAuth callbacks, the user is redirected to the active domain without falling back to internal or localhost URLs.

---

## 6. Pre-Deployment Verification Checklist

Before pushing to production:
- [x] Run `npm run typecheck --workspace=apps/web` (0 TypeScript errors).
- [x] Run `npm run test --workspace=apps/web` (all Vitest unit tests pass).
- [x] Run `npm run build --workspace=apps/web` (all 23 static & dynamic routes compile).
- [x] Verify no hardcoded `http://localhost` references exist in client-side runtime logic.
- [x] Confirm crimson/grey UI design system styles render correctly across desktop and mobile.
