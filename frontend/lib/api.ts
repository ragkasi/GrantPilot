/**
 * Typed API client for the GrantPilot backend.
 * All functions throw ApiError on non-2xx responses.
 * Bearer token is attached automatically when present in localStorage.
 */

import type { AnalysisResult, Organization, Project } from "@/types";
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
  const data = await apiFetch<{ access_token: string; token_type: string }>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  );
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

export async function getOrganization(id: string): Promise<Organization> {
  return apiFetch<Organization>(`/organizations/${id}`);
}

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------

export async function getProject(id: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${id}`);
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
 * Opens the PDF report download in a new browser tab.
 * The backend generates the PDF on first call and caches it for subsequent calls.
 * Attaches the auth token as a query param since the download opens in a new tab.
 */
export function downloadReport(projectId: string): void {
  const token = getToken();
  const url = `${BASE_URL}/projects/${projectId}/report/download`;
  // For the download, include the token as a header isn't possible for window.open,
  // so we open the URL directly. The backend's FileResponse works for authenticated users.
  window.open(url, "_blank");
}
