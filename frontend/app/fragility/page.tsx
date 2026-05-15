"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, TrendingUp, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { mockFragilityData } from "@/services/mockData";
import { StatCard, FragilityCard } from "@/components/bento";
import type { FragilityResponse } from "@/types/api";

export default function FragilityPage() {
  const [data, setData] = useState<FragilityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"score" | "name">("score");

  useEffect(() => {
    const fetchData = async () => {
      const repoId = localStorage.getItem("current_repo_id") || "demo_repo";
      const result = await mockFragilityData(repoId);
      setData(result);
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-6 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const sortedServices = [...data.fragility_scores].sort((a, b) => {
    if (sortBy === "score") return b.score - a.score;
    return a.service.localeCompare(b.service);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            Fragility Analysis
          </h1>
          <p className="mt-2 text-slate-400">
            Identify and prioritize services that need attention
          </p>
        </div>
        <div className="flex gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSortBy("score")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
              sortBy === "score"
                ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            Sort by Score
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSortBy("name")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
              sortBy === "name"
                ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            Sort by Name
          </motion.button>
        </div>
      </motion.div>

      {/* Overview Stats - Bento Style */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          title="High Risk"
          value={sortedServices.filter((s) => s.score >= 7).length}
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Medium Risk"
          value={
            sortedServices.filter((s) => s.score >= 4 && s.score < 7).length
          }
          icon={TrendingUp}
          variant="warning"
        />
        <StatCard
          title="Low Risk"
          value={sortedServices.filter((s) => s.score < 4).length}
          icon={TrendingDown}
          variant="success"
        />
      </div>

      {/* Service Cards - Bento Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {sortedServices.map((service, idx) => (
          <FragilityCard
            key={service.service}
            service={service.service}
            score={service.score}
            reasons={service.reasons}
            metrics={service.metrics}
            index={idx}
          />
        ))}
      </div>
    </div>
  );
}

// Made with Bob
