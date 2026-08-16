"use client";

import {
  Server,
  GitBranch,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/useDashboard";
import {
  StatCard,
  FragilityCard,
  IncidentCard,
  BentoCard,
  BentoCardHeader,
  BentoCardContent,
} from "@/components/bento";

export default function DashboardPage() {
  const { data, loading, analysing, refetch } = useDashboard();

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  // Compute average fragility from fragile_services
  const avgFragility =
    Array.isArray(data.fragile_services) && data.fragile_services.length > 0
      ? (
          data.fragile_services.reduce((sum, s) => sum + (s.score || 0), 0) /
          data.fragile_services.length
        ).toFixed(1)
      : "0.0";

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-start justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="mt-2 text-slate-400">
            Overview of your repository health and incidents
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 disabled:opacity-50"
          title="Refresh dashboard data"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Refresh
        </button>
      </motion.div>

      {/* Analysis in Progress Banner */}
      {analysing && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm text-blue-300"
        >
          <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
          <span>
            <strong>Analysis in progress</strong> — AI is scanning your
            repository. This page will auto-update when results are ready (usually
            30–90 seconds).
          </span>
        </motion.div>
      )}

      {/* Stats Grid - Bento Style */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Files / Modules"
          value={data.services}
          icon={Server}
          trend={analysing ? "Scanning…" : "+2 this week"}
          variant="default"
        />

        <StatCard
          title="Dependencies"
          value={data.dependencies}
          icon={GitBranch}
          trend={analysing ? "Mapping…" : "+5 this week"}
          variant="default"
        />

        <StatCard
          title="Active Incidents"
          value={
            Array.isArray(data.recent_incidents)
              ? data.recent_incidents.length
              : data.recent_incidents || 0
          }
          icon={AlertTriangle}
          trend="2 resolved"
          variant="warning"
        />

        <StatCard
          title="Avg Fragility"
          value={avgFragility}
          icon={TrendingUp}
          trend={analysing ? "Calculating…" : "-0.3 this week"}
          variant="success"
        />
      </div>

      {/* Main Content Grid - Bento Layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Fragile Services */}
        <BentoCard gradient glow>
          <BentoCardHeader
            title="Fragile Components"
            description={
              analysing
                ? "Fragility analysis running — results will appear shortly"
                : "Components with high fragility scores requiring attention"
            }
            icon={<AlertTriangle className="h-5 w-5 text-orange-400" />}
          />

          <BentoCardContent>
            {analysing ? (
              <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                <Loader2 className="h-8 w-8 animate-spin text-blue-400 mb-3" />
                <p className="text-sm">Analyzing repository…</p>
              </div>
            ) : (
              <div className="space-y-3">
                {Array.isArray(data.fragile_services) &&
                data.fragile_services.length > 0 ? (
                  data.fragile_services.map((service, idx) => (
                    <motion.div
                      key={service.service}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1, duration: 0.5 }}
                    >
                      <FragilityCard
                        service={service.service}
                        score={service.score}
                        reasons={[service.reason]}
                        index={idx}
                      />
                    </motion.div>
                  ))
                ) : (
                  <p className="py-6 text-center text-sm text-slate-500">
                    No fragile components detected
                  </p>
                )}
              </div>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Recent Incidents */}
        <BentoCard gradient glow>
          <BentoCardHeader
            title="Recent Incidents"
            description="Latest incidents affecting your services"
            icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
          />

          <BentoCardContent>
            <div className="space-y-3">
              {Array.isArray(data.recent_incidents) ? (
                data.recent_incidents.map((incident, idx) => (
                  <IncidentCard key={idx} incident={incident} index={idx} />
                ))
              ) : (
                <p className="py-6 text-center text-sm text-slate-400">
                  {data.recent_incidents || 0} recent incidents
                </p>
              )}
            </div>
          </BentoCardContent>
        </BentoCard>
      </div>

      {/* Quick Actions - Bento Style */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <BentoCard
          className="bg-gradient-to-br from-blue-500/10 via-purple-500/5 to-transparent border-purple-500/20"
          glow
        >
          <BentoCardContent className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="rounded-lg bg-purple-500/10 p-3 ring-1 ring-purple-500/30">
                  <Sparkles className="h-6 w-6 text-purple-400" />
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-100">
                    Need help understanding your codebase?
                  </h3>

                  <p className="mt-1 text-sm text-slate-400">
                    Ask our AI mentor for guidance and insights
                  </p>
                </div>
              </div>

              <motion.a
                href="/mentor"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-6 py-3 font-medium text-white shadow-lg shadow-purple-500/20 transition-shadow hover:shadow-xl hover:shadow-purple-500/30"
              >
                Ask Mentor
              </motion.a>
            </div>
          </BentoCardContent>
        </BentoCard>
      </motion.div>
    </div>
  );
}
