import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enables Docker-friendly standalone output.
  // The production image uses .next/standalone/server.js directly.
  output: "standalone",
};

export default nextConfig;
