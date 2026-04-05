'use client';

import clsx from 'clsx';

interface BadgeProps {
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info' | 'primary';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = 'default', size = 'md', children, className }: BadgeProps) {
  const variants = {
    default: 'bg-slate-700 text-slate-100',
    success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
    warning: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    primary: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs font-medium rounded',
    md: 'px-3 py-1 text-sm font-medium rounded-lg',
    lg: 'px-4 py-1.5 text-base font-semibold rounded-lg',
  };

  return (
    <span className={clsx(variants[variant], sizes[size], 'inline-block', className)}>
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'triggered' | 'pending' | 'completed';
  childrenchildren?: React.ReactNode;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variants = {
    active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    inactive: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
    triggered: 'bg-red-500/20 text-red-400 border border-red-500/30',
    pending: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    completed: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  };

  const labels = {
    active: '● Active',
    inactive: '● Inactive',
    triggered: '● Triggered',
    pending: '⏳ Pending',
    completed: '✓ Completed',
  };

  return (
    <span className={clsx(variants[status], 'px-3 py-1 text-sm font-medium rounded-lg inline-flex items-center gap-1')}>
      {labels[status]}
    </span>
  );
}
