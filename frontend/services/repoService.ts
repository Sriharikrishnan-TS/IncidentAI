/**
 * Repository Service
 *
 * Handles repository upload and management operations
 */

import { apiClient } from "./api";
import { mockUploadRepo } from "./mockData";
import type { UploadRepoRequest, UploadRepoResponse } from "@/types/api";

/**
 * Upload a repository for analysis
 */
export async function uploadRepository(
  repo_url: string,
): Promise<UploadRepoResponse> {
  if (apiClient.isMockMode()) {
    return mockUploadRepo(repo_url);
  }

  const request: UploadRepoRequest = { repo_url };
  return apiClient.post<UploadRepoResponse>("/upload-repo", request);
}

/**
 * Get repository status
 */
export async function getRepositoryStatus(
  repo_id: string,
): Promise<{ repo_id: string; status: string; progress?: number }> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      repo_id,
      status: "completed",
      progress: 100,
    };
  }

  return apiClient.get(`/api/repos/${repo_id}/status`);
}

/**
 * Delete a repository
 */
export async function deleteRepository(repo_id: string): Promise<void> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return;
  }

  return apiClient.delete(`/api/repos/${repo_id}`);
}

// Made with Bob
