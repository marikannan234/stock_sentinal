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
    "inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 disabled:cursor-not-allowed disabled:opacity-60";

  const variants: Record<typeof variant, string> = {
    primary: "bg-accent text-black hover:bg-emerald-500",
    secondary:
      "border border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800",
    ghost: "text-slate-300 hover:bg-slate-800/60",
  } as const;

  return (
    <button className={clsx(base, variants[variant], className)} {...rest}>
      {children}
    </button>
  );
}

