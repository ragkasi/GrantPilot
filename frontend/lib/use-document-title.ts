import { useEffect } from "react";

/**
 * Sets document.title for the current page.
 * Appends " — GrantPilot" suffix automatically.
 * Restores the root title on unmount.
 */
export function useDocumentTitle(title: string): void {
  useEffect(() => {
    const full = title ? `${title} — GrantPilot` : "GrantPilot";
    document.title = full;
    return () => {
      document.title = "GrantPilot";
    };
  }, [title]);
}
