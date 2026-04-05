'use client';

import './globals.css';
import { ReactNode } from 'react';
import { Inter } from 'next/font/google';
import { AuthInitializer } from '@/components/AuthInitializer';
import { ToastProvider } from '@/components/ui/toast';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-slate-950 font-sans text-slate-100 antialiased">
        <ToastProvider>
          <AuthInitializer />
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}


