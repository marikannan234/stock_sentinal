import './globals.css';
import type { ReactNode } from 'react';
import { ToastProvider } from '@/components/ui/toast';
import { SessionBootstrap } from '@/components/session-bootstrap';
import { AlertBootstrap } from '@/components/alert-bootstrap';
import { QueryProvider } from '@/components/providers/query-provider';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[var(--surface)] text-[var(--on-surface)] font-sans antialiased">
        <ToastProvider>
          <QueryProvider>
            <SessionBootstrap />
            <AlertBootstrap />
            {children}
          </QueryProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
