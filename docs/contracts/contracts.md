# IncidentOS — API Contracts & Workflow Blueprint

## Purpose

This document defines the communication contracts between all major services/modules inside IncidentOS.

The goal is to:

- allow parallel development
- avoid integration conflicts
- define stable interfaces
- standardize input/output formats
- enable frontend, backend, and AI teams to work independently

This is NOT production-grade API documentation. This is the hackathon communication blueprint.

---

# System Services

## 1. Frontend (Next.js)

Responsible for:

- UI
- dashboard
- mentor chat
- investigation visualization
- graph visualization

---

## 2. Backend (Golang)

Responsible for:

- API gateway
- repository ingestion
- orchestration
- websocket events
- investigation lifecycle

---

## 3. AI Engine (Python + LangGraph)

Responsible for:

- repository intelligence
- dependency extraction
- fragility scoring
- mentor reasoning
- incident investigation
- memory-aware reasoning

---

## 4. Engineering Memory Layer

### ChromaDB

Stores:

- embeddings
- semantic memory
- incident summaries
- mentor memory

### Neo4j

Stores:

- dependency graph
- service relationships
- architecture graph

---

# Workflow 1 — Upload Repository

## Purpose

Upload and register a GitHub repository.

### Frontend → Backend

#### Endpoint

```http
POST /upload-repo
````

#### Request

```json
{
  "repo_url": "https://github.com/user/repo"
}
```

#### Response

```json
{
  "repo_id": "repo_123",
  "status": "uploaded"
}
```

### Backend Responsibilities

* validate GitHub URL
* create repository ID
* clone repository
* store repository metadata
* trigger AI analysis workflow

---

# Workflow 2 — Clone Repository

## Purpose

Clone repository locally for analysis.

### Backend Internal Service

#### Input

```json
{
  "repo_id": "repo_123",
  "repo_url": "https://github.com/user/repo"
}
```

#### Output

```json
{
  "repo_id": "repo_123",
  "repo_path": "./repos/repo_123",
  "status": "cloned"
}
```

---

# Workflow 3 — Analyze Repository

## Purpose

Start repository intelligence workflow.

### Backend → AI Engine

#### Endpoint

```http
POST /analyze-repo
```

#### Request

```json
{
  "repo_id": "repo_123",
  "repo_path": "./repos/repo_123"
}
```

#### Response

```json
{
  "repo_id": "repo_123",
  "status": "analysis_started"
}
```

### AI Engine Responsibilities

* parse repository
* analyze architecture
* extract dependencies
* analyze commit history
* generate embeddings
* build memory graph

---

# Workflow 4 — Repository Parsing

## Purpose

Extract repository structure and architecture.

### Repository Agent Output

```json
{
  "repo_id": "repo_123",
  "services": [
    "auth-service",
    "payment-service",
    "checkout-service"
  ],
  "languages": [
    "Python",
    "TypeScript"
  ],
  "frameworks": [
    "FastAPI",
    "Next.js"
  ]
}
```

---

# Workflow 5 — Dependency Graph Generation

## Purpose

Build service/module dependency graph.

### Dependency Agent Output

```json
{
  "repo_id": "repo_123",
  "dependencies": [
    {
      "source": "checkout-service",
      "target": "auth-service",
      "type": "DEPENDS_ON"
    },
    {
      "source": "payment-service",
      "target": "auth-service",
      "type": "DEPENDS_ON"
    }
  ]
}
```

## Neo4j Storage Structure

### Nodes

* Service
* Module
* API
* Repository
* Incident

### Relationships

* DEPENDS_ON
* CALLS
* IMPORTS
* AFFECTED_BY

---

# Workflow 6 — Git History Analysis

## Purpose

Analyze repository evolution.

### Git History Agent Output

```json
{
  "repo_id": "repo_123",
  "high_churn_services": [
    "auth-service"
  ],
  "recent_commits": 124,
  "top_contributors": [
    "dev1",
    "dev2"
  ]
}
```

---

# Workflow 7 — Fragility Analysis

## Purpose

Identify unstable/high-risk services.

### Backend → AI Engine

#### Endpoint

```http
POST /compute-fragility
```

#### Request

```json
{
  "repo_id": "repo_123"
}
```

### AI Engine → Backend

#### Response

```json
{
  "repo_id": "repo_123",
  "fragility_scores": [
    {
      "service": "auth-service",
      "score": 8.7,
      "reasons": [
        "high commit churn",
        "high dependency centrality",
        "recent regressions"
      ]
    },
    {
      "service": "payment-service",
      "score": 4.3,
      "reasons": [
        "moderate churn"
      ]
    }
  ]
}
```

## Fragility Inputs

Signals used:

* commit churn
* dependency centrality
* incident frequency
* reverted commits
* flaky tests
* maintainer concentration

---

# Workflow 8 — Memory Storage

## Purpose

Persist repository intelligence.

### ChromaDB Stores

* incident embeddings
* RCA summaries
* mentor knowledge
* repository summaries
* onboarding notes
* architecture summaries

### Example ChromaDB Document

```json
{
  "document": "OAuth migration caused JWT regression",
  "metadata": {
    "repo_id": "repo_123",
    "service": "auth-service"
  }
}
```

### Neo4j Stores

* dependency graph
* architecture graph
* service relationships
* module relationships

---

# Workflow 9 — Dashboard Data Retrieval

## Purpose

Fetch dashboard information.

### Frontend → Backend

#### Endpoint

```http
GET /dashboard/{repo_id}
```

### Backend → Frontend

#### Response

```json
{
  "repo_id": "repo_123",
  "services": 12,
  "dependencies": 38,
  "fragile_services": [
    "auth-service",
    "checkout-service"
  ],
  "recent_incidents": 4
}
```

---

# Workflow 10 — Dependency Graph Visualization

## Purpose

Display dependency graph in frontend.

### Frontend → Backend

#### Endpoint

```http
GET /dependency-graph/{repo_id}
```

### Backend → Frontend

#### Response

```json
{
  "nodes": [
    {
      "id": "auth-service",
      "type": "service"
    }
  ],
  "edges": [
    {
      "source": "checkout-service",
      "target": "auth-service"
    }
  ]
}
```

---

# Workflow 11 — Incident Investigation

## Purpose

Investigate CI/CD or repository failures.

### Frontend → Backend

#### Endpoint

```http
POST /start-investigation
```

#### Request

```json
{
  "repo_id": "repo_123",
  "incident": "checkout-service CI failed"
}
```

### Backend → AI Engine

#### Request

```json
{
  "repo_id": "repo_123",
  "incident": "checkout-service CI failed"
}
```

### AI Engine → Backend

#### Response

```json
{
  "root_cause": "JWT validation regression",
  "affected_services": [
    "auth-service",
    "checkout-service"
  ],
  "confidence": 0.87,
  "historical_match": "OAuth migration incident"
}
```

---

# Workflow 12 — Mentor Mode

## Purpose

Provide onboarding and repository guidance.

### Frontend → Backend

#### Endpoint

```http
POST /mentor-query
```

#### Request

```json
{
  "repo_id": "repo_123",
  "question": "What should I learn first?"
}
```

### Backend → AI Engine

#### Request

```json
{
  "repo_id": "repo_123",
  "question": "What should I learn first?"
}
```

### AI Engine → Backend

#### Response

```json
{
  "answer": "Start with auth-service because it is central to the architecture and is depended on by multiple services."
}
```

---

# Workflow 13 — WebSocket Live Updates

## Purpose

Send live progress updates to frontend.

### Backend → Frontend

#### WebSocket Events

```json
{
  "event": "repo_analysis_started"
}
```

```json
{
  "event": "dependency_graph_generated"
}
```

```json
{
  "event": "fragility_analysis_complete"
}
```

```json
{
  "event": "investigation_complete"
}
```

---

# Workflow 14 — Final RCA Report

## Purpose

Generate final investigation report.

### AI Engine → Backend

#### Response

```json
{
  "incident": "checkout-service CI failed",
  "root_cause": "JWT validation regression",
  "affected_services": [
    "auth-service",
    "checkout-service"
  ],
  "fragility_score": 8.7,
  "historical_correlation": "OAuth migration incident",
  "recommended_actions": [
    "rollback recent auth changes",
    "add JWT integration tests"
  ]
}
```

---

# Frontend Pages

## Main Pages

* `/upload`
* `/dashboard`
* `/investigation`
* `/mentor`
* `/graphs`
* `/fragility`

---

# Database Responsibilities

| Database | Responsibility                  |
| -------- | ------------------------------- |
| ChromaDB | semantic memory & embeddings    |
| Neo4j    | dependency & architecture graph |

---

# MVP Priority Workflows

## MUST HAVE

1. Upload repository
2. Analyze repository
3. Generate dependency graph
4. Compute fragility score
5. Mentor query
6. One incident investigation flow

## NICE TO HAVE

* websocket live updates
* advanced onboarding insights
* historical incident replay
* contributor analytics
* architectural evolution timeline

---

# Final Notes

This document acts as the communication blueprint for the entire project.

All teams should:

* follow these contracts
* avoid changing JSON formats frequently
* communicate contract updates clearly
* prioritize integration stability

## Core Philosophy

* Define interfaces first.
* Build modules independently.
* Integrate continuously.

---

# Teamwise Internal Interaction Flow

This section explains the internal interaction/dependency flow inside each team.

It defines:

* which modules communicate internally
* which modules depend on other modules
* execution/data flow between components

This is mainly for:

* integration clarity
* ownership clarity
* LangGraph workflow understanding
* backend orchestration understanding
* frontend integration understanding

---

# Frontend Team Interaction Flow

## Frontend Layer

### Repo Upload UI

#### Connects To

* Backend API Gateway
* Upload Repository API

#### Sends

* GitHub repository URL

#### Receives

* repo_id
* upload status

---

### Dashboard UI

#### Connects To

* Backend API Gateway
* Dashboard APIs
* WebSocket Server

#### Receives

* fragility scores
* service counts
* incident summaries
* repository analytics

---

### Dependency Graph Viewer

#### Connects To

* Backend API Gateway
* Dependency Graph API

#### Receives

* graph nodes
* graph edges
* dependency relationships

---

### Mentor Chat UI

#### Connects To

* Backend API Gateway
* Mentor APIs

#### Sends

* mentor questions

#### Receives

* onboarding guidance
* architecture explanations
* learning recommendations

---

### Investigation Timeline UI

#### Connects To

* Backend API Gateway
* Investigation APIs
* WebSocket Server

#### Receives

* investigation progress
* RCA reports
* affected services
* remediation suggestions

---

# Backend Team Interaction Flow

## API Gateway

### Connects To

* Frontend
* Repo Clone Service
* Investigation Manager
* AI Engine
* WebSocket Server

### Responsibilities

* handle frontend requests
* trigger workflows
* send responses
* coordinate services

---

## Repo Clone Service

### Connects To

* GitHub repositories
* local repository storage
* API Gateway

### Sends

* local repo path
* clone status

---

## Investigation Manager

### Connects To

* API Gateway
* AI Engine
* Job Queue
* WebSocket Server

### Responsibilities

* manage investigations
* track workflow progress
* coordinate async execution

---

## Job Queue

### Connects To

* Investigation Manager
* AI Engine

### Responsibilities

* async task execution
* workflow scheduling
* background jobs

---

## WebSocket Server

### Connects To

* Frontend
* Investigation Manager
* API Gateway

### Responsibilities

* live updates
* progress streaming
* dashboard refresh events

---

# AI Team Interaction Flow

## Repository Agent

### Connects To

* Tree-sitter
* GitPython
* Dependency Agent
* Mentor Agent
* ChromaDB

### Sends Output To

* Dependency Agent
* Mentor Agent
* ChromaDB

### Responsibilities

* parse repository
* extract architecture
* identify services/modules
* generate repository summaries

---

## Git History Agent

### Connects To

* GitPython
* Fragility Agent
* ChromaDB

### Sends Output To

* Fragility Agent
* ChromaDB
* Reflection Agent

### Responsibilities

* analyze commit history
* detect high churn services
* extract contributor patterns

---

## Dependency Agent

### Connects To

* Repository Agent
* Neo4j
* Fragility Agent
* Incident Agent

### Sends Output To

* Neo4j
* Fragility Agent
* Incident Agent

### Responsibilities

* generate dependency graph
* compute service relationships
* detect architectural bottlenecks

---

## Incident Agent

### Connects To

* Semgrep
* Dependency Agent
* Reflection Agent
* ChromaDB

### Sends Output To

* Reflection Agent
* Synthesis Agent

### Responsibilities

* parse CI/CD failures
* analyze stack traces
* investigate regressions

---

## Fragility Agent

### Connects To

* Git History Agent
* Dependency Agent
* Neo4j
* ChromaDB
* Reflection Agent

### Sends Output To

* Reflection Agent
* Frontend Dashboard

### Responsibilities

* compute fragility scores
* identify risky services
* detect unstable architecture

---

## Mentor Agent

### Connects To

* Repository Agent
* ChromaDB
* Backend API Gateway

### Reads From

* repository summaries
* onboarding memory
* architecture memory

### Responsibilities

* onboarding guidance
* architecture explanation
* mentor Q&A

---

## Reflection Agent

### Connects To

* Incident Agent
* Fragility Agent
* ChromaDB
* Synthesis Agent

### Responsibilities

* validate AI reasoning
* cross-check findings
* correlate historical incidents
* compute confidence scores

---

## Synthesis Agent

### Connects To

* Reflection Agent
* Backend API Gateway
* Frontend

### Responsibilities

* generate final RCA
* generate remediation plans
* produce final AI summaries

---

# Service Interaction Map

This section defines which services/modules communicate with each other.

---

## Frontend (Next.js)

### Connects To

* Backend API Gateway
* WebSocket Server
* Mentor Agent (through backend)
* Fragility Analysis APIs
* Dependency Graph APIs
* Investigation APIs

### Responsibilities

* Upload repository
* Display dashboard
* Show dependency graph
* Show fragility analysis
* Display RCA reports
* Mentor chat interface
* Live investigation updates

---

## Backend API Gateway (Golang)

### Connects To

* Frontend
* Repo Clone Service
* Investigation Manager
* WebSocket Server
* Python AI Engine
* Neo4j
* ChromaDB

### Responsibilities

* Handle frontend requests
* Trigger repository analysis
* Manage investigation lifecycle
* Send AI requests
* Return dashboard data
* Stream websocket updates

---

## Repo Clone Service

### Connects To

* GitHub repositories
* Backend API Gateway
* Local repository storage

### Responsibilities

* Clone repositories
* Pull latest changes
* Store local repository copies
* Provide repository path to AI engine

---

## Investigation Manager

### Connects To

* Backend API Gateway
* AI Engine
* Job Queue
* WebSocket Server

### Responsibilities

* Start investigations
* Track investigation state
* Coordinate investigation workflow
* Trigger AI reasoning pipeline

---

## WebSocket Server

### Connects To

* Frontend
* Investigation Manager
* Backend API Gateway

### Responsibilities

* Send live progress updates
* Stream investigation status
* Push dashboard updates

---

## Repository Agent

### Connects To

* Tree-sitter
* GitPython
* ChromaDB
* Dependency Agent
* Backend API Gateway

### Responsibilities

* Parse repository structure
* Detect services/modules
* Extract architecture information
* Generate repository summaries

---

## Git History Agent

### Connects To

* GitPython
* ChromaDB
* Fragility Agent
* Repository Agent

### Responsibilities

* Analyze commit history
* Detect high churn modules
* Analyze repository evolution
* Extract contributor patterns

---

## Dependency Agent

### Connects To

* Tree-sitter
* Neo4j
* Fragility Agent
* Incident Agent

### Responsibilities

* Build dependency graph
* Extract service relationships
* Compute dependency centrality
* Generate architecture graph

---

## Incident Agent

### Connects To

* Semgrep
* Neo4j
* ChromaDB
* Reflection Agent
* Dependency Agent

### Responsibilities

* Parse CI/CD failures
* Analyze stack traces
* Detect regressions
* Perform incident reasoning

---

## Fragility Agent

### Connects To

* Git History Agent
* Dependency Agent
* ChromaDB
* Neo4j
* Reflection Agent

### Responsibilities

* Compute fragility scores
* Analyze risk signals
* Detect unstable services
* Identify architectural bottlenecks

---

## Mentor Agent

### Connects To

* ChromaDB
* Repository Agent
* Backend API Gateway
* Frontend

### Responsibilities

* Answer onboarding questions
* Explain architecture
* Recommend learning paths
* Provide repository guidance

---

## Reflection Agent

### Connects To

* Incident Agent
* Fragility Agent
* ChromaDB
* Synthesis Agent

### Responsibilities

* Cross-check AI findings
* Validate reasoning
* Compute confidence scores
* Correlate historical incidents

---

## Synthesis Agent

### Connects To

* Reflection Agent
* Backend API Gateway
* Frontend

### Responsibilities

* Generate final RCA
* Generate investigation summary
* Produce remediation suggestions
* Create final AI response

---

## Tree-sitter

### Connects To

* Repository Agent
* Dependency Agent

### Responsibilities

* AST parsing
* Import extraction
* Function/class extraction
* Repository structure parsing

---

## GitPython

### Connects To

* Git History Agent
* Repository Agent

### Responsibilities

* Commit history extraction
* Repository evolution analysis
* Branch/PR analysis

---

## Semgrep

### Connects To

* Incident Agent
* Fragility Agent

### Responsibilities

* Static analysis
* Risky pattern detection
* Code smell analysis
* Security/static checks

---

## ChromaDB

### Connects To

* Repository Agent
* Git History Agent
* Incident Agent
* Fragility Agent
* Mentor Agent
* Reflection Agent

### Responsibilities

* Store embeddings
* Store semantic memory
* Historical incident retrieval
* Similarity search
* Repository knowledge retrieval

---

## Neo4j

### Connects To

* Dependency Agent
* Incident Agent
* Fragility Agent
* Backend API Gateway

### Responsibilities

* Store dependency graph
* Store architecture graph
* Service relationship traversal
* Blast radius analysis

---

## Docker / DevOps Layer

### Connects To

* Frontend
* Backend
* AI Engine
* Neo4j
* ChromaDB

### Responsibilities

* Container orchestration
* Deployment
* Environment management
* CI/CD
* Monitoring/logging
