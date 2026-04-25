"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { User, Calendar, ArrowLeft, LogOut, Loader2, AlertCircle } from "lucide-react";
import { ApiError, getMe, listOrganizations, listProjects } from "@/lib/api";
import { clearToken } from "@/lib/auth";
import { useDocumentTitle } from "@/lib/use-document-title";

interface UserInfo {
  id: string;
  email: string;
  created_at: string;
}

interface Stats {
  orgCount: number;
  projectCount: number;
}

export default function AccountPage() {
  useDocumentTitle("Account");
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [me, orgs, projects] = await Promise.all([
          getMe(),
          listOrganizations(),
          listProjects(),
        ]);
        setUser(me);
        setStats({ orgCount: orgs.length, projectCount: projects.length });
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load account information.",
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleSignOut() {
    clearToken();
    router.push("/login");
  }

  function formatDate(iso: string): string {
    try {
      return new Date(iso).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch {
      return iso;
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Dashboard
        </Link>
        <h1 className="text-2xl font-semibold text-gray-900">Account</h1>
        <p className="text-sm text-gray-500 mt-1">Your profile and account settings.</p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-gray-400 py-8">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading account…</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {user && (
        <div className="space-y-4">
          {/* Profile card */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Profile</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-indigo-100 rounded-full flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-indigo-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Email</p>
                  <p className="text-sm font-medium text-gray-900">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center shrink-0">
                  <Calendar className="w-4 h-4 text-gray-500" />
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Member since</p>
                  <p className="text-sm font-medium text-gray-900">{formatDate(user.created_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Stats card */}
          {stats && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Activity</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-gray-900">{stats.orgCount}</p>
                  <p className="text-xs text-gray-500 mt-1">Organization{stats.orgCount !== 1 ? "s" : ""}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-gray-900">{stats.projectCount}</p>
                  <p className="text-xs text-gray-500 mt-1">Grant Project{stats.projectCount !== 1 ? "s" : ""}</p>
                </div>
              </div>
            </div>
          )}

          {/* Sign out */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Session</h2>
            <p className="text-sm text-gray-500 mb-4">
              Sign out of GrantPilot on this device. Your data is saved and you can sign back in anytime.
            </p>
            <button
              onClick={handleSignOut}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
