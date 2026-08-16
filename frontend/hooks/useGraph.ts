/**
 * useGraph Hook
 *
 * Manages dependency graph data fetching and state
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { getDependencyGraph, regenerateGraph } from "@/services/graphService";
import { wsManager } from "@/services/websocket";
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
      const result = await getDependencyGraph(repo_id);
      setData(result);
      if (result && Array.isArray(result.nodes) && result.nodes.length > 0) {
        stopPolling();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch graph data";
      setError(errorMessage);
      console.error("[useGraph] Error:", err);
    } finally {
      setLoading(false);
    }
  }, [repo_id]);

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
  }, [repo_id, autoFetch, fetchData]);

  // Subscribe to websocket events
  useEffect(() => {
    if (!repo_id) return;
    try {
      wsManager.connect(repo_id);
    } catch (err) {
      console.error("[useGraph] ws connect error:", err);
    }

    const unsub = wsManager.onAny((evt) => {
      fetchData();
    });

    return () => unsub();
  }, [repo_id, fetchData]);

  // Fallback polling if empty
  useEffect(() => {
    if (data !== null && (!data.nodes || data.nodes.length === 0) && pollRef.current === null) {
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
