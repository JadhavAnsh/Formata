import type { NextConfig } from "next";

const allowedDevOrigins = (
  process.env.NEXT_ALLOWED_DEV_ORIGINS ?? "localhost,127.0.0.1,192.168.1.148"
)
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  allowedDevOrigins,
  turbopack: {
    // Avoid incorrect monorepo root inference when multiple lockfiles exist.
    root: process.cwd(),
  },
};

export default nextConfig;
