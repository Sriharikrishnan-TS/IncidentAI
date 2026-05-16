/**
 * Investigation Service
 *
 * Handles incident investigation operations
 */

import { apiClient } from "./api";
import { mockInvestigation } from "./mockData";
import type {
  StartInvestigationRequest,
  InvestigationResponse,
} from "@/types/api";

/**
 * Start an incident investigation
 */
export async function startInvestigation(
  repo_id: string,
  incident: string,
): Promise<InvestigationResponse> {
  if (apiClient.isMockMode()) {
    return mockInvestigation(repo_id, incident);
  }

  const request: StartInvestigationRequest = { repo_id, incident };
  return apiClient.post<InvestigationResponse>(
    "/api/investigation/start",
    request,
  );
}

/**
 * Get investigation status
 */
export async function getInvestigationStatus(
  investigation_id: string,
): Promise<{
  id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress?: number;
}> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      id: investigation_id,
      status: "completed",
      progress: 100,
    };
  }

  return apiClient.get(`/api/investigation/${investigation_id}/status`);
}

/**
 * Get investigation history
 */
export async function getInvestigationHistory(repo_id: string): Promise<{
  investigations: Array<{
    id: string;
    incident: string;
    root_cause: string;
    timestamp: string;
  }>;
}> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      investigations: [],
    };
  }

  return apiClient.get(`/api/investigation/${repo_id}/history`);
}

// Made with Bob
