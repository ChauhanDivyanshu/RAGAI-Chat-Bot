import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["172.17.80.1", "localhost"],
  
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/:path*",
      },
    ];
  },
};

export default nextConfig;
