/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  eslint: {
    // Lint is enforced as a separate CI step; don't block builds on warnings
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
