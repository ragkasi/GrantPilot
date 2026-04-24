"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";

const NO_SIDEBAR_PATHS = ["/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = !NO_SIDEBAR_PATHS.includes(pathname);

  if (!showSidebar) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 overflow-auto min-w-0">{children}</div>
    </div>
  );
}
