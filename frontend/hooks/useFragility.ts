/**
 * useFragility Hook
 *
 * Manages fragility analysis data fetching and state
 */

import { useState, useEffect, useRef, useCallback } from "react";
import {
  getFragilityAnalysis,
  regenerateFragilityAnalysis,
} from "@/services/fragilityService";
import { wsManager } from "@/services/websocket";
import type { FragilityResponse } from "@/types/api";

interface UseFragilityOptions {
  repo_id?: string;
  autoFetch?: boolean;
}

interface UseFragilityReturn {
  data: FragilityResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  regenerate: () => Promise<void>;
}

/**
 * Hook for managing fragility analysis data
 */
export function useFragility(
  options: UseFragilityOptions = {},
): UseFragilityReturn {
  const {
    repo_id = typeof window !== "undefined"
      ? localStorage.getItem("current_repo_id") || "demo_repo"
      : "demo_repo",
    autoFetch = true,
  } = options;

  const [data, setData] = useState<FragilityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      const result = await getFragilityAnalysis(repo_id);
      setData(result);
      if (result && Array.isArray(result.fragility_scores) && result.fragility_scores.length > 0) {
        stopPolling();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch fragility data";
      setError(errorMessage);
      console.error("[useFragility] Error:", err);
    } finally {
      setLoading(false);
    }
  }, [repo_id]);

  const regenerate = async () => {
    try {
      await regenerateFragilityAnalysis(repo_id);
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to regenerate fragility analysis";
      setError(errorMessage);
      console.error("[useFragility] Regenerate error:", err);
    }
  };

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [repo_id, autoFetch, fetchData]);

  // Subscribe to websocket events
  useEffect(() => {
    if (!repo_id) return;
    try {
      wsManager.connect(repo_id);
    } catch (err) {
      console.error("[useFragility] ws connect error:", err);
    }

    const unsub = wsManager.onAny((evt) => {
      fetchData();
    });

    return () => unsub();
  }, [repo_id, fetchData]);

  // Fallback polling if empty
  useEffect(() => {
    if (data !== null && (!data.fragility_scores || data.fragility_scores.length === 0) && pollRef.current === null) {
      pollRef.current = setInterval(() => {
        fetchData();
      }, 5000);
    }
    return stopPolling;
  }, [data, fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    regenerate,
  };
}

// Made with Bob
