# IncidentOS Backend - Pending Implementation Plan

## Executive Summary

This document outlines the **pending backend implementation** for IncidentOS based on the comparison between [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) (what's done) and [`contracts.md`](contracts.md) (full specification).

**Current Status:** ✅ Core foundation complete (API Gateway, Clone Service, Job Queue)  
**Pending Work:** 3 major components + database integrations + enhanced endpoints

---

## ✅ Already Implemented (DO NOT TOUCH)

### Core Infrastructure
- [`internal/github/clone.go`](internal/github/clone.go) - Repository cloning with deterministic IDs
- [`internal/queue/queue.go`](internal/queue/queue.go) - Async job queue with AI Engine dispatch
- [`internal/api/gateway.go`](internal/api/gateway.go) - 8 HTTP endpoints (basic versions)
- [`main.go`](main.go) - Application wiring with graceful shutdown

### Working Endpoints
- `POST /upload-repo` - Clone and enqueue analysis
- `POST /analyze-repo` - Trigger AI analysis
- `POST /compute-fragility` - Enqueue fragility job
- `POST /start-investigation` - Enqueue investigation
- `POST /mentor-query` - Enqueue mentor query
- `GET /dashboard/{repo_id}` - Stubbed dashboard data
- `GET /dependency-graph/{repo_id}` - Stubbed graph data
- `GET /health` - Health check

---

## 🚧 Pending Implementation

### 1. WebSocket Server (`internal/websocket/hub.go`)

**Status:** Stub file exists, needs full implementation

**Purpose:** Real-time event streaming to frontend for live updates during analysis, investigation, and fragility computation.

**Requirements:**
- WebSocket connection management (hub pattern)
- Client registration/unregistration
- Broadcast events to all connected clients
- Room-based broadcasting (per repo_id)
- Integration with Job Queue event channel
- Graceful connection cleanup

**Key Components:**
```go
type Hub struct {
    clients    map[*Client]bool
    broadcast  chan Event
    register   chan *Client
    unregister chan *Client
    rooms      map[string]map[*Client]bool // repo_id -> clients
}

type Client struct {
    hub    *Hub
    conn   *websocket.Conn
    send   chan []byte
    repoID string
}
```

**Event Types to Support:**
- `repo_analysis_started`
- `dependency_graph_generated`
- `fragility_analysis_complete`
- `investigation_complete`

**Event Structure:**
```json
{
  "event": "repo_analysis_started"
}
```

**Integration Points:**
- Listen to `jobQueue.Events()` channel
- Broadcast events to relevant clients
- Add WebSocket endpoint: `GET /ws?repo_id={repo_id}`
- Wire into [`main.go`](main.go) startup

**Constraints:**
- Use `gorilla/websocket` or standard library only
- Non-blocking send operations
- Automatic ping/pong for connection health
- Context-aware shutdown

---

### 2. Investigation Manager (`internal/investigations/service.go`)

**Status:** Stub file exists, needs full implementation

**Purpose:** Orchestrate multi-step investigation workflows, track state, coordinate with AI Engine, and manage investigation lifecycle.

**Requirements:**
- Investigation state management (in-memory or persistent)
- Workflow orchestration for incident RCA
- Progress tracking and status updates
- Integration with Job Queue for async execution
- WebSocket event emission for progress updates

**Key Components:**
```go
type InvestigationManager struct {
    investigations map[string]*Investigation
    jobQueue       *queue.JobQueue
    wsHub          *websocket.Hub
    mu             sync.RWMutex
}

type Investigation struct {
    ID              string
    RepoID          string
    Incident        string
    Status          string // "started", "analyzing", "complete", "failed"
    Progress        []Step
    RootCause       string
    AffectedServices []string
    CreatedAt       time.Time
    UpdatedAt       time.Time
}

type Step struct {
    Name      string
    Status    string
    Timestamp time.Time
}
```

**Core Methods:**
- `StartInvestigation(repoID, incident string) (investigationID string, error)`
- `GetInvestigation(investigationID string) (*Investigation, error)`
- `UpdateProgress(investigationID, step, status string) error`
- `CompleteInvestigation(investigationID string, result RCAResult) error`
- `ListInvestigations(repoID string) ([]*Investigation, error)`

**Workflow Steps:**
1. Create investigation record
2. Emit `investigation_started` event
3. Enqueue AI Engine job
4. Track progress through callbacks
5. Store final RCA report
6. Emit `investigation_complete` event

**Integration Points:**
- Called by [`gateway.go`](internal/api/gateway.go) `/start-investigation` endpoint
- Enqueues jobs via Job Queue
- Broadcasts events via WebSocket Hub
- Receives callbacks from AI Engine (via new endpoint)

**New Endpoints Needed:**
- `GET /investigation/{investigation_id}` - Get investigation status
- `GET /investigations?repo_id={repo_id}` - List investigations
- `POST /investigation-callback` - AI Engine callback for progress updates

---

### 3. Database Integration Layer

**Status:** Not started

**Purpose:** Connect to Neo4j and ChromaDB for persistent storage of graph data, embeddings, and analysis results.

#### 3.1 Neo4j Integration (`internal/graph/neo4j.go`)

**Requirements:**
- Connection management to Neo4j database
- CRUD operations for graph nodes and relationships
- Query methods for dependency graph retrieval
- Transaction support

**Key Components:**
```go
type Neo4jClient struct {
    driver neo4j.Driver
    uri    string
}

type GraphNode struct {
    ID         string
    Type       string // "service", "module", "api"
    Properties map[string]interface{}
}

type GraphEdge struct {
    Source string
    Target string
    Type   string // "DEPENDS_ON", "CALLS", "IMPORTS"
}
```

**Core Methods:**
- `Connect(uri, username, password string) error`
- `Close() error`
- `StoreNode(node GraphNode) error`
- `StoreEdge(edge GraphEdge) error`
- `GetDependencyGraph(repoID string) (nodes []GraphNode, edges []GraphEdge, error)`
- `QueryServiceDependencies(repoID, serviceID string) ([]string, error)`

**Integration Points:**
- Called by `/dependency-graph/{repo_id}` endpoint (replace stub)
- Receives data from AI Engine via callback endpoints
- Used by Investigation Manager for impact analysis

#### 3.2 ChromaDB Integration (`internal/memory/chromadb.go`)

**Requirements:**
- HTTP client for ChromaDB REST API
- Collection management
- Document storage with embeddings
- Semantic search capabilities

**Key Components:**
```go
type ChromaDBClient struct {
    baseURL    string
    httpClient *http.Client
}

type Document struct {
    ID        string
    Content   string
    Metadata  map[string]interface{}
    Embedding []float64
}
```

**Core Methods:**
- `CreateCollection(name string) error`
- `AddDocument(collection string, doc Document) error`
- `Query(collection string, queryEmbedding []float64, limit int) ([]Document, error)`
- `GetDocument(collection, docID string) (*Document, error)`

**Collections to Support:**
- `incidents_{repo_id}` - Incident summaries
- `rca_{repo_id}` - RCA reports
- `mentor_{repo_id}` - Mentor knowledge base
- `architecture_{repo_id}` - Architecture summaries

**Integration Points:**
- Used by Mentor Query endpoint for context retrieval
- Stores investigation results
- Provides historical incident matching

---

### 4. Enhanced API Endpoints

#### 4.1 Dashboard Endpoint Enhancement (`GET /dashboard/{repo_id}`)

**Current:** Returns stubbed data  
**Required:** Fetch real data from Neo4j and ChromaDB

**Data Sources:**
- Neo4j: Service count, dependency count
- ChromaDB: Recent incidents count
- In-memory: Fragility scores (from AI Engine responses)

**Response Structure:**
```json
{
  "repo_id": "repo_123",
  "services": 12,
  "dependencies": 38,
  "fragile_services": ["auth-service", "checkout-service"],
  "recent_incidents": 4
}
```

#### 4.2 Dependency Graph Enhancement (`GET /dependency-graph/{repo_id}`)

**Current:** Returns stubbed data  
**Required:** Query Neo4j for real graph data

**Implementation:**
- Query Neo4j for all nodes with `repo_id`
- Query Neo4j for all edges between those nodes
- Transform to frontend-compatible format
- Add fragility scores to nodes (if available)

#### 4.3 New Callback Endpoints

**Purpose:** Receive async results from AI Engine

**MVP Callback Endpoints:**

1. **`POST /callback/repository-parsed`** - Repository structure analysis (Workflow 4)
   ```json
   {
     "repo_id": "repo_123",
     "services": ["auth-service", "payment-service"],
     "languages": ["Python", "TypeScript"],
     "frameworks": ["FastAPI", "Next.js"]
   }
   ```
   **Actions:** Store in ChromaDB, emit `repo_analysis_started` WebSocket event

2. **`POST /callback/dependencies-extracted`** - Dependency graph data (Workflow 5)
   ```json
   {
     "repo_id": "repo_123",
     "dependencies": [
       {
         "source": "checkout-service",
         "target": "auth-service",
         "type": "DEPENDS_ON"
       }
     ]
   }
   ```
   **Actions:** Store in Neo4j, emit `dependency_graph_generated` WebSocket event

3. **`POST /callback/git-history-analyzed`** - Git history insights (Workflow 6)
   ```json
   {
     "repo_id": "repo_123",
     "high_churn_services": ["auth-service"],
     "recent_commits": 124,
     "top_contributors": ["dev1", "dev2"]
   }
   ```
   **Actions:** Store in ChromaDB (for fragility analysis input)

4. **`POST /callback/fragility-complete`** - Fragility scores (Workflow 7)
   ```json
   {
     "repo_id": "repo_123",
     "fragility_scores": [
       {
         "service": "auth-service",
         "score": 8.7,
         "reasons": ["high commit churn", "high dependency centrality"]
       }
     ]
   }
   ```
   **Actions:** Cache in memory, emit `fragility_analysis_complete` WebSocket event

5. **`POST /callback/investigation-complete`** - Final RCA report (Workflow 14)
   ```json
   {
     "investigation_id": "inv_123",
     "incident": "checkout-service CI failed",
     "root_cause": "JWT validation regression",
     "affected_services": ["auth-service", "checkout-service"],
     "fragility_score": 8.7,
     "historical_correlation": "OAuth migration incident",
     "recommended_actions": ["rollback recent auth changes"]
   }
   ```
   **Actions:** Store in ChromaDB, update Investigation Manager, emit `investigation_complete` WebSocket event

6. **`POST /callback/mentor-response`** - Mentor query answer (Workflow 12)
   ```json
   {
     "repo_id": "repo_123",
     "question": "What should I learn first?",
     "answer": "Start with auth-service because it is central to the architecture..."
   }
   ```
   **Actions:** Return response to frontend (no WebSocket event for MVP)

**Common Responsibilities:**
- Validate callback authenticity (optional: API key)
- Store results in appropriate database (Neo4j/ChromaDB)
- Update Investigation Manager state (if applicable)
- Emit WebSocket events to connected clients (for key milestones only)
- Log completion with structured logging

---

## 📋 Implementation Checklist

### Phase 1: WebSocket Infrastructure
- [x] Implement WebSocket Hub with client management
- [x] Add client registration/unregistration logic
- [x] Implement broadcast mechanism with room support
- [x] Create WebSocket endpoint `/ws`
- [x] Integrate with Job Queue event channel
- [x] Add graceful shutdown support
- [x] Test with multiple concurrent connections
- [x] Update main.go to wire WebSocket hub
- [x] Create test HTML page
- [x] Document implementation

### Phase 2: Investigation Manager
- [x] Create Investigation struct and state management
- [x] Implement `StartInvestigation` method
- [x] Add progress tracking methods
- [x] Implement investigation retrieval endpoints
- [x] Add callback handling for AI Engine updates
- [x] Integrate with WebSocket Hub for events
- [x] Add investigation listing endpoint
- [x] Test full investigation lifecycle

### Phase 3: Neo4j Integration
- [x] Create Neo4j client with connection pooling
- [x] Implement node storage methods
- [x] Implement edge storage methods
- [x] Add dependency graph query methods
- [x] Create callback endpoint for graph data
- [x] Update `/dependency-graph/{repo_id}` to use Neo4j
- [x] Add error handling and retry logic
- [x] Test with sample graph data

### Phase 4: ChromaDB Integration
- [x] Create ChromaDB HTTP client
- [x] Implement collection management
- [x] Add document storage methods
- [x] Implement semantic search
- [x] Create callback endpoint for embeddings
- [x] Integrate with mentor query endpoint
- [x] Add incident history retrieval
- [x] Test embedding storage and retrieval

### Phase 5: Enhanced Endpoints & Callbacks
- [x] Implement `POST /callback/repository-parsed` endpoint
- [x] Implement `POST /callback/dependencies-extracted` endpoint
- [x] Implement `POST /callback/git-history-analyzed` endpoint
- [x] Implement `POST /callback/fragility-complete` endpoint
- [x] Implement `POST /callback/investigation-complete` endpoint
- [x] Implement `POST /callback/mentor-response` endpoint
- [x] Update `/dashboard/{repo_id}` with real data from databases
- [x] Add fragility score caching mechanism
- [x] Add investigation status endpoints
- [x] Test all callback endpoints with mock AI Engine responses
- [ ] Test all endpoints end-to-end

### Phase 6: Integration & Testing
- [x] Wire all components in [`main.go`](main.go)
- [x] Add environment variables for DB connections
- [ ] Test full workflow: upload → analyze → investigate
- [ ] Verify WebSocket event streaming
- [ ] Test concurrent investigations
- [ ] Load test with multiple repositories
- [x] Document API changes

---

## 🔧 Technical Decisions

### Database Connections
- **Neo4j:** Use official Go driver (`neo4j-go-driver`)
- **ChromaDB:** Use HTTP client (standard library)
- **Connection Pooling:** Implement for both databases
- **Retry Logic:** Exponential backoff for transient failures

### State Management
- **Investigations:** In-memory map with mutex (MVP)
- **Future:** Persistent storage in PostgreSQL/Redis
- **Fragility Scores:** Cache in memory, refresh on analysis

### WebSocket Strategy
- **Library:** `gorilla/websocket` (if allowed) or standard library upgrade
- **Pattern:** Hub-and-spoke with room-based broadcasting
- **Scalability:** Single instance for MVP, Redis pub/sub for multi-instance

### Error Handling
- **Logging:** Structured logging with context
- **Responses:** Consistent JSON error format
- **Retries:** Automatic for database operations
- **Timeouts:** Context-based for all operations

---

## 🚀 Deployment Considerations

### Environment Variables (New)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
CHROMADB_URL=http://localhost:8000
CALLBACK_API_KEY=secret_key_for_ai_engine
```

### Docker Compose Updates
- Add Neo4j service
- Add ChromaDB service
- Configure network connectivity
- Add health checks

### Testing Strategy
- Unit tests for each component
- Integration tests with test databases
- WebSocket connection tests
- End-to-end workflow tests
- Load testing for concurrent operations

---

## 📊 Success Criteria

### Functional Requirements
✅ WebSocket server streams real-time events  
✅ Investigation Manager tracks full lifecycle  
✅ Neo4j stores and retrieves dependency graphs  
✅ ChromaDB stores embeddings and enables search  
✅ Dashboard shows real data from databases  
✅ All callback endpoints receive AI results  
✅ Concurrent investigations work correctly  

### Non-Functional Requirements
✅ Response time < 200ms for API endpoints  
✅ WebSocket latency < 100ms  
✅ Support 100+ concurrent WebSocket connections  
✅ Graceful degradation if databases unavailable  
✅ Zero data loss during shutdown  
✅ Comprehensive error logging  

---

## 🎯 MVP Priority

### MUST HAVE (Week 1)
1. WebSocket Hub implementation
2. Investigation Manager core functionality
3. Neo4j integration for dependency graphs
4. Enhanced `/dependency-graph/{repo_id}` endpoint

### SHOULD HAVE (Week 2)
5. ChromaDB integration
6. Callback endpoints for AI results
7. Enhanced `/dashboard/{repo_id}` endpoint
8. Investigation status endpoints

### NICE TO HAVE (Week 3)
9. Fragility score caching
10. Advanced error recovery
11. Performance optimizations
12. Comprehensive test coverage

---

## 📝 Notes

### Compatibility with Existing Code
- All new code must work with existing [`gateway.go`](internal/api/gateway.go)
- Do not modify existing endpoint signatures
- Extend Gateway struct with new dependencies
- Maintain backward compatibility

### Code Style
- Follow existing Go conventions in codebase
- Use standard library where possible
- Add comprehensive comments
- Include error context in logs

### Team Coordination
- Backend team owns all Go code
- AI team provides callback data formats
- Frontend team consumes WebSocket events
- Database schemas agreed upon in advance

---

## 🔗 Related Documents

- [`contracts.md`](contracts.md) - Full API specification
- [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Current implementation status
- [`backendplan.md`](backendplan.md) - Original backend plan
- [`CONTRACT_VERIFICATION.md`](CONTRACT_VERIFICATION.md) - Contract verification report

---

**Document Version:** 1.2 (MVP Simplified)
**Last Updated:** 2026-05-16
**Status:** Contract-Verified & Ready for Implementation 🚀

**Changes in v1.2 (MVP Simplification):**
- ✅ Simplified WebSocket events to 4 core types (removed intermediate progress events)
- ✅ Reverted to simple event structure: `{"event": "event_name"}`
- ✅ Removed investigation progress callback (not needed for MVP)
- ✅ Reduced callback endpoints from 7 to 6 (MVP scope)
- ✅ Mentor response returns directly to frontend (no WebSocket event)

**Changes in v1.1:**
- ✅ Fixed dashboard response structure (removed `last_analysis` field)
- ✅ Added 3 missing callback endpoints (repository-parsed, dependencies-extracted, git-history-analyzed)
- ✅ Added detailed specifications for all callback endpoints
- ✅ Cross-verified all request-response structures with [`contracts.md`](contracts.md)