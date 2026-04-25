"use client";

import { useEffect, useRef, useState } from "react";
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
  Upload,
  FileText,
  XCircle,
  AlertTriangle,
  Pencil,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ApiError,
  deleteDocument,
  downloadReport,
  getAnalysis,
  getOrganization,
  getProject,
  listDocuments,
  runAnalysis,
  updateProject,
  uploadDocument,
} from "@/lib/api";
import type {
  AnalysisResult,
  Document,
  DocumentType,
  Organization,
  Project,
  ProjectUpdate,
} from "@/types";
import { ScoreRing } from "@/components/project/score-ring";
import { RequirementsTable } from "@/components/project/requirements-table";
import { DraftAnswersPanel } from "@/components/project/draft-answers-panel";
import { RiskPanel } from "@/components/project/risk-panel";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS = ["Requirements", "Draft Answers", "Missing Docs & Risks"] as const;
type Tab = (typeof TABS)[number];

const DOC_TYPES: { value: DocumentType; label: string }[] = [
  { value: "mission_statement", label: "Mission Statement" },
  { value: "program_description", label: "Program Description" },
  { value: "annual_report", label: "Annual Report" },
  { value: "budget", label: "Annual Budget" },
  { value: "irs_letter", label: "IRS Determination Letter" },
  { value: "grant_opportunity", label: "Grant Opportunity Document" },
  { value: "past_application", label: "Past Application" },
  { value: "other", label: "Other" },
];

const STATUS_STYLE: Record<string, { label: string; classes: string }> = {
  parsed: { label: "Parsed", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  stored: { label: "Stored", classes: "bg-gray-100 text-gray-600 border-gray-200" },
  uploaded: { label: "Uploading", classes: "bg-blue-50 text-blue-600 border-blue-200" },
  parse_failed: { label: "Parse Failed", classes: "bg-red-50 text-red-600 border-red-200" },
};

const ANALYZE_STEPS = [
  "Parsing uploaded documents",
  "Extracting grant requirements",
  "Matching evidence to requirements",
  "Scoring eligibility and readiness",
];

// ---------------------------------------------------------------------------
// Page state
// ---------------------------------------------------------------------------

type PageState =
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "upload"; project: Project; org: Organization; documents: Document[] }
  | { phase: "analyzing"; project: Project; org: Organization; documents: Document[] }
  | { phase: "ready"; project: Project; org: Organization; analysis: AnalysisResult; documents: Document[] };

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ProjectPage() {
  const params = useParams();
  const projectId = typeof params.id === "string" ? params.id : (params.id?.[0] ?? "");

  const [state, setState] = useState<PageState>({ phase: "loading" });
  const [activeTab, setActiveTab] = useState<Tab>("Requirements");

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<DocumentType>("mission_statement");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Delete state — maps doc_id to "confirming" state
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Download state
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  async function loadProject(cancelled?: { value: boolean }) {
    try {
      const project = await getProject(projectId);
      const [org, documents] = await Promise.all([
        getOrganization(project.organization_id),
        listDocuments(projectId),
      ]);

      if (cancelled?.value) return;

      if (project.status === "analyzed" || project.status === "report_generated") {
        const analysis = await getAnalysis(projectId);
        if (!cancelled?.value)
          setState({ phase: "ready", project, org, analysis, documents });
      } else {
        setState({ phase: "upload", project, org, documents });
      }
    } catch (err) {
      if (!cancelled?.value) {
        const message =
          err instanceof ApiError
            ? `${err.message} (${err.status})`
            : "Failed to load project data.";
        setState({ phase: "error", message });
      }
    }
  }

  useEffect(() => {
    if (!projectId) return;
    const cancelled = { value: false };
    setState({ phase: "loading" });
    loadProject(cancelled);
    return () => { cancelled.value = true; };
  }, [projectId]);

  async function handleUpload() {
    if (!selectedFile || state.phase !== "upload") return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(projectId, state.project.organization_id, docType, selectedFile);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      const freshDocs = await listDocuments(projectId);
      setState((prev) =>
        prev.phase === "upload" ? { ...prev, documents: freshDocs } : prev,
      );
    } catch (err) {
      setUploadError(
        err instanceof ApiError ? err.message : "Upload failed. Please try again.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: string) {
    if (deletingId !== docId) {
      setDeletingId(docId);
      return;
    }
    // Confirmed — proceed
    try {
      await deleteDocument(docId);
      setDeletingId(null);
      const freshDocs = await listDocuments(projectId);
      setState((prev) => {
        if (prev.phase === "upload") return { ...prev, documents: freshDocs };
        if (prev.phase === "ready") return { ...prev, documents: freshDocs };
        return prev;
      });
    } catch (err) {
      // Silently cancel confirmation on error; user can try again
      setDeletingId(null);
    }
  }

  async function handleRunAnalysis() {
    if (state.phase !== "upload") return;
    setState((prev) =>
      prev.phase === "upload"
        ? { phase: "analyzing", project: prev.project, org: prev.org, documents: prev.documents }
        : prev,
    );
    try {
      await runAnalysis(projectId);
      await loadProject();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Analysis failed. Please try again.";
      setState({ phase: "error", message });
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadReport(projectId);
    } catch (err) {
      setDownloadError(
        err instanceof ApiError ? err.message : "Download failed. Please try again.",
      );
    } finally {
      setDownloading(false);
    }
  }

  async function handleSaveEdit(data: ProjectUpdate) {
    setEditSaving(true);
    setEditError(null);
    try {
      const updated = await updateProject(projectId, data);
      setState((prev) => {
        if (prev.phase === "upload") return { ...prev, project: updated };
        if (prev.phase === "ready") return { ...prev, project: updated };
        return prev;
      });
      setIsEditing(false);
    } catch (err) {
      setEditError(
        err instanceof ApiError ? err.message : "Save failed. Please try again.",
      );
    } finally {
      setEditSaving(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Document list (shared between upload + ready states)
  // ---------------------------------------------------------------------------

  function renderDocumentList(documents: Document[], showDelete: boolean) {
    if (documents.length === 0) return null;
    return (
      <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
        {documents.map((doc) => {
          const s = STATUS_STYLE[doc.status] ?? STATUS_STYLE.stored;
          const typeLabel = DOC_TYPES.find((dt) => dt.value === doc.document_type)?.label ?? doc.document_type;
          const isConfirming = deletingId === doc.id;
          return (
            <div key={doc.id} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                  <p className="text-xs text-gray-400">{typeLabel}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0 ml-3">
                {doc.page_count != null && (
                  <span className="text-xs text-gray-400">{doc.page_count}p</span>
                )}
                <span className={cn("text-xs font-medium border px-2 py-0.5 rounded-full", s.classes)}>
                  {s.label}
                </span>
                {showDelete && (
                  isConfirming ? (
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs text-gray-500">Delete?</span>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-xs font-medium text-red-600 hover:text-red-800"
                      >
                        Yes
                      </button>
                      <button
                        onClick={() => setDeletingId(null)}
                        className="text-xs font-medium text-gray-500 hover:text-gray-700"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-gray-300 hover:text-red-400 transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (state.phase === "loading") return <LoadingSkeleton />;
  if (state.phase === "error") return <ErrorState message={state.message} />;
  if (state.phase === "analyzing") return <AnalyzingState project={state.project} org={state.org} />;

  // Edit form overlay (shown on top of upload or ready state)
  const currentProject = state.phase === "upload" || state.phase === "ready" ? state.project : null;
  const currentOrg = state.phase === "upload" || state.phase === "ready" ? state.org : null;

  if (state.phase === "upload") {
    const { project, org, documents } = state;
    return (
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          project={project}
          org={org}
          showDownload={false}
          onEdit={() => setIsEditing(!isEditing)}
          isEditing={isEditing}
        />

        {/* Inline edit form */}
        {isEditing && (
          <EditForm
            project={project}
            onSave={handleSaveEdit}
            onCancel={() => { setIsEditing(false); setEditError(null); }}
            saving={editSaving}
            error={editError}
          />
        )}

        <div className="px-8 py-6 max-w-4xl mx-auto space-y-5">
          {/* Upload card */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <Upload className="w-4 h-4 text-indigo-500" />
                Upload Documents
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Upload nonprofit documents and the grant opportunity. PDF, DOCX, or TXT &middot; max 20 MB.
              </p>
            </div>
            <div className="p-6 space-y-4">
              {uploadError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  {uploadError}
                </p>
              )}
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">Document Type</label>
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value as DocumentType)}
                    className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  >
                    {DOC_TYPES.map((dt) => (
                      <option key={dt.value} value={dt.value}>{dt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">File</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.doc,.txt"
                    onChange={(e) => {
                      setSelectedFile(e.target.files?.[0] ?? null);
                      setUploadError(null);
                    }}
                    className="block w-full text-sm text-gray-600
                      file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border file:border-gray-300
                      file:text-xs file:font-medium file:bg-white file:text-gray-700
                      hover:file:bg-gray-50 file:cursor-pointer cursor-pointer"
                  />
                </div>
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile || uploading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                  {uploading ? "Uploading…" : "Upload"}
                </button>
              </div>

              {documents.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Uploaded Documents
                  </p>
                  {renderDocumentList(documents, true)}
                </div>
              )}
            </div>
          </div>

          {/* Run analysis card */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-sm font-semibold text-gray-900 mb-1">Run Analysis</h2>
                <p className="text-sm text-gray-500">
                  {documents.length === 0
                    ? "Upload at least one document to begin analysis."
                    : `${documents.length} document${documents.length !== 1 ? "s" : ""} uploaded. Analysis will extract requirements and match evidence.`}
                </p>
                {!documents.some((d) => d.document_type === "grant_opportunity") && documents.length > 0 && (
                  <p className="text-xs text-amber-600 mt-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Upload a Grant Opportunity Document for the most accurate analysis.
                  </p>
                )}
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={documents.length === 0}
                className="shrink-0 ml-6 inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Run Analysis
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Ready state (analysis complete)
  // ---------------------------------------------------------------------------
  const { project, org, analysis, documents } = state;
  const { eligibility_score, readiness_score, requirements, missing_documents, risk_flags, draft_answers } = analysis;

  const metCount = requirements.filter((r) => r.status === "satisfied").length;
  const partialCount = requirements.filter((r) => r.status === "partially_satisfied").length;
  const highRiskCount = risk_flags.filter((f) => f.severity === "high").length;
  const requiredMissingCount = missing_documents.filter((d) => d.required).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        project={project}
        org={org}
        showDownload
        onDownload={handleDownload}
        downloading={downloading}
        downloadError={downloadError}
        onEdit={() => setIsEditing(!isEditing)}
        isEditing={isEditing}
      />

      {isEditing && (
        <EditForm
          project={project}
          onSave={handleSaveEdit}
          onCancel={() => { setIsEditing(false); setEditError(null); }}
          saving={editSaving}
          error={editError}
        />
      )}

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
            <StatBlock label="Requirements Met" value={`${metCount}/${requirements.length}`} sub={`${partialCount} partially met`} valueClass="text-gray-900" />
            <StatBlock label="Missing Documents" value={String(missing_documents.length)} sub={`${requiredMissingCount} required`} valueClass="text-amber-600" />
            <StatBlock label="High Risk Flags" value={String(highRiskCount)} sub={`${risk_flags.length - highRiskCount} medium / low`} valueClass={highRiskCount > 0 ? "text-red-500" : "text-gray-900"} />
            <StatBlock label="Draft Answers" value={String(draft_answers.length)} sub="ready to review" valueClass="text-gray-900" />
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-4">
          <div className="flex border-b border-gray-200">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-5 py-3.5 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-2",
                  activeTab === tab ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                )}
              >
                {tab}
                {tab === "Missing Docs & Risks" && highRiskCount > 0 && (
                  <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold bg-red-500 text-white rounded-full">{highRiskCount}</span>
                )}
              </button>
            ))}
          </div>
          {activeTab === "Requirements" && <RequirementsTable requirements={requirements} />}
          {activeTab === "Draft Answers" && <DraftAnswersPanel answers={draft_answers} />}
          {activeTab === "Missing Docs & Risks" && <RiskPanel missingDocuments={missing_documents} riskFlags={risk_flags} />}
        </div>

        {/* Analyzed documents summary */}
        {documents.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl px-5 py-4 mb-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Analyzed Documents ({documents.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {documents.map((doc) => {
                const s = STATUS_STYLE[doc.status] ?? STATUS_STYLE.stored;
                return (
                  <span key={doc.id} className={cn("inline-flex items-center gap-1.5 text-xs font-medium border px-2.5 py-1 rounded-full", s.classes)}>
                    <FileText className="w-3 h-3" />
                    {doc.filename}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Bottom bar */}
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl px-5 py-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-indigo-900">Ready to strengthen your application?</p>
            <p className="text-sm text-indigo-700 mt-0.5">
              Upload the {requiredMissingCount} missing required documents to improve your readiness score.
            </p>
          </div>
          <button
            onClick={() => setState({ phase: "upload", project, org, documents })}
            className="shrink-0 px-4 py-2 text-sm font-medium text-indigo-700 bg-white border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            Upload More Documents
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Edit form
// ---------------------------------------------------------------------------

function EditForm({
  project,
  onSave,
  onCancel,
  saving,
  error,
}: {
  project: Project;
  onSave: (data: ProjectUpdate) => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}) {
  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const data: ProjectUpdate = {};
    const grantName = (fd.get("grant_name") as string).trim();
    if (grantName) data.grant_name = grantName;
    const funderName = (fd.get("funder_name") as string).trim();
    data.funder_name = funderName || null;
    const deadline = (fd.get("deadline") as string).trim();
    data.deadline = deadline || null;
    const amount = (fd.get("grant_amount") as string).trim();
    data.grant_amount = amount || null;
    const url = (fd.get("grant_source_url") as string).trim();
    data.grant_source_url = url || null;
    onSave(data);
  }

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-5 max-w-7xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-semibold text-gray-700">Edit Project Details</h3>
          <button type="button" onClick={onCancel} className="text-xs text-gray-400 hover:text-gray-600">
            Cancel
          </button>
        </div>
        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
        )}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Grant Name *</label>
            <input
              name="grant_name"
              type="text"
              defaultValue={project.grant_name}
              required
              maxLength={300}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Funder</label>
            <input
              name="funder_name"
              type="text"
              defaultValue={project.funder_name ?? ""}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Deadline</label>
            <input
              name="deadline"
              type="text"
              defaultValue={project.deadline ?? ""}
              placeholder="e.g. May 15, 2026"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Amount Range</label>
            <input
              name="grant_amount"
              type="text"
              defaultValue={project.grant_amount ?? ""}
              placeholder="e.g. $50,000 – $150,000"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Source URL</label>
            <input
              name="grant_source_url"
              type="url"
              defaultValue={project.grant_source_url ?? ""}
              placeholder="https://..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {saving ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</> : "Save Changes"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared sub-components
// ---------------------------------------------------------------------------

function PageHeader({
  project, org, showDownload, onDownload, downloading, downloadError, onEdit, isEditing,
}: {
  project: Project;
  org: Organization;
  showDownload: boolean;
  onDownload?: () => void;
  downloading?: boolean;
  downloadError?: string | null;
  onEdit?: () => void;
  isEditing?: boolean;
}) {
  const statusBadge =
    project.status === "analyzed" || project.status === "report_generated"
      ? { label: "Analyzed", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" }
      : project.status === "analyzing"
      ? { label: "Analyzing…", classes: "bg-indigo-50 text-indigo-700 border-indigo-200" }
      : { label: "Draft", classes: "bg-gray-100 text-gray-500 border-gray-200" };

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="px-8 pt-5 pb-0 max-w-7xl mx-auto">
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700 mb-4 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          Dashboard
        </Link>
        <div className="flex items-start justify-between pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-500">{org.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-gray-900">{project.grant_name}</h1>
              {onEdit && (
                <button
                  onClick={onEdit}
                  className={cn(
                    "p-1 rounded transition-colors",
                    isEditing ? "text-indigo-600 bg-indigo-50" : "text-gray-300 hover:text-gray-600 hover:bg-gray-50",
                  )}
                  title="Edit project details"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 mt-2.5">
              {project.funder_name && <span className="text-sm text-gray-500">{project.funder_name}</span>}
              {project.deadline && (
                <>
                  <span className="text-gray-300">·</span>
                  <span className="flex items-center gap-1 text-sm text-gray-500"><Clock className="w-3.5 h-3.5" />Due {project.deadline}</span>
                </>
              )}
              {project.grant_amount && (
                <>
                  <span className="text-gray-300">·</span>
                  <span className="flex items-center gap-1 text-sm text-gray-500"><DollarSign className="w-3.5 h-3.5" />{project.grant_amount}</span>
                </>
              )}
              <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium border px-2.5 py-1 rounded-full", statusBadge.classes)}>
                <CheckCircle2 className="w-3 h-3" />
                {statusBadge.label}
              </span>
            </div>
            {downloadError && (
              <p className="text-xs text-red-600 mt-2">{downloadError}</p>
            )}
          </div>
          {showDownload && onDownload && (
            <button
              onClick={onDownload}
              disabled={downloading}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-60 transition-colors shadow-sm"
            >
              {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {downloading ? "Generating…" : "Download Report"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalyzingState({ project, org }: { project: Project; org: Organization }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader project={{ ...project, status: "analyzing" }} org={org} showDownload={false} />
      <div className="px-8 py-12 max-w-4xl mx-auto flex items-center justify-center">
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center w-full max-w-md">
          <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Analyzing grant fit…</h2>
          <p className="text-sm text-gray-500 mb-8">Extracting requirements, matching evidence, scoring readiness.</p>
          <div className="space-y-3 text-left">
            {ANALYZE_STEPS.map((step, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-gray-500">
                <div className="w-5 h-5 border border-indigo-300 rounded-full bg-indigo-50 flex items-center justify-center shrink-0">
                  <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
                </div>
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

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
        <Link href="/dashboard" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

function StatBlock({ label, value, sub, valueClass }: { label: string; value: string; sub: string; valueClass: string }) {
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
