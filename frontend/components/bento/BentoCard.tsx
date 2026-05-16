"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface BentoCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
  glow?: boolean;
}

export function BentoCard({
  children,
  className,
  hover = true,
  gradient = false,
  glow = false,
}: BentoCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={hover ? { scale: 1.02, y: -4 } : {}}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm transition-all duration-300",
        hover &&
          "hover:border-slate-700 hover:shadow-xl hover:shadow-blue-500/10",
        gradient && "bg-gradient-to-br from-slate-900/80 to-slate-800/50",
        glow && "hover:shadow-2xl hover:shadow-purple-500/20",
        className,
      )}
    >
      {/* Radial gradient overlay on hover */}
      {hover && (
        <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100">
          <div className="absolute inset-0 bg-gradient-radial from-blue-500/5 via-transparent to-transparent" />
        </div>
      )}

      {/* Border glow effect */}
      {glow && (
        <div className="pointer-events-none absolute inset-0 rounded-xl opacity-0 transition-opacity duration-500 group-hover:opacity-100">
          <div className="absolute inset-[-1px] rounded-xl bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-blue-500/20 blur-sm" />
        </div>
      )}

      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

interface BentoCardHeaderProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  badge?: ReactNode;
}

export function BentoCardHeader({
  title,
  description,
  icon,
  badge,
}: BentoCardHeaderProps) {
  return (
    <div className="flex items-start justify-between p-6 pb-4">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          {icon && (
            <div className="rounded-lg bg-slate-800/50 p-2 ring-1 ring-slate-700/50">
              {icon}
            </div>
          )}
          <div>
            <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
            {description && (
              <p className="mt-1 text-sm text-slate-400">{description}</p>
            )}
          </div>
        </div>
      </div>
      {badge && <div className="ml-4">{badge}</div>}
    </div>
  );
}

interface BentoCardContentProps {
  children: ReactNode;
  className?: string;
}

export function BentoCardContent({
  children,
  className,
}: BentoCardContentProps) {
  return <div className={cn("px-6 pb-6", className)}>{children}</div>;
}

// Made with Bob
