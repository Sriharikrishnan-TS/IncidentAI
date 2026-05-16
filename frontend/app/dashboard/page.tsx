"use client";

import {
  Server,
  GitBranch,
  AlertTriangle,
  TrendingUp,
  Sparkles,
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
  const { data, loading } = useDashboard();

  if (loading) {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="mt-2 text-slate-400">
          Overview of your repository health and incidents
        </p>
      </motion.div>

      {/* Stats Grid - Bento Style */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Services"
          value={data.services}
          icon={Server}
          trend="+2 this week"
          variant="default"
        />
        <StatCard
          title="Dependencies"
          value={data.dependencies}
          icon={GitBranch}
          trend="+5 this week"
          variant="default"
        />
        <StatCard
          title="Active Incidents"
          value={data.recent_incidents.length}
          icon={AlertTriangle}
          trend="2 resolved"
          variant="warning"
        />
        <StatCard
          title="Avg Fragility"
          value="6.8"
          icon={TrendingUp}
          trend="-0.3 this week"
          variant="success"
        />
      </div>

      {/* Main Content Grid - Bento Layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Fragile Services */}
        <BentoCard gradient glow>
          <BentoCardHeader
            title="Fragile Services"
            description="Services with high fragility scores requiring attention"
            icon={<AlertTriangle className="h-5 w-5 text-orange-400" />}
          />
          <BentoCardContent>
            <div className="space-y-3">
              {data.fragile_services.map((service, idx) => (
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
              ))}
            </div>
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
              {data.recent_incidents.map((incident, idx) => (
                <IncidentCard key={idx} incident={incident} index={idx} />
              ))}
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

// Made with Bob
