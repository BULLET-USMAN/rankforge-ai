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
  verification_status: "pending" | "verified" | "failed";
  verification_token: string;
  created_by?: string | null;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
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

  // Website Projects (Phase 2 Workspace-scoped)
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
};
