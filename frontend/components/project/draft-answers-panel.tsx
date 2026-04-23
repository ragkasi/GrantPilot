"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, AlertTriangle, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DraftAnswer } from "@/types";

function ConfidencePill({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colorClass =
    pct >= 80
      ? "bg-green-100 text-green-700 border-green-200"
      : pct >= 60
      ? "bg-amber-100 text-amber-700 border-amber-200"
      : "bg-red-100 text-red-700 border-red-200";
  return (
    <span className={cn("text-xs font-semibold px-2 py-0.5 rounded-full border", colorClass)}>
      {pct}% confidence
    </span>
  );
}

export function DraftAnswersPanel({ answers }: { answers: DraftAnswer[] }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set([answers[0]?.id]));

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="p-5 space-y-3">
      <p className="text-sm text-gray-500 mb-1">
        Draft answers are grounded in your uploaded documents. Review and edit before submitting.
      </p>

      {answers.map((answer) => (
        <div
          key={answer.id}
          className="border border-gray-200 rounded-xl overflow-hidden"
        >
          <button
            onClick={() => toggle(answer.id)}
            className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start gap-3 flex-1 mr-4">
              <ConfidencePill value={answer.confidence} />
              <p className="text-sm font-medium text-gray-900 leading-snug">
                {answer.question}
              </p>
            </div>
            {expanded.has(answer.id) ? (
              <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
            )}
          </button>

          {expanded.has(answer.id) && (
            <div className="px-5 pb-5 border-t border-gray-100">
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap mt-4">
                {answer.draft_answer}
              </p>

              {answer.missing_evidence.length > 0 && (
                <div className="mt-4 flex items-start gap-2.5 bg-amber-50 border border-amber-200 rounded-lg p-3.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-amber-800 mb-1">
                      Missing Evidence
                    </p>
                    {answer.missing_evidence.map((me, i) => (
                      <p key={i} className="text-sm text-amber-700">
                        {me}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {answer.citations.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Citations
                  </p>
                  <div className="space-y-1.5">
                    {answer.citations.map((cite, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <BookOpen className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0" />
                        <span className="font-medium text-indigo-600 whitespace-nowrap">
                          {cite.document_name} p.{cite.page_number}
                        </span>
                        <span className="text-gray-400">—</span>
                        <span className="text-gray-500">{cite.summary}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
