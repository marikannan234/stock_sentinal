'use client';

import './globals.css';
import { ReactNode } from 'react';
import { Inter } from 'next/font/google';
import { ToastProvider } from '@/components/ui/toast';
import { SessionBootstrap } from '@/components/session-bootstrap';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[var(--surface)] font-sans text-[var(--on-surface)] antialiased">
        <ToastProvider>
          <SessionBootstrap />
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
