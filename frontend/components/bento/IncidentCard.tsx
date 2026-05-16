"use client";

import { motion } from "framer-motion";
import { AlertCircle, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { BentoCard, BentoCardContent } from "./BentoCard";
import { getSeverityColor, formatTimestamp } from "@/lib/constants";
import type { Incident } from "@/types/api";

interface IncidentCardProps {
  incident: Incident;
  index?: number;
}

export function IncidentCard({ incident, index = 0 }: IncidentCardProps) {
  const getSeverityGradient = (severity: string) => {
    switch (severity) {
      case "critical":
        return "from-red-500/20 to-pink-500/10 border-red-500/30";
      case "high":
        return "from-orange-500/20 to-red-500/10 border-orange-500/30";
      case "medium":
        return "from-yellow-500/20 to-orange-500/10 border-yellow-500/30";
      default:
        return "from-blue-500/20 to-slate-500/10 border-blue-500/30";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
    >
      <BentoCard
        className={`bg-gradient-to-br ${getSeverityGradient(incident.severity)}`}
        glow
      >
        <BentoCardContent className="py-4">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
              className="rounded-lg bg-slate-800/50 p-2 ring-1 ring-slate-700/50"
            >
              <AlertCircle className="h-5 w-5 text-red-400" />
            </motion.div>

            {/* Content */}
            <div className="flex-1 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <h3 className="font-semibold text-slate-100">
                  {incident.title}
                </h3>
                <Badge className={getSeverityColor(incident.severity)}>
                  {incident.severity}
                </Badge>
              </div>

              {/* Affected Services */}
              <div className="flex flex-wrap gap-1.5">
                {incident.affected_services.map((service, idx) => (
                  <motion.div
                    key={service}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 + 0.3 + idx * 0.05 }}
                  >
                    <Badge
                      variant="outline"
                      className="border-slate-700 bg-slate-800/50 text-xs"
                    >
                      {service}
                    </Badge>
                  </motion.div>
                ))}
              </div>

              {/* Timestamp */}
              {incident.timestamp && (
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Clock className="h-3 w-3" />
                  <span>{formatTimestamp(incident.timestamp)}</span>
                </div>
              )}
            </div>
          </div>
        </BentoCardContent>
      </BentoCard>
    </motion.div>
  );
}

// Made with Bob
