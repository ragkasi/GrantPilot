"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Zap,
  Upload,
  Search,
  FileText,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Download,
  ExternalLink,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { useDocumentTitle } from "@/lib/use-document-title";

export default function LandingPage() {
  useDocumentTitle("GrantPilot — AI grant readiness for nonprofits");
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* ------------------------------------------------------------------ */}
      {/* Nav                                                                  */}
      {/* ------------------------------------------------------------------ */}
      <header className="border-b border-gray-100 bg-white sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-indigo-600 rounded-md flex items-center justify-center shrink-0">
              <Zap className="w-4 h-4 text-white" aria-hidden="true" />
            </div>
            <span className="font-semibold text-gray-900">GrantPilot</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              API Docs
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
            </a>
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Sign in
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* ---------------------------------------------------------------- */}
        {/* Hero                                                              */}
        {/* ---------------------------------------------------------------- */}
        <section className="max-w-5xl mx-auto px-6 pt-16 pb-14 text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-full px-4 py-1.5 text-xs font-medium text-indigo-700 mb-6">
            <Zap className="w-3.5 h-3.5" aria-hidden="true" />
            AI-powered grant readiness for small nonprofits
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 leading-tight mb-5 tracking-tight">
            Know if you&apos;re ready to apply —<br className="hidden sm:block" />
            <span className="text-indigo-600"> before you write a word.</span>
          </h1>

          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8 leading-relaxed">
            Upload your nonprofit&apos;s documents and a grant opportunity. GrantPilot extracts
            requirements, matches evidence from your files, scores eligibility and readiness,
            drafts application answers with citations, and generates a downloadable PDF report.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="w-full sm:w-auto px-6 py-3 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition-colors shadow-sm"
            >
              Try the demo →
            </Link>
            <a
              href="https://github.com/ragkasi/GrantPilot"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto px-6 py-3 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
            >
              View on GitHub
              <ExternalLink className="w-4 h-4" aria-hidden="true" />
            </a>
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* How it works                                                      */}
        {/* ---------------------------------------------------------------- */}
        <section
          className="bg-gray-50 border-y border-gray-100 py-14"
          aria-label="How it works"
        >
          <div className="max-w-5xl mx-auto px-6">
            <h2 className="text-xl font-semibold text-gray-900 text-center mb-10">
              How it works
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {[
                {
                  step: "1",
                  icon: Upload,
                  title: "Upload your documents",
                  desc: "Add your mission statement, annual report, budget, IRS determination letter, and other nonprofit materials.",
                },
                {
                  step: "2",
                  icon: Search,
                  title: "Add the grant opportunity",
                  desc: "Upload the grant RFP or announcement as a Grant Opportunity Document. GrantPilot extracts all requirements automatically.",
                },
                {
                  step: "3",
                  icon: CheckCircle2,
                  title: "Get your readiness analysis",
                  desc: "Review eligibility and readiness scores, see which requirements are met, read draft answers with citations, and download a PDF report.",
                },
              ].map(({ step, icon: Icon, title, desc }) => (
                <div key={step} className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm font-bold text-indigo-700 shrink-0">
                      {step}
                    </div>
                    <Icon className="w-5 h-5 text-indigo-500" aria-hidden="true" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">{title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* Feature highlights                                                */}
        {/* ---------------------------------------------------------------- */}
        <section className="max-w-5xl mx-auto px-6 py-14" aria-label="Features">
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-10">
            What you get
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                icon: CheckCircle2,
                color: "emerald",
                title: "Eligibility & Readiness Scores",
                desc: "Deterministic scores computed from evidence match statuses — no LLM guessing.",
              },
              {
                icon: Search,
                color: "indigo",
                title: "Evidence Matching with Citations",
                desc: "Each requirement is matched to the most relevant chunks in your uploaded documents, with page-level citations.",
              },
              {
                icon: BookOpen,
                color: "violet",
                title: "Draft Application Answers",
                desc: "Narrative questions get AI-drafted answers grounded in your actual documents — labeled as drafts, never as final submissions.",
              },
              {
                icon: FileText,
                color: "amber",
                title: "Missing Documents Checklist",
                desc: "See exactly which required documents are absent so you know what to gather before applying.",
              },
              {
                icon: AlertTriangle,
                color: "red",
                title: "Risk Flags",
                desc: "High, medium, and low-severity flags surface potential problems: budget mismatches, geography restrictions, and more.",
              },
              {
                icon: Download,
                color: "gray",
                title: "Downloadable PDF Report",
                desc: "A polished readiness packet you can share with your team or a grant writer before submission.",
              },
            ].map(({ icon: Icon, color, title, desc }) => (
              <div key={title} className="flex gap-4 p-5 bg-white border border-gray-100 rounded-xl">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                    color === "emerald" ? "bg-emerald-50" :
                    color === "indigo" ? "bg-indigo-50" :
                    color === "violet" ? "bg-violet-50" :
                    color === "amber" ? "bg-amber-50" :
                    color === "red" ? "bg-red-50" : "bg-gray-100"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 ${
                      color === "emerald" ? "text-emerald-600" :
                      color === "indigo" ? "text-indigo-600" :
                      color === "violet" ? "text-violet-600" :
                      color === "amber" ? "text-amber-600" :
                      color === "red" ? "text-red-500" : "text-gray-500"
                    }`}
                    aria-hidden="true"
                  />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* Demo callout                                                      */}
        {/* ---------------------------------------------------------------- */}
        <section
          className="bg-indigo-50 border-t border-indigo-100"
          aria-label="Try the demo"
        >
          <div className="max-w-5xl mx-auto px-6 py-12 flex flex-col sm:flex-row items-center justify-between gap-6">
            <div>
              <h2 className="text-lg font-semibold text-indigo-900 mb-1">
                Try it now — no sign-up required
              </h2>
              <p className="text-sm text-indigo-700 mb-3">
                A pre-loaded demo project (BrightPath Youth Foundation) shows the full
                analysis view with scores, evidence, and a downloadable report.
              </p>
              <div className="inline-flex items-center gap-4 bg-white border border-indigo-200 rounded-lg px-4 py-2.5 text-xs font-mono text-gray-700">
                <span>
                  <span className="text-gray-400">email</span>{" "}
                  demo@grantpilot.local
                </span>
                <span className="text-gray-300">·</span>
                <span>
                  <span className="text-gray-400">password</span>{" "}
                  DemoGrantPilot123!
                </span>
              </div>
            </div>
            <Link
              href="/login"
              className="shrink-0 px-6 py-3 text-sm font-semibold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition-colors shadow-sm"
            >
              Sign in with demo account →
            </Link>
          </div>
        </section>
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* Footer                                                              */}
      {/* ------------------------------------------------------------------ */}
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-indigo-600 rounded flex items-center justify-center">
              <Zap className="w-3 h-3 text-white" aria-hidden="true" />
            </div>
            <span>GrantPilot · FastAPI · Next.js · Claude AI</span>
          </div>
          <div className="flex items-center gap-5">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-600 transition-colors flex items-center gap-1"
            >
              API Docs
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
            </a>
            <a
              href="https://github.com/ragkasi/GrantPilot"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-600 transition-colors flex items-center gap-1"
            >
              GitHub
              <ExternalLink className="w-3 h-3" aria-hidden="true" />
            </a>
            <Link href="/login" className="hover:text-gray-600 transition-colors">
              Sign in
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
