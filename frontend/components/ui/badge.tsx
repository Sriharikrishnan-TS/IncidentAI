import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?:
    | "default"
    | "secondary"
    | "destructive"
    | "outline"
    | "success"
    | "warning"
    | "critical";
}

const variantStyles = {
  default:
    "border-transparent bg-slate-900 text-slate-50 hover:bg-slate-900/80",
  secondary:
    "border-transparent bg-slate-800 text-slate-100 hover:bg-slate-800/80",
  destructive:
    "border-transparent bg-red-500 text-slate-50 hover:bg-red-500/80",
  outline: "text-slate-100 border-slate-700",
  success:
    "border-transparent bg-emerald-500 text-white hover:bg-emerald-500/80",
  warning:
    "border-transparent bg-yellow-500 text-slate-900 hover:bg-yellow-500/80",
  critical: "border-transparent bg-red-500 text-white hover:bg-red-500/80",
};

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variantStyles[variant],
        className,
      )}
      {...props}
    />
  );
}

export { Badge };

// Made with Bob
