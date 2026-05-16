import type {
  DashboardResponse,
  DependencyGraphResponse,
  FragilityResponse,
  InvestigationResponse,
  MentorQueryResponse,
  UploadRepoResponse,
} from "@/types/api";

// Simulate API delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockUploadRepo = async (
  repo_url: string,
): Promise<UploadRepoResponse> => {
  await delay(1500);

  return {
    repo_id: `repo_${Date.now()}`,
    status: "uploaded",
  };
};

export const mockDashboardData = async (
  repo_id: string,
): Promise<DashboardResponse> => {
  await delay(800);

  return {
    repo_id,
    services: 12,
    dependencies: 38,
    fragile_services: [
      {
        service: "auth-service",
        score: 8.7,
        reason: "high commit churn",
      },
      {
        service: "checkout-service",
        score: 7.9,
        reason: "dependency centrality",
      },
      {
        service: "payment-gateway",
        score: 7.2,
        reason: "low test coverage",
      },
      {
        service: "user-service",
        score: 5.8,
        reason: "moderate complexity",
      },
    ],
    recent_incidents: [
      {
        title: "JWT validation regression",
        severity: "high",
        affected_services: ["auth-service", "checkout-service"],
        timestamp: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        title: "Database connection timeout",
        severity: "critical",
        affected_services: ["user-service", "order-service"],
        timestamp: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        title: "API rate limit exceeded",
        severity: "medium",
        affected_services: ["payment-gateway"],
        timestamp: new Date(Date.now() - 10800000).toISOString(),
      },
    ],
  };
};

export const mockDependencyGraph = async (
  repo_id: string,
): Promise<DependencyGraphResponse> => {
  await delay(1000);

  return {
    nodes: [
      { id: "auth-service", type: "service" },
      { id: "checkout-service", type: "service" },
      { id: "user-service", type: "service" },
      { id: "order-service", type: "service" },
      { id: "payment-gateway", type: "service" },
      { id: "notification-service", type: "service" },
      { id: "postgres", type: "database" },
      { id: "redis", type: "database" },
      { id: "express", type: "library" },
      { id: "jwt-lib", type: "library" },
    ],
    edges: [
      {
        source: "checkout-service",
        target: "auth-service",
        type: "depends_on",
      },
      { source: "checkout-service", target: "payment-gateway", type: "calls" },
      { source: "order-service", target: "user-service", type: "depends_on" },
      { source: "auth-service", target: "postgres", type: "depends_on" },
      { source: "user-service", target: "postgres", type: "depends_on" },
      { source: "auth-service", target: "redis", type: "depends_on" },
      { source: "auth-service", target: "jwt-lib", type: "imports" },
      { source: "checkout-service", target: "express", type: "imports" },
      { source: "notification-service", target: "user-service", type: "calls" },
      { source: "payment-gateway", target: "order-service", type: "calls" },
    ],
  };
};

export const mockMentorQuery = async (
  repo_id: string,
  question: string,
): Promise<MentorQueryResponse> => {
  await delay(1200);

  // Simple response based on question keywords
  let answer =
    "Start with auth-service because it is central to the architecture and has high fragility. Understanding its authentication flow will help you grasp how other services interact with it.";

  if (question.toLowerCase().includes("test")) {
    answer =
      "Focus on improving test coverage for payment-gateway first, as it currently has the lowest coverage at 52%. Start with unit tests for critical payment processing functions.";
  } else if (question.toLowerCase().includes("deploy")) {
    answer =
      "The deployment pipeline uses GitHub Actions. Check the .github/workflows directory for CI/CD configurations. The auth-service has the most frequent deployments.";
  } else if (question.toLowerCase().includes("incident")) {
    answer =
      "Recent incidents show that JWT validation issues in auth-service are causing cascading failures. Review the authentication middleware and add integration tests.";
  }

  return {
    answer,
    confidence: 0.89,
    sources: ["auth-service/README.md", "docs/architecture.md"],
  };
};

export const mockInvestigation = async (
  repo_id: string,
  incident: string,
): Promise<InvestigationResponse> => {
  await delay(2000);

  return {
    root_cause: "JWT validation regression in auth-service v2.3.1",
    confidence: 0.87,
    affected_services: ["auth-service", "checkout-service", "user-service"],
    recommended_actions: [
      "Rollback auth-service to v2.3.0",
      "Add integration tests for JWT validation",
      "Review recent changes in auth middleware",
      "Update documentation for token validation flow",
      "Implement circuit breaker pattern for auth calls",
    ],
    timeline: [
      {
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        event: "Deploy auth-service v2.3.1",
        type: "deploy",
        details: "Updated JWT library to v5.0.0",
      },
      {
        timestamp: new Date(Date.now() - 5400000).toISOString(),
        event: "First authentication failures detected",
        type: "incident",
        details: "Error rate increased to 15%",
      },
      {
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        event: "Incident escalated to critical",
        type: "incident",
        details: "Multiple services affected",
      },
      {
        timestamp: new Date(Date.now() - 1800000).toISOString(),
        event: "Investigation started",
        type: "incident",
        details: "Team analyzing logs and recent changes",
      },
    ],
  };
};

export const mockFragilityData = async (
  repo_id: string,
): Promise<FragilityResponse> => {
  await delay(900);

  return {
    fragility_scores: [
      {
        service: "auth-service",
        score: 8.7,
        reasons: ["high commit churn", "high dependency centrality"],
        metrics: {
          commit_churn: 45,
          dependency_centrality: 0.82,
          test_coverage: 67,
        },
      },
      {
        service: "checkout-service",
        score: 7.9,
        reasons: ["dependency centrality", "complex logic"],
        metrics: {
          commit_churn: 32,
          dependency_centrality: 0.75,
          test_coverage: 71,
        },
      },
      {
        service: "payment-gateway",
        score: 7.2,
        reasons: ["low test coverage", "external dependencies"],
        metrics: {
          commit_churn: 18,
          dependency_centrality: 0.45,
          test_coverage: 52,
        },
      },
      {
        service: "user-service",
        score: 5.8,
        reasons: ["moderate complexity"],
        metrics: {
          commit_churn: 22,
          dependency_centrality: 0.58,
          test_coverage: 78,
        },
      },
      {
        service: "order-service",
        score: 5.3,
        reasons: ["stable codebase"],
        metrics: {
          commit_churn: 12,
          dependency_centrality: 0.42,
          test_coverage: 82,
        },
      },
      {
        service: "notification-service",
        score: 4.1,
        reasons: ["low complexity", "good test coverage"],
        metrics: {
          commit_churn: 8,
          dependency_centrality: 0.28,
          test_coverage: 88,
        },
      },
    ],
  };
};

// Made with Bob
