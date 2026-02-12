import { ReactNode } from "react";
import clsx from "clsx";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-xl border border-slate-800 bg-card/80 p-4 shadow-sm backdrop-blur",
        className,
      )}
    >
      {children}
    </div>
  );
}

