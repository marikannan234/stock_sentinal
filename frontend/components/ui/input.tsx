import { InputHTMLAttributes } from "react";
import clsx from "clsx";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

export function Input({ label, error, className, ...rest }: InputProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label && <span className="text-slate-300">{label}</span>}
      <input
        className={clsx(
          "rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 outline-none ring-accent/50 placeholder:text-slate-500 focus:border-accent focus:ring-2",
          className,
        )}
        {...rest}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </label>
  );
}

