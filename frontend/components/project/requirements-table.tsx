"use client";

import { useState, Fragment } from "react";
import { CheckCircle2, AlertCircle, XCircle, ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Requirement, RequirementStatus } from "@/types";

const statusConfig: Record<
  RequirementStatus,
  { label: string; icon: React.ComponentType<{ className?: string }>; className: string }
> = {
  satisfied: {
    label: "Satisfied",
    icon: CheckCircle2,
    className: "bg-green-50 text-green-700 border-green-200",
  },
  partially_satisfied: {
    label: "Partial",
    icon: AlertCircle,
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  not_satisfied: {
    label: "Not Met",
    icon: XCircle,
    className: "bg-red-50 text-red-700 border-red-200",
  },
  unclear: {
    label: "Unclear",
    icon: AlertCircle,
    className: "bg-gray-50 text-gray-600 border-gray-200",
  },
};

function StatusBadge({ status }: { status: RequirementStatus }) {
  const { label, icon: Icon, className } = statusConfig[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border whitespace-nowrap",
        className
      )}
    >
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const barColor =
    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full", barColor)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 tabular-nums">{pct}%</span>
    </div>
  );
}

export function RequirementsTable({ requirements }: { requirements: Requirement[] }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3 w-28">
              Status
            </th>
            <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">
              Requirement
            </th>
            <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3 w-36">
              Type
            </th>
            <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3 w-36">
              Confidence
            </th>
            <th className="w-10 px-4" />
          </tr>
        </thead>
        <tbody>
          {requirements.map((req) => (
            <Fragment key={req.id}>
              <tr
                onClick={() => req.evidence.length > 0 && toggle(req.id)}
                className={cn(
                  "border-b border-gray-50 transition-colors",
                  req.evidence.length > 0
                    ? "cursor-pointer hover:bg-gray-50"
                    : "cursor-default"
                )}
              >
                <td className="px-5 py-4">
                  <StatusBadge status={req.status} />
                </td>
                <td className="px-5 py-4">
                  <p className="text-sm text-gray-900">{req.text}</p>
                </td>
                <td className="px-5 py-4">
                  <span className="text-xs text-gray-500 capitalize">
                    {req.type.replace("_", " ")}
                  </span>
                </td>
                <td className="px-5 py-4">
                  {req.status !== "not_satisfied" ? (
                    <ConfidenceBar value={req.confidence} />
                  ) : (
                    <span className="text-xs text-gray-300">—</span>
                  )}
                </td>
                <td className="px-4 py-4">
                  {req.evidence.length > 0 &&
                    (expanded.has(req.id) ? (
                      <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    ))}
                </td>
              </tr>

              {expanded.has(req.id) && req.evidence.length > 0 && (
                <tr className="bg-indigo-50/40 border-b border-indigo-100/60">
                  <td />
                  <td colSpan={4} className="px-5 py-4">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5">
                      Supporting Evidence
                    </p>
                    <div className="space-y-2">
                      {req.evidence.map((cite, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-3 bg-white border border-indigo-100 rounded-lg p-3"
                        >
                          <BookOpen className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-indigo-700">
                              {cite.document_name} · p.{cite.page_number}
                            </p>
                            <p className="text-sm text-gray-600 mt-0.5">{cite.summary}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
