import { AlertTriangle, FileX } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MissingDocument, RiskFlag, RiskSeverity } from "@/types";

const severityStyles: Record<
  RiskSeverity,
  { card: string; badge: string; dot: string }
> = {
  high: {
    card: "bg-red-50/60 border-red-200",
    badge: "bg-red-100 text-red-700 border-red-200",
    dot: "bg-red-500",
  },
  medium: {
    card: "bg-amber-50/60 border-amber-200",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
    dot: "bg-amber-400",
  },
  low: {
    card: "bg-gray-50 border-gray-200",
    badge: "bg-gray-100 text-gray-600 border-gray-200",
    dot: "bg-gray-400",
  },
};

export function RiskPanel({
  missingDocuments,
  riskFlags,
}: {
  missingDocuments: MissingDocument[];
  riskFlags: RiskFlag[];
}) {
  return (
    <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Missing documents */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <FileX className="w-4 h-4 text-amber-500" />
          Missing Documents
        </h3>
        <div className="space-y-3">
          {missingDocuments.map((doc, i) => (
            <div
              key={i}
              className="border border-amber-200 bg-amber-50/50 rounded-xl p-4"
            >
              <div className="flex items-start justify-between gap-3 mb-1.5">
                <p className="text-sm font-semibold text-gray-900">{doc.name}</p>
                <span
                  className={cn(
                    "shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border",
                    doc.required
                      ? "bg-red-50 text-red-700 border-red-200"
                      : "bg-gray-50 text-gray-600 border-gray-200"
                  )}
                >
                  {doc.required ? "Required" : "Recommended"}
                </span>
              </div>
              <p className="text-sm text-gray-600">{doc.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Risk flags */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          Risk Flags
        </h3>
        <div className="space-y-3">
          {riskFlags.map((flag, i) => {
            const s = severityStyles[flag.severity];
            return (
              <div key={i} className={cn("border rounded-xl p-4", s.card)}>
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full shrink-0 mt-1", s.dot)} />
                    <p className="text-sm font-semibold text-gray-900">{flag.title}</p>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border capitalize",
                      s.badge
                    )}
                  >
                    {flag.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 ml-4">{flag.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
