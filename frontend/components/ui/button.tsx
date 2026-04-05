'use client';

import { ReactNode, ButtonHTMLAttributes, isValidElement, cloneElement } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  fullWidth?: boolean;
  asChild?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  fullWidth = false,
  asChild = false,
  className,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const baseStyles = 'font-medium rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg hover:shadow-xl hover:shadow-emerald-500/20',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    success: 'bg-emerald-500 hover:bg-emerald-600 text-white',
    outline: 'border border-slate-600 hover:border-slate-500 text-slate-300 hover:bg-slate-800/50',
    ghost: 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const buttonClass = clsx(
    baseStyles,
    variants[variant],
    sizes[size],
    fullWidth && 'w-full',
    className
  );

  // If asChild is true and children is a valid element, clone it with button styles
  if (asChild && isValidElement(children)) {
    return cloneElement(children, {
      className: clsx(buttonClass, children.props.className),
      ...props,
    } as any);
  }

  return (
    <button
      className={buttonClass}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-white"></div>
      )}
      {children}
    </button>
  );
}

export function IconButton({
  variant = 'secondary',
  size = 'md',
  className,
  children,
  ...props
}: Omit<ButtonProps, 'children'> & { children: ReactNode }) {
  const sizes = {
    sm: 'p-1.5 text-sm',
    md: 'p-2 text-base',
    lg: 'p-3 text-lg',
  };

  return (
    <Button
      variant={variant}
      className={clsx('rounded-full', sizes[size], className)}
      {...props}
    >
      {children}
    </Button>
  );
}

