const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

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

  // Organizations
  listOrganizations: () =>
    request<Array<{ id: string; name: string; slug: string; plan_tier: string; created_at: string }>>(
      "/api/v1/organizations"
    ),
  createOrganization: (payload: { name: string; slug: string; plan_tier?: string }) =>
    request<{ id: string; name: string; slug: string; plan_tier: string; created_at: string }>(
      "/api/v1/organizations",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),

  // Projects
  listProjects: (organizationId?: string) => {
    const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : "";
    return request<
      Array<{
        id: string;
        organization_id: string;
        name: string;
        domain: string;
        primary_url: string;
        is_verified: boolean;
        verification_token: string;
        created_at: string;
      }>
    >(`/api/v1/projects${query}`);
  },
  createProject: (payload: { organization_id: string; name: string; domain: string; primary_url: string }) =>
    request<{
      id: string;
      organization_id: string;
      name: string;
      domain: string;
      primary_url: string;
      is_verified: boolean;
      verification_token: string;
      created_at: string;
    }>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getProject: (projectId: string) =>
    request<{
      id: string;
      organization_id: string;
      name: string;
      domain: string;
      primary_url: string;
      is_verified: boolean;
      verification_token: string;
      created_at: string;
    }>(`/api/v1/projects/${projectId}`),
  deleteProject: (projectId: string) =>
    request<null>(`/api/v1/projects/${projectId}`, {
      method: "DELETE",
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
    }>(`/api/v1/projects/${projectId}/verification?method=${method}`),

  // Audits
  triggerAudit: (payload: { project_id: string; target_url?: string; job_type?: string }) =>
    request<{
      id: string;
      project_id: string;
      organization_id: string;
      job_type: string;
      status: string;
      celery_task_id: string | null;
      started_at: string | null;
      completed_at: string | null;
      error_message: string | null;
      created_at: string;
      results: Array<{
        id: string;
        url: string;
        status_code: number;
        response_time_ms: number;
        headers_json: Record<string, string>;
        ssl_info_json: Record<string, unknown>;
        robots_txt_found: boolean;
        sitemap_found: boolean;
        issues_json: Array<{
          code: string;
          severity: "critical" | "warning" | "info";
          title: string;
          description: string;
        }>;
        score: number;
        created_at: string;
      }>;
    }>("/api/v1/audits", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAuditJob: (jobId: string) => request(`/api/v1/audits/jobs/${jobId}`),
  listProjectAudits: (projectId: string) => request<Array<any>>(`/api/v1/audits/projects/${projectId}`),

  // Worker Smoke
  triggerWorkerSmoke: (x: number = 21, y: number = 21) =>
    request<{ task_id: string; status: string; message: string; result?: unknown }>("/api/v1/worker/smoke-task", {
      method: "POST",
      body: JSON.stringify({ x, y }),
    }),
  getWorkerTaskStatus: (taskId: string) =>
    request<{ task_id: string; status: string; message: string; result?: unknown }>(
      `/api/v1/worker/task-status/${taskId}`
    ),
};
