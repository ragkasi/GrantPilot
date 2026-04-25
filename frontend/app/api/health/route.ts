import { NextResponse } from "next/server";

/**
 * Frontend health endpoint — used by Docker health checks and load balancers.
 * Returns 200 when the Next.js server is running.
 */
export function GET() {
  return NextResponse.json({ status: "ok" });
}
