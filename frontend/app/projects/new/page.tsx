import { Suspense } from "react";
import { ProjectForm } from "./project-form";

// This page is intentionally a Server Component so that the Suspense boundary
// is respected by Next.js 15. The client logic (including useSearchParams) lives
// in project-form.tsx which is marked "use client".
export default function NewProjectPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-gray-400">Loading…</div>}>
      <ProjectForm />
    </Suspense>
  );
}
