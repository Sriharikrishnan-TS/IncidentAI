# Frontend Integration Architecture

This document describes the clean integration architecture implemented for the IncidentOS frontend.

## Architecture Overview

The frontend follows a layered architecture pattern:

```
Component/Page
   ↓
Custom Hook
   ↓
Service Layer
   ↓
API Client / Mock Data
```

## Layers

### 1. Components/Pages

- **Responsibility**: UI rendering and user interactions
- **What they do**: Display data, handle user input, trigger actions
- **What they DON'T do**: Direct API calls, business logic, state management beyond UI state

**Example:**

```tsx
export default function DashboardPage() {
  const { data, loading } = useDashboard();

  if (loading) return <Skeleton />;
  return <div>{/* Render data */}</div>;
}
```

### 2. Custom Hooks

Located in `/hooks/`

- **Responsibility**: State management and data fetching orchestration
- **What they provide**:
  - Loading states
  - Error states
  - Data state
  - Action methods (refetch, refresh, etc.)

**Available Hooks:**

- `useDashboard()` - Dashboard data
- `useGraph()` - Dependency graph data
- `useMentor()` - AI mentor chat
- `useInvestigation()` - Incident investigation
- `useFragility()` - Fragility analysis
- `useRepo()` - Repository upload
- `useRepoStatus()` - Repository status checking

**Example:**

```tsx
const { data, loading, error, refetch } = useDashboard({
  repo_id: "my-repo",
  autoFetch: true,
});
```

### 3. Service Layer

Located in `/services/`

- **Responsibility**: Business logic and API communication
- **What they do**:
  - Handle API requests
  - Route to mock data in development
  - Transform data if needed
  - Handle service-specific logic

**Available Services:**

- `repoService.ts` - Repository operations
- `dashboardService.ts` - Dashboard data
- `graphService.ts` - Dependency graph
- `mentorService.ts` - AI mentor queries
- `investigationService.ts` - Incident investigation
- `fragilityService.ts` - Fragility analysis

**Example:**

```tsx
export async function getDashboardData(
  repo_id: string,
): Promise<DashboardResponse> {
  if (apiClient.isMockMode()) {
    return mockDashboardData(repo_id);
  }
  return apiClient.get<DashboardResponse>(`/api/dashboard/${repo_id}`);
}
```

### 4. API Client

Located in `/services/api.ts`

- **Responsibility**: Low-level HTTP communication
- **Features**:
  - Unified request/response handling
  - Error handling
  - Timeout management
  - Mock mode support
  - Future backend integration ready

**Configuration:**

```typescript
// Environment variables
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_USE_MOCK=true  // Set to false for real backend
NEXT_PUBLIC_WS_URL=ws://localhost:8080/ws
```

### 5. WebSocket Service

Located in `/services/websocket.ts`

- **Responsibility**: Real-time event handling
- **Features**:
  - Event subscription/unsubscription
  - Automatic reconnection
  - Mock event simulation
  - Type-safe event handling

**Supported Events:**

- `repo_analysis_started`
- `repo_analysis_progress`
- `repo_analysis_complete`
- `dependency_graph_generated`
- `fragility_analysis_complete`
- `investigation_started`
- `investigation_progress`
- `investigation_complete`

**Example:**

```tsx
import { wsManager } from "@/services/websocket";

// Connect
wsManager.connect(repo_id);

// Subscribe to events
const unsubscribe = wsManager.on("repo_analysis_complete", (event) => {
  console.log("Analysis complete:", event.data);
});

// Cleanup
unsubscribe();
wsManager.disconnect();
```

## Data Flow Example

### Fetching Dashboard Data

1. **Component** calls hook:

   ```tsx
   const { data, loading } = useDashboard();
   ```

2. **Hook** manages state and calls service:

   ```tsx
   const result = await getDashboardData(repo_id);
   setData(result);
   ```

3. **Service** routes to appropriate data source:

   ```tsx
   if (apiClient.isMockMode()) {
     return mockDashboardData(repo_id);
   }
   return apiClient.get(`/api/dashboard/${repo_id}`);
   ```

4. **API Client** makes HTTP request (or returns mock):
   ```tsx
   const response = await fetch(url);
   return response.json();
   ```

## Benefits

### 1. Separation of Concerns

- Components focus on UI
- Hooks manage state
- Services handle business logic
- API client handles communication

### 2. Testability

- Each layer can be tested independently
- Easy to mock dependencies
- Clear interfaces between layers

### 3. Maintainability

- Changes in one layer don't affect others
- Easy to locate and fix bugs
- Clear code organization

### 4. Scalability

- Easy to add new features
- Simple to switch from mock to real backend
- WebSocket support for real-time updates

### 5. Developer Experience

- Type-safe throughout
- Consistent patterns
- Clear error handling
- Loading states built-in

## Migration to Real Backend

When the backend is ready:

1. Set environment variable:

   ```
   NEXT_PUBLIC_USE_MOCK=false
   ```

2. Services automatically switch to real API calls

3. No changes needed in components or hooks

4. WebSocket connects to real server

## Best Practices

### DO:

✅ Use hooks in components for data fetching
✅ Keep components focused on UI
✅ Handle errors in hooks
✅ Use TypeScript types from `/types/api.ts`
✅ Add loading states for better UX

### DON'T:

❌ Import `mockData.ts` directly in components
❌ Make API calls directly in components
❌ Put business logic in components
❌ Ignore error states
❌ Skip loading states

## File Structure

```
frontend/
├── app/                    # Next.js pages
│   ├── dashboard/
│   ├── graphs/
│   ├── mentor/
│   ├── investigation/
│   ├── fragility/
│   └── upload/
├── hooks/                  # Custom React hooks
│   ├── useDashboard.ts
│   ├── useGraph.ts
│   ├── useMentor.ts
│   ├── useInvestigation.ts
│   ├── useFragility.ts
│   ├── useRepo.ts
│   └── index.ts
├── services/               # Service layer
│   ├── api.ts             # Base API client
│   ├── websocket.ts       # WebSocket manager
│   ├── repoService.ts
│   ├── dashboardService.ts
│   ├── graphService.ts
│   ├── mentorService.ts
│   ├── investigationService.ts
│   ├── fragilityService.ts
│   ├── mockData.ts        # Mock data (dev only)
│   └── index.ts
└── types/                  # TypeScript types
    └── api.ts             # API contract types
```

## Summary

This architecture provides:

- Clean separation of concerns
- Easy backend integration
- Type safety throughout
- Excellent developer experience
- Production-ready patterns

All components now use hooks instead of direct mock data imports, making the codebase ready for seamless backend integration.

---

Made with Bob
