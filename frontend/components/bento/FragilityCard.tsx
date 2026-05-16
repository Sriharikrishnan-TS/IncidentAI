"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { BentoCard, BentoCardContent, BentoCardHeader } from "./BentoCard";
import { getScoreColor } from "@/lib/constants";

interface FragilityCardProps {
  service: string;
  score: number;
  reasons: string[];
  metrics?: {
    commit_churn: number;
    dependency_centrality: number;
    test_coverage: number;
  };
  index?: number;
}

export function FragilityCard({
  service,
  score,
  reasons,
  metrics,
  index = 0,
}: FragilityCardProps) {
  const getRiskLevel = (score: number) => {
    if (score >= 7)
      return {
        level: "High",
        color: "from-red-500/20 to-orange-500/10",
        border: "border-red-500/30",
      };
    if (score >= 4)
      return {
        level: "Medium",
        color: "from-yellow-500/20 to-orange-500/10",
        border: "border-yellow-500/30",
      };
    return {
      level: "Low",
      color: "from-emerald-500/20 to-green-500/10",
      border: "border-emerald-500/30",
    };
  };

  const risk = getRiskLevel(score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
    >
      <BentoCard
        className={`bg-gradient-to-br ${risk.color} ${risk.border}`}
        glow
      >
        <BentoCardHeader
          title={service}
          icon={<AlertTriangle className="h-5 w-5 text-orange-400" />}
          badge={
            <div className="text-right">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 + 0.3, type: "spring" }}
                className={`text-4xl font-bold ${getScoreColor(score)}`}
              >
                {score.toFixed(1)}
              </motion.div>
              <div className="text-sm text-slate-500">/ 10</div>
            </div>
          }
        />
        <BentoCardContent>
          {/* Reasons */}
          <div className="mb-4 flex flex-wrap gap-2">
            {reasons.map((reason, idx) => (
              <motion.div
                key={reason}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 + 0.2 + idx * 0.05 }}
              >
                <Badge
                  variant="outline"
                  className="border-slate-700 bg-slate-800/50 text-xs"
                >
                  {reason}
                </Badge>
              </motion.div>
            ))}
          </div>

          {/* Metrics */}
          {metrics && (
            <div className="space-y-3">
              <MetricBar
                label="Commit Churn"
                value={metrics.commit_churn}
                max={50}
                color="blue"
                delay={index * 0.1 + 0.4}
              />
              <MetricBar
                label="Dependency Centrality"
                value={metrics.dependency_centrality * 100}
                max={100}
                color="purple"
                delay={index * 0.1 + 0.5}
              />
              <MetricBar
                label="Test Coverage"
                value={metrics.test_coverage}
                max={100}
                color="emerald"
                delay={index * 0.1 + 0.6}
              />
            </div>
          )}
        </BentoCardContent>
      </BentoCard>
    </motion.div>
  );
}

interface MetricBarProps {
  label: string;
  value: number;
  max: number;
  color: "blue" | "purple" | "emerald";
  delay?: number;
}

function MetricBar({ label, value, max, color, delay = 0 }: MetricBarProps) {
  const percentage = (value / max) * 100;
  const colorClasses = {
    blue: "bg-blue-500",
    purple: "bg-purple-500",
    emerald: "bg-emerald-500",
  };

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="font-medium text-slate-300">
          {Math.round(value)}
          {label === "Test Coverage" || label === "Dependency Centrality"
            ? "%"
            : ""}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800/50 ring-1 ring-slate-700/50">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percentage, 100)}%` }}
          transition={{ delay, duration: 0.8, ease: "easeOut" }}
          className={`h-full ${colorClasses[color]}`}
        />
      </div>
    </div>
  );
}

// Made with Bob
