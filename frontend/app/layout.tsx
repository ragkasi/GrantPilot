import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthGuard } from "@/components/auth/auth-guard";
import { AppShell } from "@/components/layout/app-shell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "GrantPilot",
  description: "AI-powered grant eligibility and application assistant for nonprofits",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 text-gray-900 antialiased`}>
        <AuthGuard>
          <AppShell>{children}</AppShell>
        </AuthGuard>
      </body>
    </html>
  );
}
