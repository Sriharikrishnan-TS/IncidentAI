# Extended LangGraph Orchestrator with Backend Callbacks

## Overview

This extended orchestrator builds upon the existing `live_orchestrator.py` by adding:

- **Backend callback integration** for persistence
- **Additional analysis nodes** (dependency, fragility, incident, mentor)
- **Standardized shared state flow** across all nodes
- **Comprehensive logging** with structured output
- **Graceful error handling** without breaking the pipeline

## Architecture

```
Frontend → Backend → LangGraph Orchestrator → Agents → Backend Callbacks → Neo4j/ChromaDB
                                                      ↓
                                              WebSocket Broadcast
```

## Pipeline Flow

```
START
  ↓
repository_agent (filesystem parsing)
  ↓
git_history_agent (Git analysis)
  ↓
dependency_agent (dependency extraction + callback)
  ↓
fragility_agent (fragility scoring + callback)
  ↓
incident_agent (incident generation + callback)
  ↓
mentor_agent (mentor context + callback)
  ↓
END
```

## New Components

### 1. Shared State (`shared_state.py`)

Defines standardized state keys and schemas:

- `StateKeys`: Consistent key names across all nodes
- `DependencyType`: Enum of allowed dependency types
- `DependencySchema`: Backend-compatible dependency format
- Helper functions for schema conversion

### 2. Backend Callback Utility (`backend_callback.py`)

Lightweight async HTTP client for backend callbacks:

- Environment-based configuration
- Async and sync request methods
- Graceful error handling
- No direct backend coupling in agents

### 3. Orchestration Nodes (`nodes/`)

#### `dependency_node.py`

- Extracts dependency graph
- Converts to backend schema
- Sends callback to `/callback/dependencies-extracted`
- Maintains graph in shared state

#### `fragility_node.py`

- Computes fragility scores
- Sends callback to `/callback/fragility-computed`
- Maintains scores in shared state

#### `incident_node.py`

- Generates incident scenarios
- Sends callback to `/callback/incidents-generated`
- Maintains incidents in shared state

#### `mentor_node.py`

- Generates mentor context
- Sends callback to `/callback/mentor-context-ready`
- Maintains context in shared state

### 4. Logging Configuration (`logging_config.py`)

Structured logging with:

- Colored console output
- Node name tracking
- Repository ID tracking
- Timestamp inclusion
- Multiple log levels

## Configuration

### Environment Variables

```bash
# AI Engine
BACKEND_URL=http://localhost:8080
CALLBACK_API_KEY=your-secure-api-key

# Backend (must match)
CALLBACK_API_KEY=your-secure-api-key
```

### Installation

```bash
cd ai-engine
pip install -r requirements.txt
```

New dependency: `httpx==0.27.0`

## Usage

### Run Extended Orchestrator

```bash
cd ai-engine
python orchestration/extended_orchestrator.py
```

### Programmatic Usage

```python
from orchestration.extended_orchestrator import execute_extended_orchestrator

final_state = execute_extended_orchestrator(
    repo_path="/path/to/repository",
    repo_id="my-repo"
)

# Access results
print(final_state['dependency_graph'])
print(final_state['fragility_scores'])
print(final_state['incidents'])
print(final_state['mentor_context'])
```

## Shared State Contract

All nodes use consistent state keys defined in `StateKeys`:

### Core Identifiers

- `repo_id`: Repository identifier
- `repo_path`: Repository path

### Repository Metadata

- `repository_metadata`: Metadata summary
- `services`: Detected services
- `languages`: Programming languages
- `frameworks`: Detected frameworks
- `architecture_summary`: Architecture description

### Analysis Results

- `dependency_graph`: Dependency relationships
- `fragility_scores`: Service fragility scores
- `incidents`: Incident scenarios
- `mentor_context`: Mentor insights

### Git History

- `high_churn_services`: High-churn services
- `recent_commits`: Commit count
- `top_contributors`: Top contributors
- `pr_analytics`: PR analytics

### Logging

- `logs`: Structured log entries
- `status`: Current workflow status

## Backend Callback Endpoints

### 1. Dependencies Extracted

```http
POST /callback/dependencies-extracted
Content-Type: application/json
X-API-Key: <CALLBACK_API_KEY>

{
  "repo_id": "repo_123",
  "dependencies": [
    {
      "source": "service-a",
      "target": "service-b",
      "type": "DEPENDS_ON"
    }
  ],
  "timestamp": "2026-05-17T07:30:00Z"
}
```

### 2. Fragility Computed

```http
POST /callback/fragility-computed
Content-Type: application/json
X-API-Key: <CALLBACK_API_KEY>

{
  "repo_id": "repo_123",
  "fragility_scores": [
    {
      "service": "auth-service",
      "score": 8.7,
      "reasons": ["high commit churn"]
    }
  ],
  "timestamp": "2026-05-17T07:31:00Z"
}
```

### 3. Incidents Generated

```http
POST /callback/incidents-generated
Content-Type: application/json
X-API-Key: <CALLBACK_API_KEY>

{
  "repo_id": "repo_123",
  "incidents": [
    {
      "id": "INC-001",
      "title": "Potential failure in auth-service",
      "severity": "HIGH",
      "affected_services": ["auth-service"]
    }
  ],
  "timestamp": "2026-05-17T07:32:00Z"
}
```

### 4. Mentor Context Ready

```http
POST /callback/mentor-context-ready
Content-Type: application/json
X-API-Key: <CALLBACK_API_KEY>

{
  "repo_id": "repo_123",
  "mentor_context": {
    "summary": "Repository analysis complete",
    "insights": [...],
    "recommendations": [...]
  },
  "timestamp": "2026-05-17T07:33:00Z"
}
```

## Error Handling

### Callback Failures

- **Non-blocking**: Pipeline continues even if callbacks fail
- **Logged as warnings**: Failures recorded in shared state logs
- **Graceful degradation**: Analysis completes without persistence

### Critical Failures

- Node-level errors return safe defaults
- Workflow may stop on critical failures
- All errors logged with full context

## Dependency Types

Allowed types for Neo4j relationships:

- `DEPENDS_ON` - General dependency
- `IMPORTS` - Code import
- `CALLS` - Function/API call
- `USES` - Resource usage
- `COMMUNICATES_WITH` - Service communication
- `READS_FROM` - Data read
- `WRITES_TO` - Data write
- `PUBLISHES_TO` - Event publishing
- `SUBSCRIBES_TO` - Event subscription

## Integration with Real Agents

Current nodes use mock data that can be easily replaced:

### Example: Replace Mock Dependency Extraction

```python
# In dependency_node.py

def _extract_dependencies_real(repo_path, state):
    from agents.dependency_agent import DependencyGraphManager

    manager = DependencyGraphManager()

    # Build input from repository analysis
    input_data = {
        "services": [
            {"name": service, "imports": [...]}
            for service in state.get(StateKeys.SERVICES, [])
        ]
    }

    # Process dependencies
    result = manager.process(input_data, dry_run=True)

    # Convert to mock format for schema conversion
    dependencies = []
    for dep in result.extracted_dependencies:
        for target in dep.depends_on:
            dependencies.append({
                "from": dep.service,
                "to": target,
                "type": "depends_on"
            })

    return dependencies
```

## Testing

### Without Backend

```bash
# Callbacks will be skipped but analysis runs
python orchestration/extended_orchestrator.py
```

### With Backend

```bash
# Set environment variables
export BACKEND_URL=http://localhost:8080
export CALLBACK_API_KEY=your-key

# Run orchestrator
python orchestration/extended_orchestrator.py
```

## Logging Output

```
2026-05-17 13:30:00 INFO     [repository_agent] [repo_id=IncidentOS] Started repository analysis
2026-05-17 13:30:01 INFO     [repository_agent] [repo_id=IncidentOS] Detected 3 services
2026-05-17 13:30:02 INFO     [dependency_agent] [repo_id=IncidentOS] Started dependency analysis
2026-05-17 13:30:03 INFO     [dependency_agent] [repo_id=IncidentOS] Backend callback successful
2026-05-17 13:30:04 INFO     [fragility_agent] [repo_id=IncidentOS] Computed fragility scores
```

## Future Enhancements

1. **Real Agent Integration**: Replace mock implementations with actual agents
2. **Parallel Execution**: Run independent nodes concurrently
3. **Caching**: Cache analysis results for faster re-runs
4. **Retry Logic**: Add retry mechanism for failed callbacks
5. **Metrics**: Track execution time and success rates

## Troubleshooting

### httpx Not Available

```bash
pip install httpx==0.27.0
```

### Callbacks Not Working

1. Check environment variables are set
2. Verify backend is running
3. Check API key matches
4. Review logs for error messages

### LangGraph Errors

```bash
pip install langgraph==0.2.45
```

## Documentation

See `contracts.md` for complete API contracts and communication flows.

## License

Part of the IncidentOS project.
