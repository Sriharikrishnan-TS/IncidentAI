# IncidentOS — Backend Go Implementation Plan
## Prompt for IBM BAM (AI Code Generation Agent)

---

## Who You Are

You are an AI code generation agent. Your job is to implement the Go backend for **IncidentOS** — a memory-aware engineering intelligence platform. You will implement three internal packages from scratch based on the contracts and responsibilities defined below.

Read this entire document before writing any code. Then implement each package in the order specified.

---

## What You Are Building

You are implementing three Go packages inside a `backend/` directory:

```
backend/
└── internal/
    ├── api/
    │   └── gateway.go        ← Package 1: API Gateway
    ├── github/
    │   └── clone.go          ← Package 2: Repo Clone Service
    └── queue/
        └── queue.go          ← Package 3: Job Queue
```

These three packages are the core of the IncidentOS backend. They work together like this:

```
Frontend HTTP Request
        ↓
   internal/api  (API Gateway)
        ↓
   internal/github (Clone Service) — clones the GitHub repo locally
        ↓
   internal/queue (Job Queue) — enqueues async AI analysis jobs
        ↓
   AI Engine (Python) — receives the job via HTTP (you don't implement this)
```

---

## Package 1 — `internal/api/gateway.go`

### Responsibility

This is the **central routing hub**. Every HTTP request from the frontend hits this package first. It validates requests, calls the clone service, enqueues jobs, and returns responses. Nothing in the backend is called directly by the frontend except through here.

### File to create

`internal/api/gateway.go`

### Struct to define

```go
type Gateway struct {
    cloner   *github.CloneService
    jobQueue *queue.JobQueue
}
```

Constructor:
```go
func NewGateway(cloner *github.CloneService, jq *queue.JobQueue) *Gateway
```

Method to register all routes:
```go
func (g *Gateway) RegisterRoutes(mux *http.ServeMux)
```

---

### Endpoints to implement

#### POST /upload-repo

**Purpose:** Accept a GitHub URL from the frontend, trigger cloning and analysis.

**Request body:**
```json
{ "repo_url": "https://github.com/user/repo" }
```

**What it does internally:**
1. Decode and validate the request body — return 400 if `repo_url` is missing or empty
2. Call `github.IsValidGitHubURL(req.RepoURL)` — return 400 if invalid
3. Call `g.cloner.Clone(ctx, req.RepoURL)` — return 500 if it fails
4. Call `g.jobQueue.Enqueue("analyze_repo", payload)` where payload contains `repo_id` and `repo_path`
5. Return 200 with the response below

**Success response:**
```json
{ "repo_id": "repo_abc123", "status": "uploaded" }
```

---

#### POST /analyze-repo

**Purpose:** Directly trigger AI analysis for an already-cloned repo (internal use).

**Request body:**
```json
{ "repo_id": "repo_abc123", "repo_path": "./repos/repo_abc123" }
```

**What it does internally:**
1. Validate that both `repo_id` and `repo_path` are present — return 400 if missing
2. Call `g.jobQueue.Enqueue("analyze_repo", payload)`
3. Return 200 with the response below

**Success response:**
```json
{ "repo_id": "repo_abc123", "status": "analysis_started" }
```

---

#### POST /compute-fragility

**Purpose:** Request fragility score computation for a given repo.

**Request body:**
```json
{ "repo_id": "repo_abc123" }
```

**What it does internally:**
1. Validate `repo_id` is present — return 400 if missing
2. Call `g.jobQueue.Enqueue("compute_fragility", payload)`
3. Return 200 with the response below

**Success response:**
```json
{ "repo_id": "repo_abc123", "status": "fragility_job_queued" }
```

---

#### POST /start-investigation

**Purpose:** Kick off an incident investigation workflow.

**Request body:**
```json
{ "repo_id": "repo_abc123", "incident": "checkout-service CI failed" }
```

**What it does internally:**
1. Validate both fields are present — return 400 if missing
2. Call `g.jobQueue.Enqueue("start_investigation", payload)`
3. Return 200 with the response below

**Success response:**
```json
{ "repo_id": "repo_abc123", "status": "investigation_started" }
```

---

#### POST /mentor-query

**Purpose:** Forward a mentor/onboarding question to the AI engine asynchronously.

**Request body:**
```json
{ "repo_id": "repo_abc123", "question": "What should I learn first?" }
```

**What it does internally:**
1. Validate both fields — return 400 if missing
2. Call `g.jobQueue.Enqueue("mentor_query", payload)`
3. Return 200 with the response below

**Success response:**
```json
{ "repo_id": "repo_abc123", "status": "mentor_query_queued" }
```

---

#### GET /dashboard/{repo_id}

**Purpose:** Return summary data for the frontend dashboard.

**What it does internally:**
1. Extract `repo_id` from the URL path — return 400 if missing
2. For now, return a hardcoded/stubbed response (real data will come from Neo4j/ChromaDB later)

**Success response:**
```json
{
  "repo_id": "repo_abc123",
  "services": 12,
  "dependencies": 38,
  "fragile_services": ["auth-service", "checkout-service"],
  "recent_incidents": 4
}
```

---

#### GET /dependency-graph/{repo_id}

**Purpose:** Return graph nodes and edges for the dependency graph viewer.

**What it does internally:**
1. Extract `repo_id` from the URL path — return 400 if missing
2. For now, return a stubbed response

**Success response:**
```json
{
  "nodes": [{ "id": "auth-service", "type": "service" }],
  "edges": [{ "source": "checkout-service", "target": "auth-service" }]
}
```

---

#### GET /health

**Purpose:** Health check. Returns 200 with `{ "status": "ok" }`. No logic needed.

---

### Helper function to write inside gateway.go

Write a private helper for JSON error responses:
```go
func httpError(w http.ResponseWriter, message string, code int)
```
It should set `Content-Type: application/json`, write the status code, and write:
```json
{ "error": "<message>" }
```

---

### Rules for gateway.go

- Use only Go standard library — no external HTTP frameworks
- All handlers must check HTTP method and return 405 if wrong method is used
- All JSON decoding errors must return 400
- Log errors with `log.Printf` before returning 500
- Set `Content-Type: application/json` on all responses

---

## Package 2 — `internal/github/clone.go`

### Responsibility

This service handles cloning GitHub repositories to local disk. It generates a unique `repo_id`, creates a local directory, runs `git clone`, and returns the path. The API Gateway calls this directly during `/upload-repo`.

### File to create

`internal/github/clone.go`

---

### Struct to define

```go
type CloneService struct {
    BaseDir string // e.g. "./repos" — root directory for all cloned repos
}
```

Constructor:
```go
func NewCloneService(baseDir string) *CloneService
```

---

### Functions to implement

#### `IsValidGitHubURL(url string) bool`

A standalone (non-method) validation function.

Rules:
- Must start with `https://github.com/`
- Must have at least one `/` after the domain (meaning it has an owner)
- Must have at least one more segment after the owner (meaning it has a repo name)
- Return `false` for anything that fails these checks

---

#### `(s *CloneService) Clone(ctx context.Context, repoURL string) (*CloneResult, error)`

**Steps:**
1. Generate a unique `repo_id` using `fmt.Sprintf("repo_%s", shortHash(repoURL))` — see helper below
2. Build the local path: `filepath.Join(s.BaseDir, repoID)`
3. Create the directory with `os.MkdirAll` — return error if it fails
4. Run `git clone <repoURL> <localPath>` using `exec.CommandContext`
5. Capture stderr and return a wrapped error if the command fails
6. Return a `*CloneResult` on success

---

#### Return type

```go
type CloneResult struct {
    RepoID   string `json:"repo_id"`
    RepoPath string `json:"repo_path"`
    Status   string `json:"status"` // always "cloned" on success
}
```

---

#### Private helper — `shortHash(input string) string`

- Takes the input string (the repo URL)
- Computes `sha256.Sum256([]byte(input))`
- Returns the first 8 hex characters of the hash
- This makes `repo_id` deterministic per URL (same URL = same ID)

---

### Rules for clone.go

- Import `os/exec`, `crypto/sha256`, `fmt`, `path/filepath`, `context`, `os`
- Do not use any third-party Git libraries — use the system `git` binary via `exec.CommandContext`
- `BaseDir` must be created with `os.MkdirAll` if it doesn't exist — do this in the constructor
- If `git clone` fails, wrap stderr output in the error message so it's debuggable

---

## Package 3 — `internal/queue/queue.go`

### Responsibility

The job queue handles all async task execution. When the API Gateway receives a request that needs heavy processing (AI analysis, fragility scoring, investigation), it does NOT block waiting for a result. Instead it enqueues a job and returns immediately. A background worker goroutine picks up jobs and dispatches them to the Python AI Engine via HTTP POST.

### File to create

`internal/queue/queue.go`

---

### Types to define

```go
// Job represents a single unit of async work.
type Job struct {
    Type    string                 // e.g. "analyze_repo", "compute_fragility"
    Payload map[string]interface{} // arbitrary data for the job
}

// Event is broadcast over WebSocket to the frontend.
type Event struct {
    Event string `json:"event"` // e.g. "repo_analysis_started"
    RepoID string `json:"repo_id"`
}

// JobQueue is the async task dispatcher.
type JobQueue struct {
    jobs      chan Job
    aiBaseURL string // base URL of the Python AI Engine, e.g. "http://localhost:8001"
    events    chan Event
}
```

---

### Functions to implement

#### `NewJobQueue(aiBaseURL string, bufferSize int) *JobQueue`

- Creates a buffered `jobs` channel of size `bufferSize`
- Creates a buffered `events` channel of size 100
- Stores `aiBaseURL`
- Returns the struct (does NOT start the worker — caller does that)

---

#### `(q *JobQueue) Start(ctx context.Context)`

- Starts a goroutine that loops on `q.jobs` channel
- For each job received, calls `q.dispatch(ctx, job)`
- Stops when `ctx` is cancelled

---

#### `(q *JobQueue) Enqueue(jobType string, payload map[string]interface{}) error`

- Creates a `Job{Type: jobType, Payload: payload}`
- Sends it to `q.jobs` channel (non-blocking — use `select` with a `default` branch)
- If the channel is full, return an error: `"job queue is full, try again later"`
- Return nil on success

---

#### `(q *JobQueue) dispatch(ctx context.Context, job Job)`

This is the private worker method. It maps job types to AI Engine endpoints and sends them.

**Job type → AI Engine endpoint mapping:**

| Job Type | AI Engine Endpoint |
|---|---|
| `analyze_repo` | `POST /analyze-repo` |
| `compute_fragility` | `POST /compute-fragility` |
| `start_investigation` | `POST /start-investigation` |
| `mentor_query` | `POST /mentor-query` |

**Steps:**
1. Look up the endpoint from the job type — log and return if unknown type
2. Build the full URL: `q.aiBaseURL + endpoint`
3. Marshal `job.Payload` to JSON
4. POST it to the AI Engine using `http.NewRequestWithContext`
5. Log success or failure
6. On success, emit an event to `q.events` channel using a non-blocking send
7. The event format: `Event{ Event: jobType + "_dispatched", RepoID: payload["repo_id"] }`

---

#### `(q *JobQueue) Events() <-chan Event`

Returns the read-only `q.events` channel. This is used by the WebSocket server to stream live updates to the frontend.

---

### Rules for queue.go

- Use only Go standard library
- The `jobs` channel must be buffered — never block the API Gateway
- `dispatch` must never panic — wrap everything in error checks
- Failed dispatches must be logged with `log.Printf` but must NOT crash the worker
- The worker goroutine must respect `ctx.Done()` for clean shutdown
- Do not retry failed jobs in this version (retries are a future enhancement)

---

## `main.go` — Wiring Everything Together

Create a `main.go` at `backend/main.go` that wires up all three packages.

**Steps:**
1. Create a `CloneService` with `BaseDir = "./repos"`
2. Create a `JobQueue` pointing at `http://localhost:8001` (AI Engine URL) with buffer size 50
3. Create a `Gateway` with the clone service and job queue
4. Call `jq.Start(ctx)` to start the background worker
5. Register routes with `gateway.RegisterRoutes(mux)`
6. Start `http.ListenAndServe(":8080", mux)`
7. Handle OS signals (`SIGINT`, `SIGTERM`) for graceful shutdown using `context.WithCancel`

---

## Environment Variables to Support

Read these from environment in `main.go` using `os.Getenv` with the defaults shown:

| Variable | Default | Used By |
|---|---|---|
| `PORT` | `8080` | HTTP server listen port |
| `AI_ENGINE_URL` | `http://localhost:8001` | JobQueue AI base URL |
| `REPOS_DIR` | `./repos` | CloneService BaseDir |

---

## Error Handling Rules (Apply Everywhere)

- Return HTTP 400 for bad input (missing fields, invalid URL, wrong method)
- Return HTTP 500 for internal failures (clone failed, queue full after retry)
- Always log internal errors with `log.Printf("[component] error: %v", err)`
- Never expose raw Go error strings directly in the JSON response to the frontend
- Use the `httpError(w, message, code)` helper from `gateway.go` for all error responses

---

## What You Do NOT Need to Implement

- WebSocket server (separate package, handled later)
- Investigation Manager (separate package, handled later)
- Neo4j or ChromaDB clients (handled later)
- Authentication or API keys
- The Python AI Engine itself

The `/dashboard/{repo_id}` and `/dependency-graph/{repo_id}` responses should return **stubbed/hardcoded JSON** for now. Real data integration comes in a later sprint.

---

## Output Checklist

Before finishing, confirm:

- [ ] `internal/api/gateway.go` — all 8 endpoints implemented
- [ ] `internal/github/clone.go` — `IsValidGitHubURL`, `Clone`, `CloneResult`, `shortHash`
- [ ] `internal/queue/queue.go` — `Job`, `Event`, `JobQueue`, `NewJobQueue`, `Start`, `Enqueue`, `dispatch`, `Events`
- [ ] `main.go` — wires all three packages, reads env vars, handles shutdown
- [ ] All files use only Go standard library (no third-party imports)
- [ ] All handlers return correct HTTP status codes
- [ ] No handler blocks indefinitely — all async work goes through the queue

---

## Summary

You are building the **Go orchestration layer** for IncidentOS. It does not do AI reasoning — it receives requests, clones repos, enqueues work, and hands everything off to the Python AI engine. Keep it simple, reliable, and fast. Every function has one clear job.