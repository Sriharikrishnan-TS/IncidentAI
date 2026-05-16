/**
 * useInvestigation Hook
 *
 * Manages incident investigation operations and state
 */

import { useState, useCallback } from "react";
import { startInvestigation } from "@/services/investigationService";
import type { InvestigationResponse } from "@/types/api";

interface UseInvestigationOptions {
  repo_id?: string;
}

interface UseInvestigationReturn {
  result: InvestigationResponse | null;
  loading: boolean;
  error: string | null;
  investigate: (incident: string) => Promise<void>;
  reset: () => void;
}

/**
 * Hook for managing incident investigations
 */
export function useInvestigation(
  options: UseInvestigationOptions = {},
): UseInvestigationReturn {
  const {
    repo_id = typeof window !== "undefined"
      ? localStorage.getItem("current_repo_id") || "demo_repo"
      : "demo_repo",
  } = options;

  const [result, setResult] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const investigate = useCallback(
    async (incident: string) => {
      if (!incident.trim()) {
        setError("Please provide incident details");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await startInvestigation(repo_id, incident);
        setResult(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Investigation failed";
        setError(errorMessage);
        console.error("[useInvestigation] Error:", err);
      } finally {
        setLoading(false);
      }
    },
    [repo_id],
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    result,
    loading,
    error,
    investigate,
    reset,
  };
}

// Made with Bob
