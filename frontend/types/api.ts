// API Contract Types for IncidentOS

// Upload Repo API
export interface UploadRepoRequest {
  repo_url: string;
}

export interface UploadRepoResponse {
  repo_id: string;
  status: "uploaded" | "processing" | "failed";
}

// Dashboard API
export interface FragileService {
  service: string;
  score: number;
  reason: string;
}

export interface Incident {
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  affected_services: string[];
  timestamp?: string;
}

export interface DashboardResponse {
  repo_id: string;
  services: number;
  dependencies: number;
  fragile_services: FragileService[];
  recent_incidents: Incident[];
}

// Dependency Graph API
export interface GraphNode {
  id: string;
  type: "service" | "library" | "database";
}

export interface GraphEdge {
  source: string;
  target: string;
  type?: "depends_on" | "calls" | "imports";
}

export interface DependencyGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Mentor Query API
export interface MentorQueryRequest {
  repo_id: string;
  question: string;
}

export interface MentorQueryResponse {
  answer: string;
  confidence?: number;
  sources?: string[];
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  message: string;
  timestamp: string;
}

// Investigation API
export interface StartInvestigationRequest {
  repo_id: string;
  incident: string;
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  type: "commit" | "deploy" | "incident" | "fix";
  details?: string;
}

export interface InvestigationResponse {
  root_cause: string;
  confidence: number;
  affected_services: string[];
  recommended_actions: string[];
  timeline?: TimelineEvent[];
}

// Fragility API
export interface FragilityMetrics {
  commit_churn: number;
  dependency_centrality: number;
  test_coverage: number;
}

export interface FragilityScore {
  service: string;
  score: number;
  reasons: string[];
  metrics?: FragilityMetrics;
}

export interface FragilityResponse {
  fragility_scores: FragilityScore[];
}

// Made with Bob
