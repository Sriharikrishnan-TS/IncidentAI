/**
 * useDashboard Hook
 *
 * Manages dashboard data fetching and state
 */

import { useState, useEffect } from "react";
import {
  getDashboardData,
  refreshDashboard,
} from "@/services/dashboardService";
import type { DashboardResponse } from "@/types/api";

interface UseDashboardOptions {
  repo_id?: string;
  autoFetch?: boolean;
}

interface UseDashboardReturn {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Hook for managing dashboard data
 */
export function useDashboard(
  options: UseDashboardOptions = {},
): UseDashboardReturn {
  const {
    repo_id = typeof window !== "undefined"
      ? localStorage.getItem("current_repo_id") || "demo_repo"
      : "demo_repo",
    autoFetch = true,
  } = options;

  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getDashboardData(repo_id);
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch dashboard data";
      setError(errorMessage);
      console.error("[useDashboard] Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    try {
      await refreshDashboard(repo_id);
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to refresh dashboard";
      setError(errorMessage);
      console.error("[useDashboard] Refresh error:", err);
    }
  };

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [repo_id, autoFetch]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    refresh,
  };
}

// Made with Bob
