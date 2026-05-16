/**
 * Fragility Service
 *
 * Handles fragility analysis operations
 */

import { apiClient } from "./api";
import { mockFragilityData } from "./mockData";
import type { FragilityResponse } from "@/types/api";

/**
 * Get fragility analysis for a repository
 */
export async function getFragilityAnalysis(
  repo_id: string,
): Promise<FragilityResponse> {
  if (apiClient.isMockMode()) {
    return mockFragilityData(repo_id);
  }

  return apiClient.get<FragilityResponse>(`/api/fragility/${repo_id}`);
}

/**
 * Get fragility score for a specific service
 */
export async function getServiceFragility(
  repo_id: string,
  service_name: string,
): Promise<{
  service: string;
  score: number;
  reasons: string[];
  metrics?: {
    commit_churn: number;
    dependency_centrality: number;
    test_coverage: number;
  };
}> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      service: service_name,
      score: 7.5,
      reasons: ["high commit churn", "dependency centrality"],
      metrics: {
        commit_churn: 35,
        dependency_centrality: 0.72,
        test_coverage: 68,
      },
    };
  }

  return apiClient.get(`/api/fragility/${repo_id}/services/${service_name}`);
}

/**
 * Regenerate fragility analysis
 */
export async function regenerateFragilityAnalysis(
  repo_id: string,
): Promise<{ status: string; message: string }> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return {
      status: "success",
      message: "Fragility analysis regeneration initiated",
    };
  }

  return apiClient.post(`/api/fragility/${repo_id}/regenerate`);
}

// Made with Bob
