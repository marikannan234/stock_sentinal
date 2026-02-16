import { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({
  children,
  className,
  variant = "primary",
  ...rest
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 disabled:cursor-not-allowed disabled:opacity-60";

  const variants: Record<typeof variant, string> = {
    primary: "bg-emerald-500 text-slate-950 hover:bg-emerald-400 active:bg-emerald-600",
    secondary:
      "border border-slate-700 bg-slate-800/60 text-slate-100 hover:bg-slate-800 hover:border-slate-600",
    ghost: "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200",
  } as const;

  return (
    <button className={clsx(base, variants[variant], className)} {...rest}>
      {children}
    </button>
  );
}

