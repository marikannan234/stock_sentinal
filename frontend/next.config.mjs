import path from 'path';
import { fileURLToPath } from 'url';
import { PHASE_PRODUCTION_BUILD } from 'next/constants.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {(phase: string) => import('next').NextConfig} */
export default function nextConfig(phase) {
  // NEXT_PUBLIC_* values are inlined into the bundle, so a production build
  // without the API origin would silently call localhost. Fail it instead.
  // (lib/config.ts reads and validates the value for the application.)
  if (phase === PHASE_PRODUCTION_BUILD && !process.env.NEXT_PUBLIC_API_URL) {
    throw new Error(
      'NEXT_PUBLIC_API_URL is required for a production build. ' +
        'Set it to the API origin, e.g. NEXT_PUBLIC_API_URL=https://api.example.com ' +
        '(Docker: --build-arg NEXT_PUBLIC_API_URL=...).',
    );
  }

  return {
    reactStrictMode: true,
    outputFileTracingRoot: __dirname,
  };
}
