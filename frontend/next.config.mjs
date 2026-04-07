import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: __dirname,
  async rewrites() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');

    if (!apiOrigin) {
      return [];
    }

    return [
      {
        source: '/backend-api/:path*',
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

