/**
 * useDashboard Hook
 *
 * Manages dashboard data fetching and state
 */

import { useState, useEffect, useRef, useCallback } from "react";
import {
  getDashboardData,
  refreshDashboard,
} from "@/services/dashboardService";
import { wsManager } from "@/services/websocket";
import type { DashboardResponse } from "@/types/api";

interface UseDashboardOptions {
  repo_id?: string;
  autoFetch?: boolean;
}

interface UseDashboardReturn {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  analysing: boolean; // true when analysis is still running (all zeros)
  refetch: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Returns true when the dashboard response looks like analysis hasn't
 * produced results yet (all counts are zero or missing).
 */
function isAnalysisPending(data: DashboardResponse | null): boolean {
  if (!data) return true;
  const services = data.services ?? 0;
  const fragCount = Array.isArray(data.fragile_services)
    ? data.fragile_services.length
    : 0;
  return services === 0 && fragCount === 0;
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
  // Track whether we're in a poll-until-ready state
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getDashboardData(repo_id);
      setData(result);

      // If analysis is done (non-zero data received), stop polling
      if (!isAnalysisPending(result)) {
        stopPolling();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch dashboard data";
      setError(errorMessage);
      console.error("[useDashboard] Error:", err);
    } finally {
      setLoading(false);
    }
  }, [repo_id]);

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
  }, [repo_id, autoFetch, fetchData]);

  // Subscribe to websocket events for live updates
  useEffect(() => {
    if (!repo_id) return;

    try {
      wsManager.connect(repo_id);
    } catch (err) {
      console.error("[useDashboard] ws connect error:", err);
    }

    const unsub = wsManager.onAny((evt) => {
      try {
        const evtRepo =
          evt.data?.repo_id ||
          evt.data?.RepoID ||
          evt.data?.repoId;
        // Re-fetch on any event matching our repo, or on analysis_complete for any repo
        if (
          !evtRepo ||
          evtRepo === repo_id ||
          evt.data?.event === "analysis_complete"
        ) {
          fetchData();
        }
      } catch (e) {
        console.error("[useDashboard] onAny handler error:", e);
      }
    });

    return () => {
      unsub();
    };
  }, [repo_id, fetchData]);

  // Fallback polling: if data is still pending (analysis running), poll every 8s
  useEffect(() => {
    if (data !== null && isAnalysisPending(data) && pollRef.current === null) {
      console.log("[useDashboard] Analysis pending — starting poll every 8s");
      pollRef.current = setInterval(() => {
        fetchData();
      }, 8000);
    }

    if (data !== null && !isAnalysisPending(data)) {
      stopPolling();
    }

    return stopPolling;
  }, [data, fetchData]);

  return {
    data,
    loading,
    error,
    analysing: isAnalysisPending(data),
    refetch: fetchData,
    refresh,
  };
}

// Made with Bob
