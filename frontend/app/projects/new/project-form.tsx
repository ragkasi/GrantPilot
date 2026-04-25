"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FolderOpen, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { ApiError, createProject, listOrganizations } from "@/lib/api";
import type { Organization } from "@/types";
import { useDocumentTitle } from "@/lib/use-document-title";

export function ProjectForm() {
  useDocumentTitle("New Project");
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedOrgId = searchParams.get("org_id") ?? "";

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgsLoading, setOrgsLoading] = useState(true);
  const [selectedOrgId, setSelectedOrgId] = useState(preselectedOrgId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [createdGrantName, setCreatedGrantName] = useState("");

  useEffect(() => {
    listOrganizations()
      .then((data) => {
        setOrgs(data);
        if (!preselectedOrgId && data.length > 0) {
          setSelectedOrgId(data[0].id);
        }
      })
      .catch(() => setOrgs([]))
      .finally(() => setOrgsLoading(false));
  }, [preselectedOrgId]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedOrgId) {
      setError("Please select an organization.");
      return;
    }
    setError(null);
    setLoading(true);

    const fd = new FormData(e.currentTarget);
    try {
      const project = await createProject({
        organization_id: selectedOrgId,
        grant_name: fd.get("grant_name") as string,
        funder_name: (fd.get("funder_name") as string) || null,
        grant_amount: (fd.get("grant_amount") as string) || null,
        deadline: (fd.get("deadline") as string) || null,
        grant_source_url: (fd.get("grant_source_url") as string) || null,
      });
      setCreatedProjectId(project.id);
      setCreatedGrantName(project.grant_name);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (createdProjectId) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Project created</h2>
          <p className="text-sm text-gray-500 mb-6">
            <strong>{createdGrantName}</strong> is ready. Upload documents and run analysis from
            the project page.
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => { router.push(`/projects/${createdProjectId}`); router.refresh(); }}
              className="px-6 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Go to Project
            </button>
            <button
              onClick={() => { router.push("/dashboard"); router.refresh(); }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-7">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
            <FolderOpen className="w-4 h-4 text-violet-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900">New Grant Project</h1>
        </div>
        <p className="text-sm text-gray-500">
          Enter the grant details. You&apos;ll upload documents and run analysis from the project
          page.
        </p>
      </div>

      {!orgsLoading && orgs.length === 0 && (
        <div className="mb-5 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-700">
            <strong>No organizations found.</strong>{" "}
            <button
              className="underline hover:no-underline"
              onClick={() => router.push("/organizations/new")}
            >
              Create one first
            </button>{" "}
            before adding a project.
          </div>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100"
      >
        <div className="p-6 space-y-5">
          <h2 className="text-sm font-semibold text-gray-700">Grant Information</h2>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Organization <span className="text-red-500">*</span>
            </label>
            {orgsLoading ? (
              <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading organizations…
              </div>
            ) : (
              <select
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                {orgs.length === 0 ? (
                  <option value="">No organizations available</option>
                ) : (
                  orgs.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Grant Name <span className="text-red-500">*</span>
            </label>
            <input
              name="grant_name"
              type="text"
              required
              maxLength={300}
              placeholder="e.g. Community STEM Access Fund"
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Funder / Foundation Name
            </label>
            <input
              name="funder_name"
              type="text"
              placeholder="e.g. Ohio Community Foundation"
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Grant Amount Range
              </label>
              <input
                name="grant_amount"
                type="text"
                placeholder="e.g. $50,000 – $150,000"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Application Deadline
              </label>
              <input
                name="deadline"
                type="text"
                placeholder="e.g. May 15, 2026"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Grant Source URL
            </label>
            <input
              name="grant_source_url"
              type="url"
              placeholder="https://..."
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="px-6 py-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || orgs.length === 0}
            className="inline-flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Creating…
              </>
            ) : (
              "Create Project"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
