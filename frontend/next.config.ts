import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Performance optimizations */
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Optimize production builds
  productionBrowserSourceMaps: false,

  // Image optimization
  images: {
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Compression
  compress: true,

  // Experimental features for better performance
  experimental: {
    // Optimize package imports
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },

  // Output configuration for Docker deployment
  output: 'standalone',
};

export default nextConfig;
