import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enables Docker-friendly standalone output.
  // The production image uses .next/standalone/server.js directly.
  output: "standalone",

  // ESLint errors won't abort the production build.
  // Run `npm run lint` separately to surface lint issues during development.
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
