"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, CheckCircle2, Loader2 } from "lucide-react";
import { ApiError, createOrganization } from "@/lib/api";

export default function NewOrganizationPage() {
  const router = useRouter();
  const [createdOrgId, setCreatedOrgId] = useState<string | null>(null);
  const [createdOrgName, setCreatedOrgName] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const fd = new FormData(e.currentTarget);
    const budget = parseFloat((fd.get("annual_budget") as string).replace(/[^0-9.]/g, "")) || 0;

    try {
      const org = await createOrganization({
        name: fd.get("name") as string,
        mission: fd.get("mission") as string,
        location: fd.get("location") as string,
        nonprofit_type: fd.get("nonprofit_type") as string,
        annual_budget: budget,
        population_served: (fd.get("population_served") as string) || "",
      });
      setCreatedOrgId(org.id);
      setCreatedOrgName(org.name);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (createdOrgId) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Organization created</h2>
          <p className="text-sm text-gray-500 mb-6">
            {createdOrgName} has been added to your account.
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => router.push(`/projects/new?org_id=${createdOrgId}`)}
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Create a Grant Project
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="px-5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Go to Dashboard
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
          <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
            <Building2 className="w-4 h-4 text-indigo-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900">New Organization</h1>
        </div>
        <p className="text-sm text-gray-500">
          Add your nonprofit organization. Documents you upload later will be linked here.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
        <div className="p-6 space-y-5">
          <h2 className="text-sm font-semibold text-gray-700">Organization Details</h2>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Organization Name <span className="text-red-500">*</span>
            </label>
            <input
              name="name"
              type="text"
              required
              maxLength={200}
              placeholder="e.g. BrightPath Youth Foundation"
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Mission Statement <span className="text-red-500">*</span>
            </label>
            <textarea
              name="mission"
              required
              rows={3}
              placeholder="e.g. Provide after-school STEM mentoring to low-income youth."
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Location <span className="text-red-500">*</span>
              </label>
              <input
                name="location"
                type="text"
                required
                placeholder="e.g. Columbus, Ohio"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Nonprofit Type <span className="text-red-500">*</span>
              </label>
              <select
                name="nonprofit_type"
                defaultValue="501(c)(3)"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
              >
                <option>501(c)(3)</option>
                <option>501(c)(4)</option>
                <option>501(c)(6)</option>
                <option>Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Annual Operating Budget
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                <input
                  name="annual_budget"
                  type="text"
                  placeholder="e.g. 420,000"
                  className="w-full pl-7 pr-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Population Served
              </label>
              <input
                name="population_served"
                type="text"
                placeholder="e.g. Low-income middle school students"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
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
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Creating…
              </>
            ) : (
              "Create Organization"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
