# IncidentOS Frontend Implementation Guide

## Dependencies to Install

```bash
# Core dependencies
npm install framer-motion recharts reactflow lucide-react

# shadcn/ui components (install via CLI)
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add separator
```

## TypeScript Type Definitions

### API Contract Types (`types/api.ts`)

```typescript
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

// Investigation API
export interface StartInvestigationRequest {
  repo_id: string;
  incident: string;
}

export interface InvestigationResponse {
  root_cause: string;
  confidence: number;
  affected_services: string[];
  recommended_actions: string[];
  timeline?: TimelineEvent[];
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  type: "commit" | "deploy" | "incident" | "fix";
  details?: string;
}

// Fragility API
export interface FragilityScore {
  service: string;
  score: number;
  reasons: string[];
  metrics?: {
    commit_churn: number;
    dependency_centrality: number;
    test_coverage: number;
  };
}

export interface FragilityResponse {
  fragility_scores: FragilityScore[];
}
```

## Mock Data Service (`services/mockData.ts`)

```typescript
import type {
  DashboardResponse,
  DependencyGraphResponse,
  FragilityResponse,
  InvestigationResponse,
  MentorQueryResponse,
  UploadRepoResponse,
} from "@/types/api";

export const mockUploadRepo = async (
  repo_url: string,
): Promise<UploadRepoResponse> => {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 1500));

  return {
    repo_id: `repo_${Date.now()}`,
    status: "uploaded",
  };
};

export const mockDashboardData = async (
  repo_id: string,
): Promise<DashboardResponse> => {
  await new Promise((resolve) => setTimeout(resolve, 800));

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
    ],
  };
};

export const mockDependencyGraph = async (
  repo_id: string,
): Promise<DependencyGraphResponse> => {
  await new Promise((resolve) => setTimeout(resolve, 1000));

  return {
    nodes: [
      { id: "auth-service", type: "service" },
      { id: "checkout-service", type: "service" },
      { id: "user-service", type: "service" },
      { id: "order-service", type: "service" },
      { id: "payment-gateway", type: "service" },
      { id: "postgres", type: "database" },
      { id: "redis", type: "database" },
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
    ],
  };
};

export const mockMentorQuery = async (
  repo_id: string,
  question: string,
): Promise<MentorQueryResponse> => {
  await new Promise((resolve) => setTimeout(resolve, 1200));

  return {
    answer:
      "Start with auth-service because it is central to the architecture and has high fragility. Understanding its authentication flow will help you grasp how other services interact with it.",
    confidence: 0.89,
    sources: ["auth-service/README.md", "docs/architecture.md"],
  };
};

export const mockInvestigation = async (
  repo_id: string,
  incident: string,
): Promise<InvestigationResponse> => {
  await new Promise((resolve) => setTimeout(resolve, 2000));

  return {
    root_cause: "JWT validation regression in auth-service v2.3.1",
    confidence: 0.87,
    affected_services: ["auth-service", "checkout-service", "user-service"],
    recommended_actions: [
      "Rollback auth-service to v2.3.0",
      "Add integration tests for JWT validation",
      "Review recent changes in auth middleware",
      "Update documentation for token validation flow",
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
    ],
  };
};

export const mockFragilityData = async (
  repo_id: string,
): Promise<FragilityResponse> => {
  await new Promise((resolve) => setTimeout(resolve, 900));

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
    ],
  };
};
```

## Component Specifications

### Sidebar Component

**Features:**

- Fixed left sidebar (256px width)
- Navigation links with icons (Lucide React)
- Active state highlighting
- Repository selector
- Collapsible on mobile

**Navigation Items:**

- Upload (Upload icon)
- Dashboard (LayoutDashboard icon)
- Fragility (AlertTriangle icon)
- Graphs (Network icon)
- Mentor (MessageSquare icon)
- Investigation (Search icon)

### Navbar Component

**Features:**

- Fixed top bar (64px height)
- Logo/branding on left
- Search bar in center (optional)
- User avatar/menu on right
- Glassmorphism background

### Dashboard Page Layout

**Sections:**

1. **Stats Row** (3-4 cards)
   - Total Services
   - Total Dependencies
   - Active Incidents
   - Average Fragility Score

2. **Fragile Services** (Card with list)
   - Service name
   - Score (0-10) with color coding
   - Reason badge
   - Click to view details

3. **Recent Incidents** (Card with list)
   - Incident title
   - Severity badge
   - Affected services
   - Timestamp

4. **Dependency Overview** (Visual chart)
   - Bar chart or pie chart
   - Service distribution

### Upload Page

**Features:**

- Large drag-and-drop zone
- URL input field
- Upload button
- Progress indicator
- Success/error messages

### Fragility Page

**Features:**

- Service list with scores
- Bar chart visualization (Recharts)
- Sorting controls (by score, name)
- Filter by score range
- Detailed metrics on click

### Graphs Page

**Features:**

- React Flow canvas
- Custom node styling (different colors for service types)
- Interactive nodes (click to show details)
- Zoom controls
- Minimap
- Legend

### Mentor Page

**Features:**

- Chat message list
- User messages (right, blue)
- AI messages (left, gray)
- Input field with send button
- Suggested questions as chips
- Typing indicator

### Investigation Page

**Features:**

- Incident input form
- Timeline visualization
- Root cause card
- Confidence score
- Affected services list
- Recommended actions checklist

## Styling Guidelines

### Glassmorphism Effect

```css
.glass-card {
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.1);
}
```

### Gradient Accents

```css
.gradient-border {
  border-image: linear-gradient(135deg, #3b82f6, #8b5cf6) 1;
}

.gradient-text {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Score Color Coding

- **0-3**: emerald-500 (low risk)
- **4-6**: yellow-500 (medium risk)
- **7-8**: orange-500 (high risk)
- **9-10**: red-500 (critical risk)

## Animation Patterns

### Page Transitions

```typescript
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};
```

### Card Hover

```typescript
const cardVariants = {
  rest: { scale: 1 },
  hover: { scale: 1.02, transition: { duration: 0.2 } },
};
```

### Stagger Children

```typescript
const containerVariants = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};
```

## Custom Hooks Pattern

```typescript
export function useDashboard(repoId: string) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const result = await mockDashboardData(repoId);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [repoId]);

  return { data, loading, error };
}
```

## Implementation Order

1. **Foundation** (Day 1)
   - Install dependencies
   - Create type definitions
   - Set up mock data services

2. **Layout** (Day 1-2)
   - Build Sidebar
   - Build Navbar
   - Update root layout

3. **Core Components** (Day 2)
   - shadcn/ui components
   - Custom Card component
   - LoadingSkeleton
   - Badge

4. **Pages** (Day 2-3)
   - Upload page
   - Dashboard page
   - Fragility page
   - Graphs page
   - Mentor page
   - Investigation page

5. **Polish** (Day 3-4)
   - Animations
   - Responsive design
   - Error handling
   - Testing

## Testing Checklist

- [ ] All pages load without errors
- [ ] Navigation works correctly
- [ ] Mock data displays properly
- [ ] Loading states show correctly
- [ ] Responsive on mobile/tablet
- [ ] Animations are smooth
- [ ] Dark theme looks good
- [ ] All interactive elements work
- [ ] Error states display properly
- [ ] TypeScript compiles without errors

## Performance Optimization

- Use React.memo for expensive components
- Lazy load React Flow and Recharts
- Optimize images with Next.js Image
- Code split by route
- Use loading skeletons for better perceived performance

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus indicators
- Color contrast compliance
- Screen reader friendly

This guide provides all the specifications needed to implement the IncidentOS frontend efficiently and consistently.
