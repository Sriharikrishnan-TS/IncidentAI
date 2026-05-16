/**
 * Dashboard Service
 *
 * Handles dashboard data fetching and aggregation
 */

import { apiClient } from "./api";
import { mockDashboardData } from "./mockData";
import type { DashboardResponse } from "@/types/api";

/**
 * Get dashboard data for a repository
 */
export async function getDashboardData(
  repo_id: string,
): Promise<DashboardResponse> {
  if (apiClient.isMockMode()) {
    return mockDashboardData(repo_id);
  }

  return apiClient.get<DashboardResponse>(`/api/dashboard/${repo_id}`);
}

/**
 * Refresh dashboard data (trigger re-analysis)
 */
export async function refreshDashboard(
  repo_id: string,
): Promise<{ status: string; message: string }> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      status: "success",
      message: "Dashboard refresh initiated",
    };
  }

  return apiClient.post(`/api/dashboard/${repo_id}/refresh`);
}

// Made with Bob
