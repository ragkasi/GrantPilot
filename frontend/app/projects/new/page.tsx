"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FolderOpen, CheckCircle2, Upload, X } from "lucide-react";
import { mockOrganization, mockProject } from "@/lib/mock-data";

const documentTypes = [
  { value: "mission_statement", label: "Mission Statement" },
  { value: "program_description", label: "Program Description" },
  { value: "annual_report", label: "Annual Report" },
  { value: "budget", label: "Annual Budget" },
  { value: "irs_letter", label: "IRS Determination Letter" },
  { value: "past_application", label: "Past Application" },
  { value: "grant_opportunity", label: "Grant Opportunity Document" },
  { value: "other", label: "Other" },
];

interface UploadedFile {
  name: string;
  type: string;
  size: string;
}

const mockUploadedFiles: UploadedFile[] = [
  { name: "Mission Statement.pdf", type: "mission_statement", size: "124 KB" },
  { name: "Program Description.pdf", type: "program_description", size: "287 KB" },
  { name: "Annual Report 2024.pdf", type: "annual_report", size: "1.2 MB" },
  { name: "Annual Budget FY2025.pdf", type: "budget", size: "98 KB" },
  { name: "Community STEM Access Fund RFP.pdf", type: "grant_opportunity", size: "312 KB" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState<"details" | "documents" | "analyzing" | "done">("details");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const handleDetailsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep("documents");
  };

  const addMockFile = (file: UploadedFile) => {
    setFiles((prev) => [...prev, file]);
  };

  const removeFile = (name: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const handleAnalyze = () => {
    setStep("analyzing");
    setTimeout(() => setStep("done"), 2000);
  };

  if (step === "analyzing") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Analyzing grant fit…</h2>
          <p className="text-sm text-gray-500">
            Extracting requirements, matching evidence, scoring readiness.
          </p>
          <div className="mt-6 space-y-2 text-left max-w-xs mx-auto">
            {[
              "Parsing uploaded documents",
              "Extracting grant requirements",
              "Matching evidence to requirements",
              "Scoring eligibility and readiness",
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-2.5 text-sm text-gray-500">
                <div className="w-4 h-4 border border-indigo-300 rounded-full bg-indigo-50 flex items-center justify-center">
                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full" />
                </div>
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (step === "done") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Analysis complete</h2>
          <p className="text-sm text-gray-500 mb-6">
            {mockProject.grant_name} has been analyzed for {mockOrganization.name}.
          </p>
          <button
            onClick={() => router.push(`/projects/${mockProject.id}`)}
            className="px-6 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            View Analysis Results
          </button>
        </div>
      </div>
    );
  }

  if (step === "documents") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="mb-7">
          <div className="flex items-center gap-2 text-sm text-gray-400 mb-3">
            <span className="text-indigo-600 font-medium">Project Details</span>
            <span>→</span>
            <span className="font-medium text-gray-700">Upload Documents</span>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">Upload Documents</h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload nonprofit documents and the grant opportunity. The more you upload, the better the analysis.
          </p>
        </div>

        <div className="space-y-4">
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
              dragOver ? "border-indigo-400 bg-indigo-50" : "border-gray-200 bg-white"
            }`}
          >
            <Upload className="w-8 h-8 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-700">Drop files here or</p>
            <p className="text-sm text-gray-400 mt-1">PDF, DOCX, or TXT · max 20 MB each</p>

            {/* Demo shortcut */}
            <div className="mt-5 pt-5 border-t border-gray-100">
              <p className="text-xs text-gray-400 mb-3">Demo: add sample documents</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {mockUploadedFiles
                  .filter((f) => !files.find((uf) => uf.name === f.name))
                  .map((f) => (
                    <button
                      key={f.name}
                      onClick={() => addMockFile(f)}
                      className="text-xs font-medium text-indigo-600 bg-indigo-50 border border-indigo-200 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors"
                    >
                      + {f.name}
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* Uploaded files list */}
          {files.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
              {files.map((file) => (
                <div key={file.name} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center text-xs font-bold text-gray-500">
                      PDF
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-400">{file.size}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <select
                      defaultValue={file.type}
                      className="text-xs border border-gray-200 rounded-md px-2 py-1 text-gray-600 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                    >
                      {documentTypes.map((dt) => (
                        <option key={dt.value} value={dt.value}>{dt.label}</option>
                      ))}
                    </select>
                    <button onClick={() => removeFile(file.name)} className="text-gray-400 hover:text-gray-600">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setStep("details")}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              ← Back
            </button>
            <button
              onClick={handleAnalyze}
              disabled={files.length === 0}
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Run Analysis →
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-7">
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-3">
          <span className="font-medium text-gray-700">Project Details</span>
          <span>→</span>
          <span>Upload Documents</span>
        </div>
        <div className="flex items-center gap-2.5 mb-2">
          <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
            <FolderOpen className="w-4 h-4 text-violet-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900">New Grant Project</h1>
        </div>
        <p className="text-sm text-gray-500">
          Enter the grant you&apos;re applying for. Then upload documents for analysis.
        </p>
      </div>

      <form onSubmit={handleDetailsSubmit} className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
        <div className="p-6 space-y-5">
          <h2 className="text-sm font-semibold text-gray-700">Grant Information</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Organization <span className="text-red-500">*</span>
            </label>
            <select className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white">
              <option>{mockOrganization.name}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Grant Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              defaultValue={mockProject.grant_name}
              required
              placeholder="e.g. Community STEM Access Fund"
              className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Funder / Foundation Name
            </label>
            <input
              type="text"
              defaultValue={mockProject.funder_name ?? undefined}
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
                type="text"
                defaultValue={mockProject.grant_amount ?? undefined}
                placeholder="e.g. $50,000 – $150,000"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Application Deadline
              </label>
              <input
                type="text"
                defaultValue={mockProject.deadline ?? undefined}
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
            className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Next: Upload Documents →
          </button>
        </div>
      </form>
    </div>
  );
}
