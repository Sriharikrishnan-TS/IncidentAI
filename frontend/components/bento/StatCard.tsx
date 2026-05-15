"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { BentoCard } from "./BentoCard";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
  variant?: "default" | "warning" | "success" | "danger";
}

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp,
  variant = "default",
}: StatCardProps) {
  const variantStyles = {
    default: {
      gradient: "from-blue-500/10 via-purple-500/5 to-transparent",
      border: "border-blue-500/20",
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-400",
      glow: "group-hover:shadow-blue-500/20",
    },
    warning: {
      gradient: "from-orange-500/10 via-yellow-500/5 to-transparent",
      border: "border-orange-500/20",
      iconBg: "bg-orange-500/10",
      iconColor: "text-orange-400",
      glow: "group-hover:shadow-orange-500/20",
    },
    success: {
      gradient: "from-emerald-500/10 via-green-500/5 to-transparent",
      border: "border-emerald-500/20",
      iconBg: "bg-emerald-500/10",
      iconColor: "text-emerald-400",
      glow: "group-hover:shadow-emerald-500/20",
    },
    danger: {
      gradient: "from-red-500/10 via-pink-500/5 to-transparent",
      border: "border-red-500/20",
      iconBg: "bg-red-500/10",
      iconColor: "text-red-400",
      glow: "group-hover:shadow-red-500/20",
    },
  };

  const styles = variantStyles[variant];

  return (
    <BentoCard
      className={`bg-gradient-to-br ${styles.gradient} ${styles.border} ${styles.glow}`}
      glow
    >
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-400">{title}</p>
            <motion.p
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="mt-2 text-3xl font-bold text-slate-100"
            >
              {value}
            </motion.p>
            {trend && (
              <div className="mt-2 flex items-center gap-1">
                <span
                  className={`text-xs font-medium ${
                    trendUp === undefined
                      ? "text-slate-500"
                      : trendUp
                        ? "text-emerald-400"
                        : "text-red-400"
                  }`}
                >
                  {trend}
                </span>
              </div>
            )}
          </div>
          <motion.div
            whileHover={{ rotate: 360, scale: 1.1 }}
            transition={{ duration: 0.6 }}
            className={`rounded-lg ${styles.iconBg} p-3 ring-1 ring-slate-700/50`}
          >
            <Icon className={`h-6 w-6 ${styles.iconColor}`} />
          </motion.div>
        </div>
      </div>
    </BentoCard>
  );
}

// Made with Bob
