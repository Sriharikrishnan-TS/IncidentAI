# IncidentOS LangGraph Orchestration

## Overview

This module preserves both orchestration implementations used by IncidentOS:

1. **Pipeline orchestrator** (`graph/workflow.py`) for the node-by-node incident analysis flow.
2. **Live intelligence orchestrator** (`orchestration/live_orchestrator.py`) for repository + git ingestion and normalized state generation.

Both feed the same shared-state model and support backend callback integration.

## End-to-End Architecture

`Frontend → Backend → LangGraph Orchestrator → Agents → Backend Callbacks`

## Implementations

### 1) Pipeline Orchestrator (`graph/workflow.py`)

Sequential flow:

`START → repository_node → dependency_node → fragility_node → incident_node → mentor_node → END`

It updates shared state at each step (`parsed_repo`, `dependency_graph`, `fragility_scores`, `incidents`, `mentor_context`) and keeps execution logs/status for backend consumption.

### 2) Live Intelligence Orchestrator (`orchestration/live_orchestrator.py`)

Live flow:

`START → repository_agent → git_history_agent → END`

It performs filesystem parsing + git history analysis and standardizes outputs (`services`, `languages`, `frameworks`, `high_churn_services`, `top_contributors`, etc.) for downstream agents and callback handlers.

## Shared State and Callback Compatibility

- Keep shared state updates enabled in every node.
- Keep backend callback payload fields populated from orchestrator state.
- Preserve error/status/log fields so backend can stream progress and completion events.

## Usage

### FastAPI-triggered pipeline

```bash
curl -X POST http://localhost:8000/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_id":"example-repo-123","repo_path":"/path/to/repository"}'
```

### Programmatic (pipeline)

```python
from graph.workflow import execute_workflow

result = execute_workflow(repo_id="example-repo-123", repo_path="/path/to/repository")
```

### Programmatic (live intelligence)

```python
from orchestration.live_orchestrator import execute_orchestrator

state = execute_orchestrator(repo_path="/path/to/repository", repo_id="example-repo-123")
```
