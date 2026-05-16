# IncidentOS Orchestration Layer

This directory contains the LangGraph-based orchestration system for the IncidentOS multi-agent architecture.

## Overview

The orchestration layer provides a deterministic pipeline that coordinates multiple AI agents to analyze repositories, detect incidents, and provide mentorship guidance.

## Architecture

### Components

1. **State Management** (`state.py`)
   - `IncidentState`: TypedDict defining shared state across all nodes
   - Helper functions for state initialization and logging

2. **Orchestration Nodes** (`nodes/`)
   - `repository_node.py`: Parses repository structure
   - `dependency_node.py`: Analyzes code dependencies
   - `fragility_node.py`: Calculates fragility scores
   - `incident_node.py`: Detects potential incidents
   - `mentor_node.py`: Generates mentorship guidance

3. **Workflow** (`../graph/workflow.py`)
   - LangGraph-based deterministic pipeline
   - Sequential execution flow
   - Error handling and logging

## Execution Flow

```
START
  ↓
[Repository Node]
  ↓ (parsed_repo)
[Dependency Node]
  ↓ (dependency_graph)
[Fragility Node]
  ↓ (fragility_scores)
[Incident Node]
  ↓ (incidents)
[Mentor Node]
  ↓ (mentor_context)
END
```

## State Schema

```python
IncidentState = {
    # Input
    "repo_id": str,
    "repo_path": str,

    # Agent Outputs
    "parsed_repo": dict | None,
    "dependency_graph": dict | None,
    "fragility_scores": dict | None,
    "incidents": list[dict] | None,
    "mentor_context": dict | None,

    # Metadata
    "logs": list[dict],
    "status": str,
    "error": str | None,
    "timestamp": str
}
```

## Usage

### Via FastAPI Endpoint

```bash
curl -X POST http://localhost:8000/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "example-repo-123",
    "repo_path": "/path/to/repository"
  }'
```

### Programmatic Usage

```python
from graph.workflow import execute_workflow

result = execute_workflow(
    repo_id="example-repo-123",
    repo_path="/path/to/repository"
)

print(f"Status: {result['status']}")
print(f"Incidents found: {len(result['incidents'])}")
```

## Node Implementation

Each node follows a consistent pattern:

```python
def node_name(state: IncidentState) -> IncidentState:
    """Node description."""

    # 1. Log start
    state = log_node_execution(state, "node_name", "started", "message")

    # 2. Validate prerequisites
    if not state.get("required_field"):
        raise ValueError("required_field is missing")

    # 3. Execute agent logic
    result = agent_function(state["input_data"])

    # 4. Update state
    state["output_field"] = result
    state["status"] = "node_completed"

    # 5. Log completion
    state = log_node_execution(state, "node_name", "completed", "message")

    return state
```

## Adding New Nodes

To add a new node to the pipeline:

1. Create a new file in `orchestration/nodes/`
2. Implement the node function following the pattern above
3. Add the node to `orchestration/nodes/__init__.py`
4. Update `graph/workflow.py` to include the node in the graph
5. Update the state schema if needed

Example:

```python
# orchestration/nodes/new_node.py
from orchestration.state import IncidentState, log_node_execution

def new_node(state: IncidentState) -> IncidentState:
    """New node description."""
    # Implementation here
    return state
```

```python
# graph/workflow.py
from orchestration.nodes import new_node

workflow.add_node("new_node", new_node)
workflow.add_edge("previous_node", "new_node")
workflow.add_edge("new_node", "next_node")
```

## Agent Integration

Currently, nodes use mock implementations. To integrate actual agents:

1. Implement the agent in `agents/<agent_name>/`
2. Update the corresponding node to import and use the agent
3. Remove the mock implementation

Example:

```python
# Before (mock)
parsed_repo = {"mock": "data"}

# After (real agent)
from agents.repository_agent import analyze_repository
parsed_repo = analyze_repository(state["repo_path"])
```

## Logging

All nodes log their execution:

```python
{
    "node": "repository_node",
    "status": "completed",
    "message": "Repository analysis completed",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "data": {"total_files": 42}
}
```

## Error Handling

Nodes handle errors gracefully:

```python
try:
    # Node logic
except Exception as e:
    state["error"] = f"Node failed: {str(e)}"
    state["status"] = "failed"
    state = log_node_execution(state, node_name, "failed", str(e))
```

## Future Enhancements

- [ ] Conditional routing based on analysis results
- [ ] Parallel execution for independent nodes
- [ ] Streaming results for long-running analyses
- [ ] Checkpoint/resume functionality
- [ ] Agent-specific configuration
- [ ] Performance metrics and monitoring
- [ ] Integration with vector stores for context
- [ ] Human-in-the-loop capabilities

## Testing

Run the workflow visualization:

```bash
cd ai-engine
python -m graph.workflow
```

Test the FastAPI endpoint:

```bash
uvicorn main:app --reload
# Visit http://localhost:8000/docs for API documentation
```
