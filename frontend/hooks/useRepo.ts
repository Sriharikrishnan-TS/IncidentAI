/**
 * useRepo Hook
 *
 * Manages repository upload and status operations
 */

import { useState, useCallback } from "react";
import { uploadRepository, getRepositoryStatus } from "@/services/repoService";
import { wsManager } from "@/services/websocket";
import type { UploadRepoResponse } from "@/types/api";

interface UseRepoReturn {
  uploadResult: UploadRepoResponse | null;
  uploading: boolean;
  error: string | null;
  upload: (repo_url: string) => Promise<UploadRepoResponse | null>;
  reset: () => void;
}

/**
 * Hook for managing repository operations
 */
export function useRepo(): UseRepoReturn {
  const [uploadResult, setUploadResult] = useState<UploadRepoResponse | null>(
    null,
  );
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (repo_url: string): Promise<UploadRepoResponse | null> => {
      if (!repo_url.trim()) {
        setError("Please enter a repository URL");
        return null;
      }

      setUploading(true);
      setError(null);

      try {
        const result = await uploadRepository(repo_url);
        setUploadResult(result);

        // Store repo_id in localStorage for demo purposes
        if (typeof window !== "undefined") {
          localStorage.setItem("current_repo_id", result.repo_id);
          // Ensure frontend joins the repo-specific WebSocket room
          try {
            wsManager.connect(result.repo_id);
          } catch (err) {
            console.error("[useRepo] Failed to connect websocket:", err);
          }
        }

        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to upload repository";
        setError(errorMessage);
        console.error("[useRepo] Upload error:", err);
        return null;
      } finally {
        setUploading(false);
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setUploadResult(null);
    setError(null);
  }, []);

  return {
    uploadResult,
    uploading,
    error,
    upload,
    reset,
  };
}

/**
 * Hook for checking repository status
 */
export function useRepoStatus(repo_id: string | null) {
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    if (!repo_id) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getRepositoryStatus(repo_id);
      setStatus(result.status);
      setProgress(result.progress || 0);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to get repository status";
      setError(errorMessage);
      console.error("[useRepoStatus] Error:", err);
    } finally {
      setLoading(false);
    }
  }, [repo_id]);

  return {
    status,
    progress,
    loading,
    error,
    checkStatus,
  };
}

// Made with Bob
