'use client';

import { ReactNode } from 'react';

/**
 * Auth layout for login and register pages
 * 
 * This layout group ensures that authentication pages
 * do NOT have the sidebar or any dashboard elements.
 * Users accessing /login or /register will see only
 * the page content without navigation sidebars.
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
