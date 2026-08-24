/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable SWR caching for external API calls
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['three', '@react-three/fiber', '@react-three/drei']
  },

  // Enable image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60 * 60 * 24 * 365 // 1 year cache
  },

  // Headers for performance
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=10, stale-while-revalidate=59'
          }
        ]
      },
      {
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ];
  },

  // Compression
  compress: true,

  // Production sourcemaps disabled for smaller bundles
  productionBrowserSourceMaps: false,

  // React strict mode for catching errors
  reactStrictMode: true,

  // Trailing slash configuration
  trailingSlash: false
};

module.exports = nextConfig;
