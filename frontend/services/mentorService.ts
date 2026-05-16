/**
 * Mentor Service
 *
 * Handles AI mentor query operations
 */

import { apiClient } from "./api";
import { mockMentorQuery } from "./mockData";
import type { MentorQueryRequest, MentorQueryResponse } from "@/types/api";

/**
 * Send a query to the AI mentor
 */
export async function queryMentor(
  repo_id: string,
  question: string,
): Promise<MentorQueryResponse> {
  if (apiClient.isMockMode()) {
    return mockMentorQuery(repo_id, question);
  }

  const request: MentorQueryRequest = { repo_id, question };
  return apiClient.post<MentorQueryResponse>("/api/mentor/query", request);
}

/**
 * Get mentor conversation history
 */
export async function getMentorHistory(repo_id: string): Promise<{
  conversations: Array<{
    id: string;
    question: string;
    answer: string;
    timestamp: string;
  }>;
}> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      conversations: [],
    };
  }

  return apiClient.get(`/api/mentor/${repo_id}/history`);
}

/**
 * Clear mentor conversation history
 */
export async function clearMentorHistory(
  repo_id: string,
): Promise<{ status: string; message: string }> {
  if (apiClient.isMockMode()) {
    // Mock implementation
    await new Promise((resolve) => setTimeout(resolve, 300));
    return {
      status: "success",
      message: "History cleared",
    };
  }

  return apiClient.delete(`/api/mentor/${repo_id}/history`);
}

// Made with Bob
