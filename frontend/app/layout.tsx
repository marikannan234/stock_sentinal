import './globals.css';
import type { ReactNode } from 'react';
import { ToastProvider } from '@/components/ui/toast';
import { SessionBootstrap } from '@/components/session-bootstrap';
import { AlertBootstrap } from '@/components/alert-bootstrap';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[var(--surface)] font-sans text-[var(--on-surface)] antialiased">
        <ToastProvider>
          <SessionBootstrap />
          <AlertBootstrap />
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
