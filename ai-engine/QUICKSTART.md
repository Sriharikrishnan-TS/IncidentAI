# IncidentOS AI Engine - Quick Start Guide

This guide will help you set up and test the LangGraph orchestration layer.

## Prerequisites

- Python 3.10 or higher
- pip package manager

## Installation

1. **Navigate to the ai-engine directory:**

```bash
cd IncidentOS/ai-engine
```

2. **Create a virtual environment (recommended):**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

## Running the Server

Start the FastAPI server:

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

The server will start at `http://localhost:8000`

## Testing the Orchestration Pipeline

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

### 2. View Workflow Visualization

```bash
curl http://localhost:8000/workflow/visualization
```

Or visit in browser: `http://localhost:8000/workflow/visualization`

### 3. Analyze a Repository

**Using curl:**

```bash
curl -X POST http://localhost:8000/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "test-repo-001",
    "repo_path": "/path/to/your/repository"
  }'
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/analyze-repo",
    json={
        "repo_id": "test-repo-001",
        "repo_path": "/path/to/your/repository"
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Incidents: {len(result['incidents'])}")
```

**Expected Response Structure:**

```json
{
  "repo_id": "test-repo-001",
  "status": "completed",
  "parsed_repo": {
    "files": [...],
    "structure": {...},
    "metadata": {...}
  },
  "dependency_graph": {
    "nodes": [...],
    "edges": [...],
    "metrics": {...}
  },
  "fragility_scores": {
    "components": [...],
    "summary": {...}
  },
  "incidents": [
    {
      "id": "INC-001",
      "type": "high_fragility",
      "severity": "high",
      "component": "src/main.py",
      "title": "High fragility score detected",
      "recommendations": [...]
    }
  ],
  "mentor_context": {
    "summary": {...},
    "recommendations": [...],
    "learning_resources": [...],
    "next_steps": [...]
  },
  "logs": [
    {
      "node": "repository_node",
      "status": "completed",
      "message": "Repository analysis completed",
      "timestamp": "2024-01-01T12:00:00.000Z"
    }
  ],
  "error": null
}
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:

- View all available endpoints
- See request/response schemas
- Test endpoints directly in the browser

## Testing the Workflow Programmatically

Create a test script `test_workflow.py`:

```python
"""Test script for the orchestration workflow."""

import logging
from graph.workflow import execute_workflow, get_workflow_visualization

# Configure logging
logging.basicConfig(level=logging.INFO)

# Print workflow structure
print("=" * 60)
print("WORKFLOW STRUCTURE")
print("=" * 60)
print(get_workflow_visualization())

# Test workflow execution
print("\n" + "=" * 60)
print("EXECUTING WORKFLOW")
print("=" * 60)

result = execute_workflow(
    repo_id="test-repo-001",
    repo_path="/path/to/test/repository"
)

print(f"\nStatus: {result['status']}")
print(f"Logs: {len(result['logs'])} entries")

if result.get('incidents'):
    print(f"Incidents: {len(result['incidents'])} found")
    for incident in result['incidents']:
        print(f"  - {incident['id']}: {incident['title']} ({incident['severity']})")

if result.get('mentor_context'):
    recommendations = result['mentor_context'].get('recommendations', [])
    print(f"Recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"  - [{rec['priority']}] {rec['title']}")
```

Run the test:

```bash
python test_workflow.py
```

## Project Structure

```
ai-engine/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── QUICKSTART.md               # This file
│
├── orchestration/              # Orchestration layer
│   ├── __init__.py
│   ├── state.py               # Shared state definition
│   ├── README.md              # Orchestration documentation
│   └── nodes/                 # Orchestration nodes
│       ├── __init__.py
│       ├── repository_node.py
│       ├── dependency_node.py
│       ├── fragility_node.py
│       ├── incident_node.py
│       └── mentor_node.py
│
├── graph/                      # LangGraph workflow
│   ├── __init__.py
│   └── workflow.py            # Workflow definition
│
└── agents/                     # AI agents (to be implemented)
    ├── repository_agent/
    ├── dependency_agent/
    ├── fragility_agent/
    ├── incident_agent/
    └── mentor_agent/
```

## Current Implementation Status

### ✅ Completed

- Shared state management (`IncidentState`)
- All orchestration nodes with mock implementations
- LangGraph deterministic workflow
- FastAPI endpoints
- Comprehensive logging
- Error handling
- API documentation

### 🚧 In Progress (Future Work)

- Actual agent implementations (currently using mocks)
- Integration with real repository parsing
- Advanced dependency analysis
- ML-based fragility scoring
- Intelligent incident detection
- Context-aware mentorship

## Integrating Real Agents

When actual agents are ready, update the nodes:

1. **Remove mock implementation:**

```python
# In orchestration/nodes/repository_node.py

# Remove this:
parsed_repo = {"mock": "data"}

# Add this:
from agents.repository_agent import analyze_repository
parsed_repo = analyze_repository(state["repo_path"])
```

2. **Test the integration:**

```bash
python test_workflow.py
```

3. **Verify the output:**

Check that the agent returns data matching the expected schema.

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running from the `ai-engine` directory:

```bash
cd IncidentOS/ai-engine
python main.py
```

### Port Already in Use

If port 8000 is busy, use a different port:

```bash
uvicorn main:app --reload --port 8001
```

### Module Not Found

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Next Steps

1. **Implement actual agents** in the `agents/` directory
2. **Integrate agents** with orchestration nodes
3. **Add tests** for each component
4. **Configure logging** for production
5. **Add monitoring** and metrics
6. **Deploy** to production environment

## Support

For questions or issues:

- Check the orchestration README: `orchestration/README.md`
- Review the API docs: http://localhost:8000/docs
- Check the logs for detailed execution information

## Example: Complete Test Flow

```bash
# 1. Start the server
uvicorn main:app --reload

# 2. In another terminal, test the endpoint
curl -X POST http://localhost:8000/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "example-repo",
    "repo_path": "/path/to/repo"
  }' | jq .

# 3. Check the logs in the server terminal
# You should see:
# - Repository analysis started
# - Dependency analysis started
# - Fragility analysis started
# - Incident detection started
# - Mentor guidance started
# - All completed successfully
```

## Performance Notes

Current implementation uses mock data, so execution is fast (~100ms).

When real agents are integrated:

- Repository parsing: ~1-5 seconds
- Dependency analysis: ~2-10 seconds
- Fragility scoring: ~1-5 seconds
- Incident detection: ~1-3 seconds
- Mentor guidance: ~2-5 seconds

**Total estimated time: 7-28 seconds** depending on repository size.

Consider implementing:

- Caching for repeated analyses
- Streaming responses for long operations
- Background job processing for large repositories
