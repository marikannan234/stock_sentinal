'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/sentinel-utils';
import {
  Search,
  X,
  Loader,
  Bell,
  User,
  Shield,
  LogOut,
  AlertCircle,
  MoreHorizontal,
  CheckCircle,
  LayoutDashboard,
  LineChart,
  PieChart,
  List,
  History,
  FileText,
  HelpCircle,
  Settings,
} from 'lucide-react';

const iconMap: Record<string, React.ComponentType<any>> = {
  search: Search,
  close: X,
  progress_activity: Loader,
  notifications: Bell,
  notifications_active: Bell,
  account_circle: User,
  shield_person: Shield,
  logout: LogOut,
  error_outline: AlertCircle,
  more_horiz: MoreHorizontal,
  check_circle: CheckCircle,
  dashboard: LayoutDashboard,
  show_chart: LineChart,
  pie_chart: PieChart,
  list_alt: List,
  history: History,
  article: FileText,
  help_outline: HelpCircle,
  settings: Settings,
};

function parseSizeFromClass(className?: string): number {
  if (!className) return 20; // default size
  
  // Handle pixel sizes like text-[22px]
  const pixelMatch = className.match(/text-\[(\d+)px\]/);
  if (pixelMatch) return parseInt(pixelMatch[1]);
  
  // Handle Tailwind size classes
  if (className.includes('text-xs')) return 12;
  if (className.includes('text-sm')) return 14;
  if (className.includes('text-base')) return 16;
  if (className.includes('text-lg')) return 18;
  if (className.includes('text-xl')) return 20;
  if (className.includes('text-2xl')) return 24;
  if (className.includes('text-3xl')) return 30;
  if (className.includes('text-4xl')) return 36;
  
  return 20; // default
}

export function Icon({ name, className }: { name: string; className?: string }) {
  const IconComponent = iconMap[name];
  
  // If icon not found, return null (never return text)
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in lucide-react mapping`);
    return null;
  }
  
  const size = parseSizeFromClass(className);
  const classNameWithoutSize = className?.replace(/text-\[\d+px\]|text-(xs|sm|base|lg|xl|2xl|3xl|4xl)/g, '').trim() || '';
  
  // Ensure color is always applied (default to white)
  const hasColorClass = /text-|fill-|stroke-|color-/.test(classNameWithoutSize);
  const finalClassName = cn(
    'inline-block',
    classNameWithoutSize,
    !hasColorClass && 'text-white'
  );
  
  // Always return the icon component, never text
  return <IconComponent size={size} className={finalClassName} />;
}

export function SurfaceCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('rounded-3xl border border-white/5 bg-[var(--surface-low)]', className)}>
      {children}
    </div>
  );
}

export function StatChip({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: ReactNode;
  tone?: 'positive' | 'negative' | 'neutral';
}) {
  const toneClass =
    tone === 'positive'
      ? 'text-secondary'
      : tone === 'negative'
        ? 'text-tertiary'
        : 'text-[var(--on-surface)]';

  return (
    <div className="rounded-2xl bg-black/15 px-4 py-4">
      <p className="mb-1 text-[11px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">{label}</p>
      <p className={cn('font-mono text-[28px] leading-none', toneClass)}>{value}</p>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn('animate-pulse rounded bg-gray-300/20', className)} />
  );
}
