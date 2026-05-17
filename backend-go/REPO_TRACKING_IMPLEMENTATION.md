# Repository Tracking Implementation

## Overview

This document describes the implementation of the **Repository Tracking System** that enables the backend to manage and track uploaded repositories globally across the application.

## Problem Statement

Previously, the backend had the following limitations:
- No way to list all uploaded repositories
- No persistent tracking of repo metadata (URL, upload time, status)
- Frontend had to hardcode or manually track repo_ids
- No centralized repository management

## Solution

Implemented a **Repository Tracker** service that:
1. Tracks all uploaded repositories with metadata
2. Persists repository information to disk
3. Provides REST API endpoints to list and query repositories
4. Integrates seamlessly with existing upload flow

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API Gateway                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  POST /upload-repo                                   │   │
│  │    ↓                                                 │   │
│  │  Clone Service → Repository Tracker                 │   │
│  │                      ↓                               │   │
│  │                  repos.json (persisted)              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  GET /repos → List all repositories                  │   │
│  │  GET /repo/{repo_id} → Get specific repo metadata   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Repository Tracker Service

**File:** `internal/repository/tracker.go`

**Key Components:**

```go
type RepoMetadata struct {
    RepoID      string    `json:"repo_id"`
    RepoURL     string    `json:"repo_url"`
    RepoPath    string    `json:"repo_path"`
    UploadedAt  time.Time `json:"uploaded_at"`
    Status      string    `json:"status"` // "uploaded", "analyzing", "ready"
    LastUpdated time.Time `json:"last_updated"`
}

type Tracker struct {
    repos      map[string]*RepoMetadata
    mu         sync.RWMutex
    storageDir string
}
```

**Features:**
- Thread-safe operations with RWMutex
- Persistent storage to `repos.json` file
- Automatic loading on startup
- Status tracking for repository lifecycle

**Methods:**
- `AddRepo(repoID, repoURL, repoPath string)` - Register new repository
- `UpdateStatus(repoID, status string)` - Update repository status
- `GetRepo(repoID string)` - Retrieve specific repository
- `ListRepos()` - Get all repositories
- `DeleteRepo(repoID string)` - Remove repository from tracking

---

### 2. API Gateway Integration

**File:** `internal/api/gateway.go`

**Changes:**

1. **Added Repository Tracker to Gateway struct:**
```go
type Gateway struct {
    cloner              *github.CloneService
    jobQueue            *queue.JobQueue
    investigationMgr    *investigations.InvestigationManager
    neo4jClient         *graph.Neo4jClient
    repoTracker         *repository.Tracker  // NEW
}
```

2. **Updated Constructor:**
```go
func NewGateway(..., tracker *repository.Tracker) *Gateway
```

3. **Enhanced `/upload-repo` endpoint:**
   - Now tracks repository after successful clone
   - Stores metadata (URL, path, timestamp)
   - Non-blocking (logs warning if tracking fails)

4. **Added New Endpoints:**

#### `GET /repos`
Returns list of all uploaded repositories.

**Response:**
```json
{
  "repos": [
    {
      "repo_id": "repo_abc12345",
      "repo_url": "https://github.com/user/repo",
      "repo_path": "./repos/repo_abc12345",
      "uploaded_at": "2026-05-17T04:00:00Z",
      "status": "uploaded",
      "last_updated": "2026-05-17T04:00:00Z"
    }
  ],
  "count": 1
}
```

#### `GET /repo/{repo_id}`
Returns metadata for a specific repository.

**Response:**
```json
{
  "repo_id": "repo_abc12345",
  "repo_url": "https://github.com/user/repo",
  "repo_path": "./repos/repo_abc12345",
  "uploaded_at": "2026-05-17T04:00:00Z",
  "status": "uploaded",
  "last_updated": "2026-05-17T04:00:00Z"
}
```

---

### 3. Main Application Wiring

**File:** `main.go`

**Changes:**

1. **Added import:**
```go
import "incidentos/backend-go/internal/repository"
```

2. **Initialize Repository Tracker:**
```go
repoTracker := repository.NewTracker(reposDir)
log.Printf("[Main] Repository Tracker initialized")
```

3. **Wire to Gateway:**
```go
gateway := api.NewGateway(cloneService, jobQueue, investigationMgr, neo4jClient, repoTracker)
```

---

## Data Persistence

### Storage Location
- **File:** `{REPOS_DIR}/repos.json`
- **Default:** `./repos/repos.json`

### Storage Format
```json
{
  "repo_abc12345": {
    "repo_id": "repo_abc12345",
    "repo_url": "https://github.com/user/repo",
    "repo_path": "./repos/repo_abc12345",
    "uploaded_at": "2026-05-17T04:00:00Z",
    "status": "uploaded",
    "last_updated": "2026-05-17T04:00:00Z"
  }
}
```

### Persistence Behavior
- **Automatic save** on every repository addition/update
- **Automatic load** on application startup
- **Graceful degradation** if file doesn't exist (starts fresh)

---

## Usage Examples

### 1. Upload a Repository
```bash
curl -X POST http://localhost:8080/upload-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'
```

**Response:**
```json
{
  "repo_id": "repo_abc12345",
  "status": "uploaded"
}
```

### 2. List All Repositories
```bash
curl http://localhost:8080/repos
```

**Response:**
```json
{
  "repos": [
    {
      "repo_id": "repo_abc12345",
      "repo_url": "https://github.com/user/repo",
      "repo_path": "./repos/repo_abc12345",
      "uploaded_at": "2026-05-17T04:00:00Z",
      "status": "uploaded",
      "last_updated": "2026-05-17T04:00:00Z"
    }
  ],
  "count": 1
}
```

### 3. Get Specific Repository
```bash
curl http://localhost:8080/repo/repo_abc12345
```

**Response:**
```json
{
  "repo_id": "repo_abc12345",
  "repo_url": "https://github.com/user/repo",
  "repo_path": "./repos/repo_abc12345",
  "uploaded_at": "2026-05-17T04:00:00Z",
  "status": "uploaded",
  "last_updated": "2026-05-17T04:00:00Z"
}
```

### 4. Use repo_id in Other Endpoints
```bash
# Dashboard
curl http://localhost:8080/dashboard/repo_abc12345

# Dependency Graph
curl http://localhost:8080/dependency-graph/repo_abc12345

# Fragility Analysis
curl -X POST http://localhost:8080/compute-fragility \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "repo_abc12345"}'
```

---

## Frontend Integration

### Recommended Flow

1. **Upload Repository:**
```typescript
const response = await fetch('http://localhost:8080/upload-repo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ repo_url: 'https://github.com/user/repo' })
});
const { repo_id } = await response.json();
```

2. **Store repo_id in State:**
```typescript
const [currentRepoId, setCurrentRepoId] = useState<string | null>(null);
setCurrentRepoId(repo_id);
```

3. **List Available Repositories:**
```typescript
const response = await fetch('http://localhost:8080/repos');
const { repos } = await response.json();
```

4. **Use repo_id Globally:**
```typescript
// Dashboard
fetch(`http://localhost:8080/dashboard/${currentRepoId}`)

// Dependency Graph
fetch(`http://localhost:8080/dependency-graph/${currentRepoId}`)

// Fragility
fetch('http://localhost:8080/compute-fragility', {
  method: 'POST',
  body: JSON.stringify({ repo_id: currentRepoId })
})
```

---

## Benefits

### ✅ Solved Problems

1. **No More Hardcoded repo_id**
   - Frontend can dynamically fetch available repositories
   - Users can switch between multiple uploaded repos

2. **Persistent Tracking**
   - Repository metadata survives server restarts
   - Upload history is maintained

3. **Better UX**
   - Users can see all their uploaded repositories
   - Clear status tracking (uploaded → analyzing → ready)

4. **Scalability**
   - Foundation for multi-user support
   - Easy to extend with additional metadata

---

## Future Enhancements

### Planned Features

1. **Database Storage**
   - Move from JSON file to PostgreSQL/Redis
   - Better query performance for large datasets

2. **Repository Status Updates**
   - Automatically update status when analysis completes
   - Track analysis progress percentage

3. **Repository Deletion**
   - Add DELETE endpoint to remove repositories
   - Clean up cloned files from disk

4. **Search and Filtering**
   - Search repositories by URL or name
   - Filter by status or upload date

5. **Multi-User Support**
   - Associate repositories with user accounts
   - User-specific repository lists

---

## Testing

### Manual Testing Checklist

- [x] Upload repository and verify tracking
- [x] List repositories and verify metadata
- [x] Get specific repository by ID
- [x] Use repo_id in dashboard endpoint
- [x] Use repo_id in dependency-graph endpoint
- [x] Use repo_id in fragility endpoint
- [x] Verify persistence across server restarts
- [x] Test with multiple repositories

### Test Script

```bash
# 1. Upload a repository
curl -X POST http://localhost:8080/upload-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'

# 2. List all repositories
curl http://localhost:8080/repos

# 3. Get specific repository (use repo_id from step 1)
curl http://localhost:8080/repo/repo_abc12345

# 4. Use repo_id in other endpoints
curl http://localhost:8080/dashboard/repo_abc12345
curl http://localhost:8080/dependency-graph/repo_abc12345
```

---

## Migration Notes

### Backward Compatibility

✅ **Fully backward compatible** - existing endpoints unchanged:
- `/upload-repo` still returns `repo_id` as before
- `/dashboard/{repo_id}` works with any repo_id
- `/dependency-graph/{repo_id}` works with any repo_id

### No Breaking Changes

- All existing functionality preserved
- New endpoints are additive only
- Optional tracking (graceful degradation if tracker unavailable)

---

## Summary

The Repository Tracking System provides a complete solution for managing uploaded repositories in IncidentOS. It enables:

1. ✅ **Dynamic repo_id management** - No more hardcoded values
2. ✅ **Persistent storage** - Survives server restarts
3. ✅ **REST API** - Easy frontend integration
4. ✅ **Thread-safe** - Concurrent access supported
5. ✅ **Extensible** - Easy to add new features

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Last Updated:** 2026-05-17

---

**Built with ❤️ and Bob** 🤖