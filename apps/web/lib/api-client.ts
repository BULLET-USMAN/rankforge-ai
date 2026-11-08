const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let clientAuthToken: string | null = null;

export function setApiAuthToken(token: string | null) {
  clientAuthToken = token;
  if (typeof document !== "undefined") {
    if (token) {
      document.cookie = `rf-auth-token=${token}; path=/; max-age=604800; SameSite=Lax`;
    } else {
      document.cookie = "rf-auth-token=; path=/; max-age=0";
    }
  }
}

export function getApiAuthToken(): string | null {
  if (clientAuthToken) return clientAuthToken;
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)rf-auth-token=([^;]*)/);
    if (match) return match[1];
    const sbMatch = document.cookie.match(/(?:^|;\s*)sb-access-token=([^;]*)/);
    if (sbMatch) return sbMatch[1];
  }
  return null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const token = getApiAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (res.status === 204) {
      return null as T;
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const err = data.error || {};
      throw new ApiError(
        res.status,
        err.code || "API_ERROR",
        err.message || data.detail || `Request failed with status ${res.status}`,
        err.details
      );
    }

    return data as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    const message = err instanceof Error ? err.message : "Network error";
    throw new ApiError(0, "NETWORK_ERROR", message);
  }
}

export interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  display_name: string | null;
  avatar_url: string | null;
  role: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  created_by?: string | null;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: "owner" | "admin" | "editor" | "viewer";
  email: string;
  full_name?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  created_at: string;
}

export interface OrganizationInvitation {
  id: string;
  organization_id: string;
  invited_email: string;
  invited_role: "admin" | "editor" | "viewer";
  invited_by: string;
  inviter_name?: string | null;
  expires_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
  created_at: string;
  manual_link?: string | null;
}

export interface WebsiteProject {
  id: string;
  organization_id: string;
  name: string;
  domain: string;
  primary_url: string;
  description?: string | null;
  is_verified: boolean;
  verification_status: "pending" | "verified" | "failed" | "revoked" | "expired";
  verification_token: string;
  created_by?: string | null;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface VerificationStatus {
  project_id: string;
  domain: string;
  method: string;
  status: "pending" | "verified" | "failed" | "revoked" | "expired";
  token?: string | null;
  txt_record_name?: string | null;
  txt_record_value?: string | null;
  file_path?: string | null;
  file_content?: string | null;
  last_checked_at?: string | null;
  failure_reason?: string | null;
  expires_at?: string | null;
  verified_at?: string | null;
}

export interface VerificationCheckResult {
  is_verified: boolean;
  status: string;
  message: string;
  failure_reason?: string | null;
  verified_at?: string | null;
}

export interface CrawlJob {
  id: string;
  project_id: string;
  organization_id: string;
  status: "queued" | "running" | "completed" | "partially_completed" | "failed" | "cancelled";
  celery_task_id?: string | null;
  pages_crawled: number;
  pages_discovered: number;
  pages_failed: number;
  pages_blocked: number;
  max_pages: number;
  max_depth: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CrawledPage {
  id: string;
  job_id: string;
  project_id: string;
  url: string;
  normalized_url: string;
  status_code: number;
  response_time_ms: number;
  content_type?: string | null;
  byte_size: number;
  depth: number;
  discovery_method: string;
  title?: string | null;
  meta_description?: string | null;
  canonical_url?: string | null;
  meta_robots?: string | null;
  h1_count: number;
  internal_links_count: number;
  external_links_count: number;
  content_hash?: string | null;
  error_details?: string | null;
  created_at: string;
}

export interface CrawledPageDetail extends CrawledPage {
  links_json: Array<{
    url: string;
    type: "internal" | "external";
    text?: string;
    rel?: string;
  }>;
}

export interface SEOAuditFinding {
  id: string;
  audit_run_id: string;
  organization_id: string;
  website_project_id: string;
  rule_id: string;
  rule_version: string;
  page_url?: string | null;
  severity: "critical" | "high" | "medium" | "low" | "informational";
  category: string;
  title: string;
  description: string;
  evidence_json: Record<string, any>;
  recommendation: string;
  finding_fingerprint: string;
  created_at: string;
}

export interface SEOAuditCategoryScore {
  id: string;
  audit_run_id: string;
  category: string;
  score: number;
  weight: number;
  findings_count: number;
  passed_checks_count: number;
  details_json: Record<string, any>;
  created_at: string;
}

export interface SEOAuditRun {
  id: string;
  organization_id: string;
  website_project_id: string;
  crawl_job_id: string;
  status:
    | "queued"
    | "running"
    | "completed"
    | "partially_completed"
    | "failed"
    | "cancelled"
    | "insufficient_coverage";
  ruleset_version: string;
  scoring_version: string;
  score?: number | null;
  score_coverage: number;
  pages_evaluated: number;
  pages_not_evaluated: number;
  findings_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  summary_json: Record<string, any>;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_by?: string | null;
  created_at: string;
  category_scores?: SEOAuditCategoryScore[];
}

export interface SEOAuditComparison {
  id: string;
  organization_id: string;
  website_project_id: string;
  current_audit_id: string;
  previous_audit_id: string;
  score_change: number;
  new_findings_count: number;
  resolved_findings_count: number;
  persisting_findings_count: number;
  comparison_data_json: Record<string, any>;
  created_at: string;
}

export interface AuditedPage {
  url: string;
  normalized_url: string;
  status_code: number;
  response_time_ms: number;
  depth: number;
  title?: string | null;
  canonical_url?: string | null;
  meta_robots?: string | null;
  h1_count: number;
  images_count: number;
  images_missing_alt_count: number;
  findings_count: number;
}

export const api = {
  // Health
  getLiveness: () => request<{ status: string; version: string; timestamp: string }>("/health/live"),
  getReadiness: () =>
    request<{
      status: string;
      environment: string;
      dependencies: Record<string, { status: string; latency_ms?: number; error?: string }>;
      timestamp: string;
    }>("/health/ready"),

  // User Profile
  getMe: () => request<Profile>("/api/v1/me"),
  updateMe: (payload: { display_name?: string; full_name?: string; avatar_url?: string }) =>
    request<Profile>("/api/v1/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Organizations / Workspaces
  listOrganizations: () => request<Organization[]>("/api/v1/organizations"),
  getOrganization: (orgId: string) => request<Organization>(`/api/v1/organizations/${orgId}`),
  createOrganization: (payload: { name: string; slug: string; plan_tier?: string }) =>
    request<Organization>("/api/v1/organizations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateOrganization: (orgId: string, payload: { name: string }) =>
    request<Organization>(`/api/v1/organizations/${orgId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Workspace Members
  listMembers: (orgId: string) =>
    request<OrganizationMember[]>(`/api/v1/organizations/${orgId}/members`),
  updateMemberRole: (orgId: string, memberId: string, role: string) =>
    request<OrganizationMember>(`/api/v1/organizations/${orgId}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),
  removeMember: (orgId: string, memberId: string) =>
    request<null>(`/api/v1/organizations/${orgId}/members/${memberId}`, {
      method: "DELETE",
    }),

  // Workspace Invitations
  listInvitations: (orgId: string) =>
    request<OrganizationInvitation[]>(`/api/v1/organizations/${orgId}/invitations`),
  createInvitation: (orgId: string, payload: { invited_email: string; invited_role: string }) =>
    request<OrganizationInvitation>(`/api/v1/organizations/${orgId}/invitations`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  revokeInvitation: (orgId: string, invitationId: string) =>
    request<null>(`/api/v1/organizations/${orgId}/invitations/${invitationId}`, {
      method: "DELETE",
    }),
  acceptInvitation: (payload: { token: string }) =>
    request<{
      message: string;
      organization_id: string;
      organization_name: string;
      role: string;
    }>("/api/v1/invitations/accept", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Website Projects (Workspace-scoped)
  listWebsites: (orgId: string, search?: string, includeArchived?: boolean) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (includeArchived) params.set("include_archived", "true");
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<WebsiteProject[]>(`/api/v1/organizations/${orgId}/websites${query}`);
  },
  getWebsite: (orgId: string, websiteId: string) =>
    request<WebsiteProject>(`/api/v1/organizations/${orgId}/websites/${websiteId}`),
  createWebsite: (
    orgId: string,
    payload: { name: string; domain_or_url: string; description?: string }
  ) =>
    request<WebsiteProject>(`/api/v1/organizations/${orgId}/websites`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateWebsite: (orgId: string, websiteId: string, payload: { name?: string; description?: string }) =>
    request<WebsiteProject>(`/api/v1/organizations/${orgId}/websites/${websiteId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  archiveWebsite: (orgId: string, websiteId: string) =>
    request<WebsiteProject>(`/api/v1/organizations/${orgId}/websites/${websiteId}/archive`, {
      method: "POST",
    }),
  restoreWebsite: (orgId: string, websiteId: string) =>
    request<WebsiteProject>(`/api/v1/organizations/${orgId}/websites/${websiteId}/restore`, {
      method: "POST",
    }),
  deleteWebsite: (orgId: string, websiteId: string) =>
    request<null>(`/api/v1/organizations/${orgId}/websites/${websiteId}`, {
      method: "DELETE",
    }),

  // Domain Verification (Phase 3)
  getVerificationStatus: (orgId: string, websiteId: string, method: string = "dns_txt") =>
    request<VerificationStatus>(
      `/api/v1/organizations/${orgId}/websites/${websiteId}/verification?method=${encodeURIComponent(method)}`
    ),
  initiateVerification: (orgId: string, websiteId: string, method: string = "dns_txt") =>
    request<VerificationStatus>(
      `/api/v1/organizations/${orgId}/websites/${websiteId}/verification/initiate`,
      {
        method: "POST",
        body: JSON.stringify({ method }),
      }
    ),
  checkVerification: (orgId: string, websiteId: string, method: string = "dns_txt") =>
    request<VerificationCheckResult>(
      `/api/v1/organizations/${orgId}/websites/${websiteId}/verification/check?method=${encodeURIComponent(method)}`,
      {
        method: "POST",
      }
    ),
  revokeVerification: (orgId: string, websiteId: string) =>
    request<VerificationCheckResult>(
      `/api/v1/organizations/${orgId}/websites/${websiteId}/verification/revoke`,
      {
        method: "POST",
      }
    ),

  // Website Crawler (Phase 3)
  startCrawl: (
    orgId: string,
    websiteId: string,
    payload: { max_pages?: number; max_depth?: number } = {}
  ) =>
    request<CrawlJob>(`/api/v1/organizations/${orgId}/websites/${websiteId}/crawls`, {
      method: "POST",
      body: JSON.stringify({
        max_pages: payload.max_pages ?? 50,
        max_depth: payload.max_depth ?? 3,
      }),
    }),
  listCrawls: (orgId: string, websiteId: string, skip: number = 0, limit: number = 20) =>
    request<{ items: CrawlJob[]; total: number }>(
      `/api/v1/organizations/${orgId}/websites/${websiteId}/crawls?skip=${skip}&limit=${limit}`
    ),
  getCrawlJob: (orgId: string, jobId: string) =>
    request<CrawlJob>(`/api/v1/organizations/${orgId}/crawls/${jobId}`),
  cancelCrawlJob: (orgId: string, jobId: string) =>
    request<CrawlJob>(`/api/v1/organizations/${orgId}/crawls/${jobId}/cancel`, {
      method: "POST",
    }),
  listCrawledPages: (
    orgId: string,
    jobId: string,
    params: { search?: string; status_filter?: string; page?: number; page_size?: number } = {}
  ) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.status_filter) query.set("status_filter", params.status_filter);
    if (params.page) query.set("page", params.page.toString());
    if (params.page_size) query.set("page_size", params.page_size.toString());
    const qs = query.toString();
    return request<{
      items: CrawledPage[];
      total: number;
      page: number;
      page_size: number;
    }>(`/api/v1/organizations/${orgId}/crawls/${jobId}/pages${qs ? `?${qs}` : ""}`);
  },
  getCrawledPageDetail: (orgId: string, jobId: string, pageId: string) =>
    request<CrawledPageDetail>(`/api/v1/organizations/${orgId}/crawls/${jobId}/pages/${pageId}`),

  // Phase 1 Legacy Compatibility
  listProjects: (organizationId?: string) => {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : "";
    return request<WebsiteProject[]>(`/api/v1/projects${query}`);
  },
  createProject: (payload: { organization_id: string; name: string; domain: string; primary_url: string }) =>
    request<WebsiteProject>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getVerificationInstructions: (projectId: string, method: string = "dns_txt") =>
    request<{
      project_id: string;
      domain: string;
      is_verified: boolean;
      method: string;
      token: string;
      dns_txt_record: string;
      meta_tag_snippet: string;
      file_upload_path: string;
      file_upload_content: string;
    }>(`/api/v1/projects/${projectId}/verification?method=${encodeURIComponent(method)}`),
  deleteProject: (projectId: string) =>
    request<null>(`/api/v1/projects/${projectId}`, {
      method: "DELETE",
    }),

  // Audits
  triggerAudit: (
    payloadOrProjectId: string | { project_id: string; target_url?: string; job_type?: string }
  ) => {
    const body =
      typeof payloadOrProjectId === "string"
        ? { project_id: payloadOrProjectId }
        : payloadOrProjectId;
    return request<{
      job_id: string;
      project_id: string;
      status: string;
      started_at: string;
      score: number;
      results?: any[];
    }>("/api/v1/audits", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  getAuditResult: (jobId: string) =>
    request<{
      id: string;
      job_id: string;
      project_id: string;
      url: string;
      score: number;
      response_time_ms: number;
      issues_count: number;
      issues: Array<{ id: string; category: string; severity: string; title: string; description: string }>;
      created_at: string;
    }>(`/api/v1/audits/${jobId}`),

  // Worker Smoke Task
  smokeTask: (x: number = 21, y: number = 21) =>
    request<{
      task_id: string;
      status: string;
      x: number;
      y: number;
      result: number;
      executed_at: string;
    }>("/api/v1/worker/smoke", {
      method: "POST",
      body: JSON.stringify({ x, y }),
    }),
  triggerWorkerSmoke: (x: number = 35, y: number = 65) =>
    request<{
      task_id: string;
      status: string;
      x: number;
      y: number;
      result: number;
      executed_at: string;
    }>("/api/v1/worker/smoke", {
      method: "POST",
      body: JSON.stringify({ x, y }),
    }),
  listProjectAudits: (projectId: string) =>
    request<any[]>(`/api/v1/audits?project_id=${encodeURIComponent(projectId)}`),

  // SEO Technical Audits (Phase 4)
  triggerSEOAudit: (
    orgId: string,
    websiteId: string,
    payload?: { crawl_job_id?: string; execute_sync?: boolean }
  ) =>
    request<SEOAuditRun>(`/api/v1/organizations/${orgId}/websites/${websiteId}/audits`, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    }),
  listWebsiteSEOAudits: (orgId: string, websiteId: string, page: number = 1, pageSize: number = 20) =>
    request<{
      items: SEOAuditRun[];
      total: number;
      page: number;
      page_size: number;
    }>(`/api/v1/organizations/${orgId}/websites/${websiteId}/audits?page=${page}&page_size=${pageSize}`),
  getSEOAuditRun: (orgId: string, auditId: string) =>
    request<SEOAuditRun>(`/api/v1/organizations/${orgId}/audits/${auditId}`),
  listSEOAuditFindings: (
    orgId: string,
    auditId: string,
    params: {
      category?: string;
      severity?: string;
      rule_id?: string;
      page_url?: string;
      search?: string;
      page?: number;
      page_size?: number;
    } = {}
  ) => {
    const query = new URLSearchParams();
    if (params.category) query.set("category", params.category);
    if (params.severity) query.set("severity", params.severity);
    if (params.rule_id) query.set("rule_id", params.rule_id);
    if (params.page_url) query.set("page_url", params.page_url);
    if (params.search) query.set("search", params.search);
    if (params.page) query.set("page", params.page.toString());
    if (params.page_size) query.set("page_size", params.page_size.toString());
    const qs = query.toString();
    return request<{
      items: SEOAuditFinding[];
      total: number;
      page: number;
      page_size: number;
    }>(`/api/v1/organizations/${orgId}/audits/${auditId}/findings${qs ? `?${qs}` : ""}`);
  },
  getSEOAuditCategoryScores: (orgId: string, auditId: string) =>
    request<SEOAuditCategoryScore[]>(`/api/v1/organizations/${orgId}/audits/${auditId}/scores`),
  compareSEOAudits: (orgId: string, auditId: string, previousAuditId: string) =>
    request<SEOAuditComparison>(`/api/v1/organizations/${orgId}/audits/${auditId}/compare/${previousAuditId}`),
  cancelSEOAudit: (orgId: string, auditId: string) =>
    request<SEOAuditRun>(`/api/v1/organizations/${orgId}/audits/${auditId}/cancel`, {
      method: "POST",
    }),
  listAuditedPages: (orgId: string, auditId: string) =>
    request<AuditedPage[]>(`/api/v1/organizations/${orgId}/audits/${auditId}/pages`),
};
