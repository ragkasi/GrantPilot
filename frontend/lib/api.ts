/**
 * Typed API client for the GrantPilot backend.
 * All functions throw ApiError on non-2xx responses.
 */

import type {
  AnalysisResult,
  Organization,
  Project,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse error — use statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
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
 */
export function downloadReport(projectId: string): void {
  window.open(`${BASE_URL}/projects/${projectId}/report/download`, "_blank");
}
