'use client';

import { ReactNode } from 'react';

import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppShell({
  currentPage,
  title,
  description,
  actions,
  children,
}: {
  currentPage: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="dark bg-background text-on-surface selection:bg-primary/30">
      <TopBar />
      <Sidebar currentPage={currentPage} />

      <main className="min-h-screen pl-16 pr-6 pt-32 pb-12">
        <div className="mx-auto max-w-[1600px] space-y-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white">{title}</h1>
              {description ? <p className="mt-2 text-sm text-on-surface-variant">{description}</p> : null}
            </div>
            {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
