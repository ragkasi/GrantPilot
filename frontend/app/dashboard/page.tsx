import Link from "next/link";
import { Plus, ArrowRight, FileText, Building2, Clock } from "lucide-react";
import { mockProject, mockOrganization, mockAnalysis } from "@/lib/mock-data";
import { formatCurrency } from "@/lib/utils";

export default function DashboardPage() {
  const { eligibility_score, readiness_score, requirements, missing_documents } = mockAnalysis;
  const metCount = requirements.filter((r) => r.status === "satisfied").length;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Your grant projects and organizations.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/organizations/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Organization
          </Link>
          <Link
            href="/projects/new"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Project
          </Link>
        </div>
      </div>

      {/* Organizations */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Organizations
        </h2>
        <div className="bg-white border border-gray-200 rounded-xl p-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">{mockOrganization.name}</p>
              <p className="text-sm text-gray-500">
                {mockOrganization.location} · {mockOrganization.nonprofit_type} ·{" "}
                {formatCurrency(mockOrganization.annual_budget)} annual budget
              </p>
            </div>
          </div>
          <span className="text-xs font-medium bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-full">
            Active
          </span>
        </div>
      </section>

      {/* Projects */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Grant Projects
        </h2>
        <Link
          href={`/projects/${mockProject.id}`}
          className="block bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-sm transition-all group"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center mt-0.5">
                <FileText className="w-5 h-5 text-violet-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{mockProject.grant_name}</p>
                <p className="text-sm text-gray-500">
                  {mockProject.funder_name} · {mockOrganization.name}
                </p>
                <div className="flex items-center gap-2.5 mt-2">
                  <span className="text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full">
                    Analyzed
                  </span>
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <Clock className="w-3 h-3" />
                    Due {mockProject.deadline}
                  </span>
                  <span className="text-xs text-gray-400">{mockProject.grant_amount}</span>
                </div>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 transition-colors mt-1" />
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Eligibility</p>
              <p className="text-xl font-semibold text-gray-900">
                {eligibility_score}
                <span className="text-sm font-normal text-gray-400">/100</span>
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Readiness</p>
              <p className="text-xl font-semibold text-gray-900">
                {readiness_score}
                <span className="text-sm font-normal text-gray-400">/100</span>
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Requirements Met</p>
              <p className="text-xl font-semibold text-gray-900">
                {metCount}
                <span className="text-sm font-normal text-gray-400">/{requirements.length}</span>
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-0.5">Missing Docs</p>
              <p className="text-xl font-semibold text-amber-600">
                {missing_documents.length}
              </p>
            </div>
          </div>
        </Link>
      </section>
    </div>
  );
}
