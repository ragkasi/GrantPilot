/**
 * Typed API client for the GrantPilot backend.
 * All functions throw ApiError on non-2xx responses.
 * Bearer token is attached automatically when present in localStorage.
 */

import type {
  AnalysisResult,
  Document,
  DocumentSummary,
  Organization,
  OrganizationCreate,
  Project,
  ProjectCreate,
  ProjectUpdate,
} from "@/types";
import { clearToken, getToken } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(email: string, password: string): Promise<string> {
  // Use raw fetch (not apiFetch) so a 401 "wrong credentials" response is surfaced
  // as a normal error rather than triggering the session-expired redirect.
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new ApiError(res.status, detail);
  }
  const data = await res.json();
  return data.access_token;
}

export async function register(email: string, password: string): Promise<string> {
  const data = await apiFetch<{ access_token: string; token_type: string }>(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  );
  return data.access_token;
}

export async function getMe(): Promise<{ id: string; email: string; created_at: string }> {
  return apiFetch("/auth/me");
}

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export async function listOrganizations(): Promise<Organization[]> {
  return apiFetch<Organization[]>("/organizations");
}

export async function createOrganization(data: OrganizationCreate): Promise<{ id: string; name: string; created_at: string }> {
  return apiFetch("/organizations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getOrganization(id: string): Promise<Organization> {
  return apiFetch<Organization>(`/organizations/${id}`);
}

export async function listOrgProjects(orgId: string): Promise<Project[]> {
  return apiFetch<Project[]>(`/organizations/${orgId}/projects`);
}

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------

export async function listProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects");
}

export async function createProject(data: ProjectCreate): Promise<{ id: string; organization_id: string; grant_name: string; status: string }> {
  return apiFetch("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getProject(id: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${id}`);
}

export async function updateProject(projectId: string, data: ProjectUpdate): Promise<Project> {
  return apiFetch<Project>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export async function listDocuments(projectId: string): Promise<Document[]> {
  return apiFetch<Document[]>(`/projects/${projectId}/documents`);
}

export async function deleteDocument(docId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/documents/${docId}`, {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired. Please log in again.");
  }
  if (!res.ok && res.status !== 204) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new ApiError(res.status, detail);
  }
}

/**
 * Uploads a document using multipart/form-data.
 * Does NOT set Content-Type — the browser sets it with the multipart boundary.
 */
export async function uploadDocument(
  projectId: string,
  organizationId: string,
  documentType: string,
  file: File,
): Promise<DocumentSummary> {
  const form = new FormData();
  form.append("organization_id", organizationId);
  form.append("project_id", projectId);
  form.append("document_type", documentType);
  form.append("file", file);

  const token = getToken();
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired. Please log in again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<DocumentSummary>;
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

export async function runAnalysis(
  projectId: string,
): Promise<{ project_id: string; status: string }> {
  return apiFetch(`/projects/${projectId}/analyze`, { method: "POST" });
}

export async function getAnalysis(projectId: string): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>(`/projects/${projectId}/analysis`);
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

export async function getReport(
  projectId: string,
): Promise<{ project_id: string; report_pdf_url: string | null }> {
  return apiFetch(`/projects/${projectId}/report`);
}

/**
 * Downloads the PDF report using an authenticated fetch request, then triggers
 * a browser download via a synthetic anchor click with a blob URL.
 *
 * This approach is used instead of window.open() because window.open() cannot
 * send the Authorization: Bearer header required by the protected endpoint.
 */
export async function downloadReport(projectId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}/projects/${projectId}/report/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired. Please log in again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new ApiError(res.status, detail);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `grant_readiness_report_${projectId.slice(0, 8)}.pdf`;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}
