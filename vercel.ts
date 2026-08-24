import { VercelConfiguration } from '@vercel/config';

const config: VercelConfiguration = {
  buildCommand: 'cd web && npm run build',
  outputDirectory: 'web/.next',
  framework: 'nextjs',
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    STREAMLIT_URL: process.env.STREAMLIT_URL || 'http://localhost:8501'
  },

  functions: {
    'web/app/api/**': {
      maxDuration: 30,
      memory: 1024
    }
  },

  headers: [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Cache-Control', value: 'public, s-maxage=10, stale-while-revalidate=59' },
        { key: 'Access-Control-Allow-Origin', value: '*' },
        { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
        { 
          key: 'Access-Control-Allow-Headers', 
          value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' 
        }
      ]
    },
    {
      source: '/fonts/:path*',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }
      ]
    },
    {
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' }
      ]
    }
  ],

  redirects: [
    { source: '/clusters', destination: '/#clusters', permanent: true },
    { source: '/comparison', destination: '/#comparison', permanent: true },
    { source: '/export', destination: '/#export', permanent: true },
    { source: '/simulator', destination: '/#launch', permanent: true }
  ],

  rewrites: [
    {
      source: '/api/backend/:path*',
      destination: process.env.BACKEND_URL + '/:path*' || 'http://localhost:5000/:path*'
    }
  ]
};

export default config;
