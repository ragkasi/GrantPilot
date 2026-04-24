"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  CheckCircle2,
  Clock,
  DollarSign,
  Building2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError, downloadReport, getAnalysis, getOrganization, getProject, runAnalysis } from "@/lib/api";
import type { AnalysisResult, Organization, Project } from "@/types";
import { ScoreRing } from "@/components/project/score-ring";
import { RequirementsTable } from "@/components/project/requirements-table";
import { DraftAnswersPanel } from "@/components/project/draft-answers-panel";
import { RiskPanel } from "@/components/project/risk-panel";

const TABS = ["Requirements", "Draft Answers", "Missing Docs & Risks"] as const;
type Tab = (typeof TABS)[number];

type PageState =
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "needs_analysis"; project: Project; org: Organization }
  | { phase: "ready"; project: Project; org: Organization; analysis: AnalysisResult };

export default function ProjectPage() {
  const params = useParams();
  const projectId = typeof params.id === "string" ? params.id : (params.id?.[0] ?? "");

  const [state, setState] = useState<PageState>({ phase: "loading" });
  const [activeTab, setActiveTab] = useState<Tab>("Requirements");
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (!projectId) return;

    let cancelled = false;

    async function load() {
      setState({ phase: "loading" });
      try {
        const project = await getProject(projectId);
        const org = await getOrganization(project.organization_id);

        if (project.status !== "analyzed" && project.status !== "report_generated") {
          if (!cancelled) setState({ phase: "needs_analysis", project, org });
          return;
        }

        const analysis = await getAnalysis(projectId);
        if (!cancelled) setState({ phase: "ready", project, org, analysis });
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? `${err.message} (${err.status})`
              : "Failed to load project data.";
          setState({ phase: "error", message });
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, [projectId]);

  async function handleRunAnalysis() {
    if (state.phase !== "needs_analysis") return;
    setAnalyzing(true);
    try {
      await runAnalysis(projectId);
      const [updatedProject, analysis] = await Promise.all([
        getProject(projectId),
        getAnalysis(projectId),
      ]);
      setState({ phase: "ready", project: updatedProject, org: state.org, analysis });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Analysis failed. Please try again.";
      setState({ phase: "error", message });
    } finally {
      setAnalyzing(false);
    }
  }

  if (state.phase === "loading") return <LoadingSkeleton />;
  if (state.phase === "error") return <ErrorState message={state.message} />;
  if (state.phase === "needs_analysis") {
    return (
      <NeedsAnalysisState
        project={state.project}
        org={state.org}
        analyzing={analyzing}
        onRunAnalysis={handleRunAnalysis}
      />
    );
  }

  const { project, org, analysis } = state;
  const {
    eligibility_score,
    readiness_score,
    requirements,
    missing_documents,
    risk_flags,
    draft_answers,
  } = analysis;

  const metCount = requirements.filter((r) => r.status === "satisfied").length;
  const partialCount = requirements.filter((r) => r.status === "partially_satisfied").length;
  const highRiskCount = risk_flags.filter((f) => f.severity === "high").length;
  const requiredMissingCount = missing_documents.filter((d) => d.required).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 pt-5 pb-0 max-w-7xl mx-auto">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700 mb-4 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Dashboard
          </Link>

          <div className="flex items-start justify-between pb-5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Building2 className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-500">{org.name}</span>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">{project.grant_name}</h1>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 mt-2.5">
                {project.funder_name && (
                  <span className="text-sm text-gray-500">{project.funder_name}</span>
                )}
                {project.deadline && (
                  <>
                    <span className="text-gray-300">·</span>
                    <span className="flex items-center gap-1 text-sm text-gray-500">
                      <Clock className="w-3.5 h-3.5" />
                      Due {project.deadline}
                    </span>
                  </>
                )}
                {project.grant_amount && (
                  <>
                    <span className="text-gray-300">·</span>
                    <span className="flex items-center gap-1 text-sm text-gray-500">
                      <DollarSign className="w-3.5 h-3.5" />
                      {project.grant_amount}
                    </span>
                  </>
                )}
                <span className="inline-flex items-center gap-1.5 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  Analyzed
                </span>
              </div>
            </div>

            <button
              onClick={() => downloadReport(projectId)}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 active:bg-indigo-800 transition-colors shadow-sm"
            >
              <Download className="w-4 h-4" />
              Download Report
            </button>
          </div>
        </div>
      </div>

      <div className="px-8 py-6 max-w-7xl mx-auto">
        {/* Score summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col items-center justify-center">
            <ScoreRing score={eligibility_score} label="Eligibility Score" color="indigo" />
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col items-center justify-center">
            <ScoreRing score={readiness_score} label="Readiness Score" color="violet" />
          </div>

          <div className="col-span-2 bg-white border border-gray-200 rounded-xl p-5 grid grid-cols-2 gap-5">
            <StatBlock
              label="Requirements Met"
              value={`${metCount}/${requirements.length}`}
              sub={`${partialCount} partially met`}
              valueClass="text-gray-900"
            />
            <StatBlock
              label="Missing Documents"
              value={String(missing_documents.length)}
              sub={`${requiredMissingCount} required`}
              valueClass="text-amber-600"
            />
            <StatBlock
              label="High Risk Flags"
              value={String(highRiskCount)}
              sub={`${risk_flags.length - highRiskCount} medium / low`}
              valueClass={highRiskCount > 0 ? "text-red-500" : "text-gray-900"}
            />
            <StatBlock
              label="Draft Answers"
              value={String(draft_answers.length)}
              sub="ready to review"
              valueClass="text-gray-900"
            />
          </div>
        </div>

        {/* Tabs + content */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex border-b border-gray-200">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-5 py-3.5 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-2",
                  activeTab === tab
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                )}
              >
                {tab}
                {tab === "Missing Docs & Risks" && highRiskCount > 0 && (
                  <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold bg-red-500 text-white rounded-full">
                    {highRiskCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {activeTab === "Requirements" && <RequirementsTable requirements={requirements} />}
          {activeTab === "Draft Answers" && <DraftAnswersPanel answers={draft_answers} />}
          {activeTab === "Missing Docs & Risks" && (
            <RiskPanel missingDocuments={missing_documents} riskFlags={risk_flags} />
          )}
        </div>

        {/* Bottom action bar */}
        <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-xl px-5 py-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-indigo-900">
              Ready to strengthen your application?
            </p>
            <p className="text-sm text-indigo-700 mt-0.5">
              Upload the {requiredMissingCount} missing required documents to improve your readiness
              score.
            </p>
          </div>
          <Link
            href="/projects/new"
            className="shrink-0 px-4 py-2 text-sm font-medium text-indigo-700 bg-white border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            Upload Documents
          </Link>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-states
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 animate-pulse">
      <div className="bg-white border-b border-gray-200 px-8 pt-5 pb-6 max-w-7xl mx-auto">
        <div className="h-4 w-20 bg-gray-200 rounded mb-4" />
        <div className="h-6 w-64 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-96 bg-gray-200 rounded" />
      </div>
      <div className="px-8 py-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-xl h-36" />
          ))}
        </div>
        <div className="bg-white border border-gray-200 rounded-xl h-64" />
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white border border-red-200 rounded-xl p-8 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Failed to load project</h2>
        <p className="text-sm text-gray-500 mb-5">{message}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

function NeedsAnalysisState({
  project,
  org,
  analyzing,
  onRunAnalysis,
}: {
  project: Project;
  org: Organization;
  analyzing: boolean;
  onRunAnalysis: () => void;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-8 pt-5 pb-5 max-w-7xl mx-auto">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Dashboard
        </Link>
        <div className="flex items-center gap-2 mb-1">
          <Building2 className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">{org.name}</span>
        </div>
        <h1 className="text-xl font-semibold text-gray-900">{project.grant_name}</h1>
      </div>

      <div className="px-8 py-12 max-w-7xl mx-auto flex items-center justify-center">
        <div className="max-w-sm w-full bg-white border border-gray-200 rounded-xl p-8 text-center">
          <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-6 h-6 text-indigo-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Ready to analyze</h2>
          <p className="text-sm text-gray-500 mb-6">
            Upload your documents then run analysis to see eligibility scores, evidence matches, and
            draft answers.
          </p>
          <button
            onClick={onRunAnalysis}
            disabled={analyzing}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              "Run Analysis"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

function StatBlock({
  label,
  value,
  sub,
  valueClass,
}: {
  label: string;
  value: string;
  sub: string;
  valueClass: string;
}) {
  return (
    <div className="flex flex-col justify-between">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{label}</p>
      <div className="mt-2">
        <p className={cn("text-3xl font-bold", valueClass)}>{value}</p>
        <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
      </div>
    </div>
  );
}
