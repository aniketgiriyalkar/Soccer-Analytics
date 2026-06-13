import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/football-lab",
  assetPrefix: "/football-lab",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
