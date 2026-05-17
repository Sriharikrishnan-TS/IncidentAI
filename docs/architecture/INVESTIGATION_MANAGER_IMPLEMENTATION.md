# Investigation Manager - Implementation Documentation

## Overview

The Investigation Manager is a core component of IncidentOS that orchestrates multi-step investigation workflows, tracks state, coordinates with the AI Engine, and manages the investigation lifecycle.

**Status:** ✅ Complete  
**Implementation Date:** 2026-05-16  
**Phase:** Phase 2 of Backend Implementation

---

## Architecture

### Component Structure

```
Investigation Manager
├── InvestigationManager (service.go)
│   ├── State Management (in-memory map)
│   ├── Job Queue Integration
│   └── WebSocket Hub Integration
├── Gateway Integration (gateway.go)
│   ├── POST /start-investigation
│   ├── GET /investigation/{investigation_id}
│   ├── GET /investigations?repo_id={repo_id}
│   └── POST /callback/investigation-complete
└── Main Application Wiring (main.go)
```

---

## Data Structures

### Investigation

Represents an ongoing or completed investigation with full lifecycle tracking.

```go
type Investigation struct {
    ID                 string    `json:"id"`
    RepoID             string    `json:"repo_id"`
    Incident           string    `json:"incident"`
    Status             string    `json:"status"` // "started", "analyzing", "complete", "failed"
    Progress           []Step    `json:"progress"`
    RootCause          string    `json:"root_cause,omitempty"`
    AffectedServices   []string  `json:"affected_services,omitempty"`
    FragilityScore     float64   `json:"fragility_score,omitempty"`
    HistoricalCorr     string    `json:"historical_correlation,omitempty"`
    RecommendedActions []string  `json:"recommended_actions,omitempty"`
    CreatedAt          time.Time `json:"created_at"`
    UpdatedAt          time.Time `json:"updated_at"`
}
```

### Step

Represents a single step in the investigation workflow.

```go
type Step struct {
    Name      string    `json:"name"`
    Status    string    `json:"status"` // "pending", "in_progress", "complete", "failed"
    Timestamp time.Time `json:"timestamp"`
}
```

### RCAResult

Final result structure from AI Engine investigation.

```go
type RCAResult struct {
    RootCause          string   `json:"root_cause"`
    AffectedServices   []string `json:"affected_services"`
    FragilityScore     float64  `json:"fragility_score"`
    HistoricalCorr     string   `json:"historical_correlation"`
    RecommendedActions []string `json:"recommended_actions"`
}
```

---

## Core Methods

### StartInvestigation

Creates a new investigation and enqueues it for AI Engine processing.

**Signature:**
```go
func (im *InvestigationManager) StartInvestigation(repoID, incident string) (string, error)
```

**Workflow:**
1. Validates input parameters
2. Generates unique investigation ID: `inv_{repo_id}_{timestamp}`
3. Creates investigation record with "started" status
4. Stores in in-memory map
5. Adds initial progress step
6. Enqueues job to AI Engine via Job Queue
7. Returns investigation ID

**Example:**
```go
investigationID, err := invMgr.StartInvestigation("repo_abc123", "checkout-service CI failed")
// Returns: "inv_repo_abc123_1715864400"
```

---

### GetInvestigation

Retrieves an investigation by ID with full details.

**Signature:**
```go
func (im *InvestigationManager) GetInvestigation(investigationID string) (*Investigation, error)
```

**Features:**
- Thread-safe read with RLock
- Returns deep copy to prevent external modification
- Returns error if investigation not found

---

### UpdateProgress

Adds a progress step to an investigation.

**Signature:**
```go
func (im *InvestigationManager) UpdateProgress(investigationID, stepName, status string) error
```

**Behavior:**
- Appends new step to progress array
- Updates investigation timestamp
- Transitions status from "started" to "analyzing" when first in_progress step is added

---

### CompleteInvestigation

Marks investigation as complete with final RCA results.

**Signature:**
```go
func (im *InvestigationManager) CompleteInvestigation(investigationID string, result RCAResult) error
```

**Workflow:**
1. Updates investigation status to "complete"
2. Stores RCA results (root cause, affected services, etc.)
3. Adds completion step to progress
4. Emits `investigation_complete` WebSocket event to all clients in repo room

---

### FailInvestigation

Marks investigation as failed with reason.

**Signature:**
```go
func (im *InvestigationManager) FailInvestigation(investigationID string, reason string) error
```

---

### ListInvestigations

Returns all investigations for a given repository.

**Signature:**
```go
func (im *InvestigationManager) ListInvestigations(repoID string) ([]*Investigation, error)
```

**Features:**
- Filters by repo_id
- Returns deep copies of all matching investigations
- Thread-safe with RLock

---

## API Endpoints

### POST /start-investigation

Initiates a new investigation workflow.

**Request:**
```json
{
  "repo_id": "repo_abc123",
  "incident": "checkout-service CI failed"
}
```

**Response:**
```json
{
  "investigation_id": "inv_repo_abc123_1715864400",
  "repo_id": "repo_abc123",
  "status": "investigation_started"
}
```

**Status Codes:**
- `200 OK` - Investigation started successfully
- `400 Bad Request` - Missing or invalid parameters
- `500 Internal Server Error` - Failed to start investigation

---

### GET /investigation/{investigation_id}

Retrieves the status and details of a specific investigation.

**Request:**
```
GET /investigation/inv_repo_abc123_1715864400
```

**Response:**
```json
{
  "id": "inv_repo_abc123_1715864400",
  "repo_id": "repo_abc123",
  "incident": "checkout-service CI failed",
  "status": "complete",
  "progress": [
    {
      "name": "Investigation initialized",
      "status": "complete",
      "timestamp": "2026-05-16T12:00:00Z"
    },
    {
      "name": "Investigation complete",
      "status": "complete",
      "timestamp": "2026-05-16T12:05:00Z"
    }
  ],
  "root_cause": "JWT validation regression",
  "affected_services": ["auth-service", "checkout-service"],
  "fragility_score": 8.7,
  "historical_correlation": "OAuth migration incident",
  "recommended_actions": ["rollback recent auth changes"],
  "created_at": "2026-05-16T12:00:00Z",
  "updated_at": "2026-05-16T12:05:00Z"
}
```

**Status Codes:**
- `200 OK` - Investigation found
- `404 Not Found` - Investigation not found
- `405 Method Not Allowed` - Wrong HTTP method

---

### GET /investigations?repo_id={repo_id}

Lists all investigations for a repository.

**Request:**
```
GET /investigations?repo_id=repo_abc123
```

**Response:**
```json
{
  "repo_id": "repo_abc123",
  "investigations": [
    {
      "id": "inv_repo_abc123_1715864400",
      "repo_id": "repo_abc123",
      "incident": "checkout-service CI failed",
      "status": "complete",
      "progress": [...],
      "root_cause": "JWT validation regression",
      "created_at": "2026-05-16T12:00:00Z",
      "updated_at": "2026-05-16T12:05:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Investigations retrieved (empty array if none)
- `400 Bad Request` - Missing repo_id parameter
- `500 Internal Server Error` - Failed to retrieve investigations

---

### POST /callback/investigation-complete

Receives final RCA report from AI Engine when investigation completes.

**Request:**
```json
{
  "investigation_id": "inv_repo_abc123_1715864400",
  "incident": "checkout-service CI failed",
  "root_cause": "JWT validation regression",
  "affected_services": ["auth-service", "checkout-service"],
  "fragility_score": 8.7,
  "historical_correlation": "OAuth migration incident",
  "recommended_actions": ["rollback recent auth changes"]
}
```

**Response:**
```json
{
  "status": "success",
  "investigation_id": "inv_repo_abc123_1715864400"
}
```

**Actions Performed:**
1. Validates callback payload
2. Updates investigation with RCA results
3. Marks investigation as complete
4. Emits `investigation_complete` WebSocket event

**Status Codes:**
- `200 OK` - Investigation completed successfully
- `400 Bad Request` - Invalid payload or missing investigation_id
- `500 Internal Server Error` - Failed to complete investigation

---

## Integration Points

### Job Queue Integration

The Investigation Manager enqueues jobs to the AI Engine via the Job Queue:

```go
payload := map[string]interface{}{
    "investigation_id": investigationID,
    "repo_id":          repoID,
    "incident":         incident,
}
jobQueue.Enqueue("start_investigation", payload)
```

**Job Type:** `start_investigation`  
**AI Engine Endpoint:** `/start-investigation`

---

### WebSocket Integration

The Investigation Manager emits events to connected clients:

**Event:** `investigation_complete`

```json
{
  "event": "investigation_complete",
  "investigation_id": "inv_repo_abc123_1715864400",
  "repo_id": "repo_abc123"
}
```

**Broadcast Scope:** Room-based (all clients subscribed to repo_id)

---

## Thread Safety

The Investigation Manager uses `sync.RWMutex` for thread-safe operations:

- **Read Operations** (GetInvestigation, ListInvestigations): Use `RLock()`
- **Write Operations** (StartInvestigation, UpdateProgress, CompleteInvestigation): Use `Lock()`

All methods that return investigation data create deep copies to prevent external modification.

---

## State Management

**Current Implementation:** In-memory map  
**Key:** Investigation ID (string)  
**Value:** Investigation pointer

**Future Enhancement:** Persistent storage in PostgreSQL or Redis for:
- Durability across restarts
- Multi-instance support
- Historical investigation queries

---

## Testing

### Manual Testing

1. **Start Investigation:**
```bash
curl -X POST http://localhost:8080/start-investigation \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "repo_test123",
    "incident": "Test incident description"
  }'
```

2. **Get Investigation:**
```bash
curl http://localhost:8080/investigation/inv_repo_test123_1715864400
```

3. **List Investigations:**
```bash
curl http://localhost:8080/investigations?repo_id=repo_test123
```

4. **Simulate AI Engine Callback:**
```bash
curl -X POST http://localhost:8080/callback/investigation-complete \
  -H "Content-Type: application/json" \
  -d '{
    "investigation_id": "inv_repo_test123_1715864400",
    "incident": "Test incident",
    "root_cause": "Test root cause",
    "affected_services": ["service1", "service2"],
    "fragility_score": 7.5,
    "historical_correlation": "Similar to previous incident",
    "recommended_actions": ["Action 1", "Action 2"]
  }'
```

---

## Error Handling

### Common Errors

1. **Investigation Not Found:**
   - Status: 404
   - Message: "Investigation not found"

2. **Missing Parameters:**
   - Status: 400
   - Message: "repo_id and incident are required"

3. **Queue Full:**
   - Status: 500
   - Message: "Failed to start investigation"

### Logging

All operations are logged with structured context:
```
[Gateway] Investigation inv_repo_abc123_1715864400 completed successfully
[Gateway] Failed to start investigation: queue is full
```

---

## Future Enhancements

### Phase 3 Improvements

1. **Persistent Storage:**
   - Store investigations in PostgreSQL
   - Add investigation history queries
   - Support pagination for large result sets

2. **Advanced Features:**
   - Investigation cancellation
   - Investigation retry mechanism
   - Investigation priority levels
   - Investigation templates

3. **Analytics:**
   - Investigation duration metrics
   - Success/failure rates
   - Most common root causes
   - Affected services correlation

---

## Dependencies

- [`internal/queue`](internal/queue/queue.go) - Job Queue for AI Engine dispatch
- [`internal/websocket`](internal/websocket/hub.go) - WebSocket Hub for real-time events
- Go standard library only (no external dependencies)

---

## Files Modified

1. **New File:** [`internal/investigations/service.go`](internal/investigations/service.go) (268 lines)
2. **Modified:** [`internal/api/gateway.go`](internal/api/gateway.go) - Added Investigation Manager integration
3. **Modified:** [`main.go`](main.go) - Wired Investigation Manager into application

---

## Compliance

✅ Uses only Go standard library  
✅ Thread-safe operations with mutex  
✅ Comprehensive error handling  
✅ Structured logging  
✅ Deep copy returns to prevent data races  
✅ Context-aware operations  
✅ Follows existing code patterns  

---

## Success Criteria

✅ Investigation lifecycle fully tracked  
✅ All CRUD operations implemented  
✅ WebSocket events emitted on completion  
✅ Integration with Job Queue working  
✅ API endpoints functional  
✅ Thread-safe state management  
✅ Clean build with no errors  
✅ Follows Go best practices  

---

**Implementation Complete:** Phase 2 - Investigation Manager ✅  
**Next Phase:** Phase 3 - Neo4j Integration

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-16  
**Status:** Production Ready ✅