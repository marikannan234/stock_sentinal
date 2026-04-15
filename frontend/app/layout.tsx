import './globals.css';
import type { ReactNode } from 'react';
import { ToastProvider } from '@/components/ui/toast';
import { SessionBootstrap } from '@/components/session-bootstrap';
import { AlertBootstrap } from '@/components/alert-bootstrap';
import { DataSyncProvider } from '@/components/providers/data-sync-provider';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[var(--surface)] text-[var(--on-surface)] font-sans antialiased">
        <ToastProvider>
          <DataSyncProvider>
            <SessionBootstrap />
            <AlertBootstrap />
            {children}
          </DataSyncProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
