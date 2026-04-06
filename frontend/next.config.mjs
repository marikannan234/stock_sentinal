/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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

