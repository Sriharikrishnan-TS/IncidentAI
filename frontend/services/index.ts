/**
 * Services Index
 *
 * Central export point for all service modules
 */

// API Client
export { apiClient, API_CONFIG, ApiError } from "./api";

// Service Modules
export * from "./repoService";
export * from "./dashboardService";
export * from "./graphService";
export * from "./mentorService";
export * from "./investigationService";
export * from "./fragilityService";

// WebSocket
export { wsManager } from "./websocket";
export type {
  WebSocketEvent,
  WebSocketEventType,
  EventHandler,
} from "./websocket";

// Made with Bob
