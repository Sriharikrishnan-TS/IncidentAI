/**
 * useFragility Hook
 *
 * Manages fragility analysis data fetching and state
 */

import { useState, useEffect } from "react";
import {
  getFragilityAnalysis,
  regenerateFragilityAnalysis,
} from "@/services/fragilityService";
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

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getFragilityAnalysis(repo_id);
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch fragility data";
      setError(errorMessage);
      console.error("[useFragility] Error:", err);
    } finally {
      setLoading(false);
    }
  };

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
  }, [repo_id, autoFetch]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    regenerate,
  };
}

// Made with Bob
