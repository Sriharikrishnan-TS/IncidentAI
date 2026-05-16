/**
 * useGraph Hook
 *
 * Manages dependency graph data fetching and state
 */

import { useState, useEffect } from "react";
import { getDependencyGraph, regenerateGraph } from "@/services/graphService";
import type { DependencyGraphResponse } from "@/types/api";

interface UseGraphOptions {
  repo_id?: string;
  autoFetch?: boolean;
}

interface UseGraphReturn {
  data: DependencyGraphResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  regenerate: () => Promise<void>;
}

/**
 * Hook for managing dependency graph data
 */
export function useGraph(options: UseGraphOptions = {}): UseGraphReturn {
  const {
    repo_id = typeof window !== "undefined"
      ? localStorage.getItem("current_repo_id") || "demo_repo"
      : "demo_repo",
    autoFetch = true,
  } = options;

  const [data, setData] = useState<DependencyGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getDependencyGraph(repo_id);
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch graph data";
      setError(errorMessage);
      console.error("[useGraph] Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const regenerate = async () => {
    try {
      await regenerateGraph(repo_id);
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to regenerate graph";
      setError(errorMessage);
      console.error("[useGraph] Regenerate error:", err);
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
