"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Plus, ArrowRight, FileText, Building2, Clock, Loader2,
  AlertCircle, FolderOpen, Zap,
} from "lucide-react";
import { ApiError, getAnalysis, listOrganizations, listProjects } from "@/lib/api";
import type { AnalysisResult, Organization, Project } from "@/types";
import { cn, formatCurrency } from "@/lib/utils";
import { useDocumentTitle } from "@/lib/use-document-title";

type LoadState =
  | { phase: "loading" }
  | { phase: "error"; message: string; isNetwork: boolean }
  | { phase: "ready"; orgs: Organization[]; projects: Project[]; scores: Map<string, { eligibility: number; readiness: number }> };

const STATUS_STYLES: Record<string, { label: string; classes: string }> = {
  analyzed: { label: "Analyzed", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  report_generated: { label: "Report Ready", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  analyzing: { label: "Analyzing…", classes: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  documents_uploaded: { label: "Docs Uploaded", classes: "bg-amber-50 text-amber-700 border-amber-200" },
  draft: { label: "Draft", classes: "bg-gray-100 text-gray-500 border-gray-200" },
  error: { label: "Error", classes: "bg-red-50 text-red-600 border-red-200" },
};

export default function DashboardPage() {
  useDocumentTitle("Dashboard");
  const [state, setState] = useState<LoadState>({ phase: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ phase: "loading" });
      try {
        const [orgs, projects] = await Promise.all([listOrganizations(), listProjects()]);

        // Fetch analysis scores for analyzed projects in parallel (best-effort)
        const scoreMap = new Map<string, { eligibility: number; readiness: number }>();
        const analyzedIds = projects
          .filter((p) => p.status === "analyzed" || p.status === "report_generated")
          .map((p) => p.id);

        await Promise.all(
          analyzedIds.map(async (id) => {
            try {
              const a: AnalysisResult = await getAnalysis(id);
              scoreMap.set(id, { eligibility: a.eligibility_score, readiness: a.readiness_score });
            } catch {
              // silently skip — scores are optional enrichment
            }
          }),
        );

        if (!cancelled) setState({ phase: "ready", orgs, projects, scores: scoreMap });
      } catch (err) {
        if (!cancelled) {
          const isNetwork = err instanceof ApiError && err.status === 0;
          const message = err instanceof ApiError
            ? err.message
            : "Failed to load dashboard data.";
          setState({ phase: "error", message, isNetwork });
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  if (state.phase === "loading") {
    return (
      <div className="p-8 max-w-5xl mx-auto flex items-center justify-center min-h-[40vh]">
        <div className="flex items-center gap-3 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading dashboard…</span>
        </div>
      </div>
    );
  }

  if (state.phase === "error") {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className={cn(
          "border rounded-xl p-6 flex items-start gap-3",
          state.isNetwork
            ? "bg-amber-50 border-amber-200"
            : "bg-red-50 border-red-200",
        )}>
          <AlertCircle className={cn("w-5 h-5 shrink-0 mt-0.5", state.isNetwork ? "text-amber-500" : "text-red-500")} />
          <div>
            <p className={cn("text-sm font-medium", state.isNetwork ? "text-amber-700" : "text-red-700")}>
              {state.isNetwork ? "Backend unreachable" : "Failed to load dashboard"}
            </p>
            <p className={cn("text-sm mt-1", state.isNetwork ? "text-amber-600" : "text-red-600")}>
              {state.message}
            </p>
            {state.isNetwork && (
              <p className="text-xs text-amber-600 mt-2">
                Make sure the backend is running on port 8000 and try refreshing.
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  const { orgs, projects, scores } = state;
  const orgMap = Object.fromEntries(orgs.map((o) => [o.id, o]));
  const isNewUser = orgs.length === 0 && projects.length === 0;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Your grant projects and organizations.</p>
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

      {/* Onboarding empty state for brand-new users */}
      {isNewUser && (
        <div className="bg-white border border-indigo-100 rounded-2xl p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Welcome to GrantPilot</h2>
              <p className="text-sm text-gray-500">Get started in three steps.</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {[
              { step: "1", title: "Create an Organization", desc: "Add your nonprofit's name, mission, and basic details.", href: "/organizations/new", cta: "Add Organization" },
              { step: "2", title: "Start a Grant Project", desc: "Enter the grant you're applying for and link it to your org.", href: "/projects/new", cta: "New Project" },
              { step: "3", title: "Upload Documents & Analyze", desc: "Upload your nonprofit documents and the grant RFP, then run analysis.", href: "/projects/new", cta: "Get Started" },
            ].map(({ step, title, desc, href, cta }) => (
              <div key={step} className="bg-gray-50 rounded-xl p-5">
                <div className="w-7 h-7 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center text-xs font-bold mb-3">
                  {step}
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>
                <p className="text-xs text-gray-500 mb-4">{desc}</p>
                <Link
                  href={href}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                >
                  {cta} →
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Organizations */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Organizations
        </h2>
        {orgs.length === 0 && !isNewUser ? (
          <div className="bg-white border border-dashed border-gray-200 rounded-xl p-8 text-center">
            <Building2 className="w-8 h-8 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-600">No organizations yet</p>
            <p className="text-xs text-gray-400 mt-1 mb-4">Create one to start tracking grant projects.</p>
            <Link href="/organizations/new" className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors">
              <Plus className="w-3.5 h-3.5" />
              Add Organization
            </Link>
          </div>
        ) : orgs.length > 0 ? (
          <div className="space-y-3">
            {orgs.map((org) => {
              const orgProjects = projects.filter((p) => p.organization_id === org.id);
              return (
                <div key={org.id} className="bg-white border border-gray-200 rounded-xl p-5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center shrink-0">
                      <Building2 className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{org.name}</p>
                      <p className="text-sm text-gray-500">
                        {org.location}
                        {org.nonprofit_type && ` · ${org.nonprofit_type}`}
                        {org.annual_budget > 0 && ` · ${formatCurrency(org.annual_budget)} budget`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{orgProjects.length} project{orgProjects.length !== 1 ? "s" : ""}</span>
                    <span className="text-xs font-medium bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-full">Active</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}
      </section>

      {/* Projects */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Grant Projects
        </h2>
        {projects.length === 0 && !isNewUser ? (
          <div className="bg-white border border-dashed border-gray-200 rounded-xl p-8 text-center">
            <FolderOpen className="w-8 h-8 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-600">No grant projects yet</p>
            <p className="text-xs text-gray-400 mt-1 mb-4">
              {orgs.length === 0 ? "Create an organization first, then add grant projects." : "Create a project to start your grant readiness analysis."}
            </p>
            <Link href={orgs.length === 0 ? "/organizations/new" : "/projects/new"} className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors">
              <Plus className="w-3.5 h-3.5" />
              {orgs.length === 0 ? "Add Organization" : "New Project"}
            </Link>
          </div>
        ) : projects.length > 0 ? (
          <div className="space-y-3">
            {projects.map((project) => {
              const org = orgMap[project.organization_id];
              const style = STATUS_STYLES[project.status] ?? STATUS_STYLES.draft;
              const score = scores.get(project.id);
              return (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="block bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-sm transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1 min-w-0">
                      <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center mt-0.5 shrink-0">
                        <FileText className="w-5 h-5 text-violet-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-gray-900 truncate">{project.grant_name}</p>
                        <p className="text-sm text-gray-500 truncate">
                          {project.funder_name && `${project.funder_name} · `}{org?.name ?? ""}
                        </p>
                        <div className="flex flex-wrap items-center gap-2.5 mt-2">
                          <span className={cn("text-xs font-medium border px-2.5 py-1 rounded-full", style.classes)}>
                            {style.label}
                          </span>
                          {project.deadline && (
                            <span className="flex items-center gap-1 text-xs text-gray-400">
                              <Clock className="w-3 h-3" />
                              Due {project.deadline}
                            </span>
                          )}
                          {project.grant_amount && (
                            <span className="text-xs text-gray-400">{project.grant_amount}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 ml-4 shrink-0">
                      {/* Analysis scores for analyzed projects */}
                      {score && (
                        <div className="hidden sm:flex items-center gap-3 text-right">
                          <div>
                            <p className="text-xs text-gray-400">Eligibility</p>
                            <p className="text-lg font-bold text-indigo-600">{score.eligibility}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-400">Readiness</p>
                            <p className="text-lg font-bold text-violet-600">{score.readiness}</p>
                          </div>
                        </div>
                      )}
                      <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 transition-colors" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : null}
      </section>
    </div>
  );
}
