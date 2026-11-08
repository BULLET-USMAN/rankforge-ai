# RankForge AI — Multi-Tenant Workspace Architecture

## 1. Overview & Isolation Philosophy
RankForge AI is architected as an enterprise multi-tenant software system. Every core entity—including website projects, technical audits, crawl logs, and usage quotas—is strictly partitioned by organization workspace (`organization_id`).

Users do not access the platform globally; all authenticated operations are executed in the context of an active workspace.

## 2. Organization Entity Model
```sql
CREATE TABLE organizations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    plan_tier VARCHAR(50) DEFAULT 'starter' NOT NULL,
    created_by VARCHAR(36) REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### URL Slug Rules & Reserved Keywords
- Slugs are URL-safe lowercase strings conforming to `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Auto-generated from the workspace name during onboarding, with full user customization.
- **Reserved Slugs Blocklist**: Prevents routing collisions with system paths:
  `api`, `admin`, `app`, `auth`, `login`, `register`, `dashboard`, `settings`, `billing`, `docs`, `help`, `support`, `system`, `null`, `undefined`, `root`.

## 3. Workspace Membership & Switching
- Users can belong to multiple organizations (e.g., an SEO agency consultant working across multiple client workspaces).
- Memberships are stored in `organization_members` with composite uniqueness `(organization_id, user_id)`.
- **App Shell Switcher**:
  - Located at the top of the sidebar.
  - Displays currently selected workspace and subscription badge.
  - Dropdown lists all workspaces the user has access to.
  - Persists active workspace choice in client `localStorage` (`rf_active_org`).
  - Includes a quick action to launch `/onboarding` to provision a new workspace.

## 4. First-Time User Onboarding
When an account is first created or has no workspace memberships:
1. User is guided to `/onboarding`.
2. User provides agency/workspace name, reviews generated slug, and selects evaluation tier (`Starter`, `Professional`, `Agency`).
3. Optionally enters primary website domain.
4. Backend provisions the organization, grants the user `owner` role, and redirects to `/dashboard`.
