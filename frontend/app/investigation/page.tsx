"use client";

import { useState } from "react";
import {
  Search,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  GitCommit,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  BentoCard,
  BentoCardHeader,
  BentoCardContent,
} from "@/components/bento";
import { useInvestigation } from "@/hooks/useInvestigation";
import { formatTimestamp } from "@/lib/constants";

export default function InvestigationPage() {
  const [incident, setIncident] = useState("");
  const { result, loading, investigate } = useInvestigation();

  const handleInvestigate = async () => {
    if (!incident.trim()) return;
    await investigate(incident);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Incident Investigation
        </h1>
        <p className="mt-2 text-slate-400">
          AI-powered root cause analysis for your incidents
        </p>
      </motion.div>

      {/* Input Form - Bento Style */}
      <BentoCard gradient glow>
        <BentoCardHeader
          title="Describe the Incident"
          description="Enter details about the incident you want to investigate"
          icon={<Search className="h-5 w-5 text-blue-400" />}
        />
        <BentoCardContent className="space-y-4">
          <textarea
            value={incident}
            onChange={(e) => setIncident(e.target.value)}
            placeholder="e.g., checkout-service CI failed, authentication errors in production..."
            className="w-full resize-none rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
            rows={3}
            disabled={loading}
          />
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              onClick={handleInvestigate}
              disabled={loading || !incident.trim()}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 py-6 shadow-lg shadow-blue-500/20"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Investigating...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-5 w-5" />
                  Start Investigation
                </>
              )}
            </Button>
          </motion.div>
        </BentoCardContent>
      </BentoCard>

      {/* Results - Bento Style */}
      {result && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          {/* Root Cause */}
          <BentoCard
            className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30"
            glow
          >
            <BentoCardHeader
              title="Root Cause Analysis"
              icon={<AlertCircle className="h-5 w-5 text-red-400" />}
            />
            <BentoCardContent className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <p className="text-lg font-medium text-slate-100">
                  {result.root_cause}
                </p>
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-sm text-slate-400">Confidence:</span>
                  <div className="flex-1 max-w-xs">
                    <div className="h-2 overflow-hidden rounded-full bg-slate-800/50 ring-1 ring-slate-700/50">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${result.confidence * 100}%` }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium text-slate-300">
                    {Math.round(result.confidence * 100)}%
                  </span>
                </div>
              </motion.div>

              <div>
                <p className="mb-2 text-sm font-medium text-slate-400">
                  Affected Services:
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.affected_services.map((service, idx) => (
                    <motion.div
                      key={service}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.3 + idx * 0.1 }}
                    >
                      <Badge variant="destructive">{service}</Badge>
                    </motion.div>
                  ))}
                </div>
              </div>
            </BentoCardContent>
          </BentoCard>

          {/* Timeline */}
          {result.timeline && result.timeline.length > 0 && (
            <BentoCard gradient glow>
              <BentoCardHeader
                title="Event Timeline"
                description="Chronological sequence of events leading to the incident"
                icon={<Clock className="h-5 w-5 text-blue-400" />}
              />
              <BentoCardContent>
                <div className="relative space-y-6">
                  {/* Timeline line */}
                  <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500/50 to-purple-500/50" />

                  {result.timeline.map((event, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * idx, duration: 0.5 }}
                      className="relative flex gap-4"
                    >
                      {/* Timeline dot */}
                      <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2 border-slate-700 bg-slate-900 ring-2 ring-slate-800">
                        {event.type === "deploy" && (
                          <GitCommit className="h-5 w-5 text-blue-400" />
                        )}
                        {event.type === "incident" && (
                          <AlertCircle className="h-5 w-5 text-red-400" />
                        )}
                        {event.type === "fix" && (
                          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                        )}
                        {event.type === "commit" && (
                          <GitCommit className="h-5 w-5 text-purple-400" />
                        )}
                      </div>

                      {/* Event content */}
                      <div className="flex-1 rounded-lg border border-slate-800 bg-slate-800/50 p-4 backdrop-blur-sm">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-medium text-slate-100">
                              {event.event}
                            </h3>
                            {event.details && (
                              <p className="mt-1 text-sm text-slate-400">
                                {event.details}
                              </p>
                            )}
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {event.type}
                          </Badge>
                        </div>
                        <p className="mt-2 text-xs text-slate-500">
                          {formatTimestamp(event.timestamp)}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </BentoCardContent>
            </BentoCard>
          )}

          {/* Recommended Actions */}
          <BentoCard
            className="bg-gradient-to-br from-emerald-500/10 to-green-500/10 border-emerald-500/30"
            glow
          >
            <BentoCardHeader
              title="Recommended Actions"
              description="Steps to resolve and prevent similar incidents"
              icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
            />
            <BentoCardContent>
              <ul className="space-y-3">
                {result.recommended_actions.map((action, idx) => (
                  <motion.li
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 * idx, duration: 0.5 }}
                    className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-800/50 p-4 backdrop-blur-sm"
                  >
                    <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-sm font-medium text-emerald-400 ring-1 ring-emerald-500/30">
                      {idx + 1}
                    </div>
                    <p className="flex-1 text-slate-100">{action}</p>
                  </motion.li>
                ))}
              </ul>
            </BentoCardContent>
          </BentoCard>
        </motion.div>
      )}
    </div>
  );
}

// Made with Bob
