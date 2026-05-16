/**
 * Graph Service
 *
 * Handles dependency graph data fetching and operations
 */

import { apiClient } from "./api";
import { mockDependencyGraph } from "./mockData";
import type { DependencyGraphResponse } from "@/types/api";

/**
 * Get dependency graph for a repository
 */
export async function getDependencyGraph(
  repo_id: string,
): Promise<DependencyGraphResponse> {
  if (apiClient.isMockMode()) {
    return mockDependencyGraph(repo_id);
  }

  return apiClient.get<DependencyGraphResponse>(`/api/graph/${repo_id}`);
}

/**
 * Get node details from the graph
 */
export async function getNodeDetails(
  repo_id: string,
  node_id: string,
): Promise<{
  id: string;
  type: string;
  metadata?: Record<string, any>;
}> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      id: node_id,
      type: "service",
      metadata: {
        description: `Details for ${node_id}`,
        version: "1.0.0",
      },
    };
  }

  return apiClient.get(`/api/graph/${repo_id}/nodes/${node_id}`);
}

/**
 * Regenerate dependency graph
 */
export async function regenerateGraph(
  repo_id: string,
): Promise<{ status: string; message: string }> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return {
      status: "success",
      message: "Graph regeneration initiated",
    };
  }

  return apiClient.post(`/api/graph/${repo_id}/regenerate`);
}

// Made with Bob
