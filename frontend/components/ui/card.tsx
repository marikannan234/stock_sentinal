'use client';

import { ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  noPadding?: boolean;
  onClick?: () => void;
}

export function Card({ children, className, hover = false, noPadding = false, onClick }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-slate-900 border border-slate-700 rounded-2xl backdrop-blur-xl',
        'transition-all duration-200',
        hover && 'hover:border-slate-600 hover:shadow-lg hover:shadow-slate-950/50',
        !noPadding && 'p-6',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

interface GradientCardProps extends CardProps {
  gradient?: 'emerald' | 'blue' | 'amber' | 'red';
}

export function GradientCard({
  children,
  gradient = 'emerald',
  className,
  ...props
}: GradientCardProps) {
  const gradients = {
    emerald: 'from-emerald-500/10 to-emerald-900/10 border-emerald-500/20',
    blue: 'from-blue-500/10 to-blue-900/10 border-blue-500/20',
    amber: 'from-amber-500/10 to-amber-900/10 border-amber-500/20',
    red: 'from-red-500/10 to-red-900/10 border-red-500/20',
  };

  return (
    <div
      className={clsx(
        'bg-gradient-to-br',
        gradients[gradient],
        'border rounded-2xl backdrop-blur-xl transition-all duration-200 p-6',
        'hover:shadow-lg hover:shadow-slate-950/50',
        className
      )}
    >
      {children}
    </div>
  );
}

