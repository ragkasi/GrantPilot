import { AlertTriangle, CheckCircle2, Info, RefreshCw } from "lucide-react";
import type { AnalysisSource } from "@/types";

interface ProvenanceBannerProps {
  analysisSource: AnalysisSource | null | undefined;
  fallbackReason?: string | null;
  onUploadMore?: () => void;
  onReanalyze?: () => void;
}

export function ProvenanceBanner({
  analysisSource,
  fallbackReason,
  onUploadMore,
  onReanalyze,
}: ProvenanceBannerProps) {
  if (!analysisSource) return null;

  if (analysisSource === "real_pipeline") {
    return (
      <div
        data-testid="provenance-banner"
        data-analysis-source="real_pipeline"
        role="status"
        aria-label="Analysis source: AI-generated from uploaded documents"
        className="flex items-center gap-2.5 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 mb-5"
      >
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        <p className="text-sm text-emerald-800">
          AI analysis grounded in your uploaded documents — requirements extracted and evidence matched.
        </p>
      </div>
    );
  }

  if (analysisSource === "seeded_demo") {
    return (
      <div
        data-testid="provenance-banner"
        data-analysis-source="seeded_demo"
        role="status"
        aria-label="Analysis source: pre-loaded demo data"
        className="flex items-center gap-2.5 bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-3 mb-5"
      >
        <Info className="w-4 h-4 text-indigo-500 shrink-0" />
        <p className="text-sm text-indigo-800">
          Demo project with pre-loaded sample data. Upload your own documents and click Re-analyze to see real results.
        </p>
        {onUploadMore && (
          <button
            onClick={onUploadMore}
            className="ml-auto shrink-0 text-xs font-medium text-indigo-700 underline hover:text-indigo-900"
          >
            Upload documents
          </button>
        )}
      </div>
    );
  }

  // fallback_mock
  const reason =
    fallbackReason ??
    "Upload a Grant Opportunity Document and a set of nonprofit documents, then Re-analyze.";

  return (
    <div
      data-testid="provenance-banner"
      data-analysis-source="fallback_mock"
      role="status"
      aria-label="Analysis source: sample data shown"
      className="flex items-start gap-2.5 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-5"
    >
      <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-amber-900">Showing sample analysis</p>
        <p className="text-sm text-amber-700 mt-0.5">{reason}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0 ml-2">
        {onUploadMore && (
          <button
            onClick={onUploadMore}
            className="text-xs font-medium text-amber-800 underline hover:text-amber-900"
          >
            Upload
          </button>
        )}
        {onReanalyze && (
          <button
            onClick={onReanalyze}
            className="flex items-center gap-1 text-xs font-medium text-amber-800 underline hover:text-amber-900"
          >
            <RefreshCw className="w-3 h-3" />
            Re-analyze
          </button>
        )}
      </div>
    </div>
  );
}
