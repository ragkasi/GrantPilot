/**
 * JWT storage helpers.
 * Token is stored in localStorage under STORAGE_KEY.
 * All helpers are safe to call on the server (they no-op when window is absent).
 */

const STORAGE_KEY = "grantpilot_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
