# IncidentOS AI Engine

AI-powered repository analysis and incident detection system with LangGraph orchestration.

## Overview

The IncidentOS AI Engine provides a deterministic orchestration pipeline that coordinates multiple AI agents to:

- Parse and analyze repository structure
- Build dependency graphs
- Calculate code fragility scores
- Detect potential incidents and issues
- Generate mentorship guidance and recommendations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                    (main.py - Port 8000)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Orchestration                     │
│                   (graph/workflow.py)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Repository  │  │ Dependency  │  │  Fragility  │
│    Node     │→ │    Node     │→ │    Node     │
└─────────────┘  └─────────────┘  └─────────────┘
                                          │
                         ┌────────────────┘
                         ▼
                  ┌─────────────┐  ┌─────────────┐
                  │  Incident   │→ │   Mentor    │
                  │    Node     │  │    Node     │
                  └─────────────┘  └─────────────┘
```

## Quick Start

### Installation

```bash
cd ai-engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn main:app --reload
```

Server will start at: http://localhost:8000

### Test the Pipeline

```bash
# Run test suite
python test_orchestration.py

# Or test via API
curl -X POST http://localhost:8000/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "test-001", "repo_path": "/path/to/repo"}'
```

## Project Structure

```
ai-engine/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── QUICKSTART.md               # Detailed setup guide
├── test_orchestration.py       # Test suite
│
├── orchestration/              # Orchestration layer
│   ├── state.py               # Shared state (IncidentState)
│   ├── README.md              # Orchestration documentation
│   └── nodes/                 # Orchestration nodes
│       ├── repository_node.py  # Repository parsing
│       ├── dependency_node.py  # Dependency analysis
│       ├── fragility_node.py   # Fragility scoring
│       ├── incident_node.py    # Incident detection
│       └── mentor_node.py      # Mentorship guidance
│
├── graph/                      # LangGraph workflow
│   └── workflow.py            # Workflow definition & execution
│
├── agents/                     # AI agents (to be implemented)
│   ├── repository_agent/      # Repository parsing agent
│   ├── dependency_agent/      # Dependency analysis agent
│   ├── fragility_agent/       # Fragility scoring agent
│   ├── incident_agent/        # Incident detection agent
│   └── mentor_agent/          # Mentorship agent
│
├── memory/                     # Memory management (future)
├── reasoning/                  # Reasoning capabilities (future)
└── parsers/                    # Code parsers (future)
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns server health status.

### Analyze Repository

```bash
POST /analyze-repo
Content-Type: application/json

{
  "repo_id": "unique-repo-id",
  "repo_path": "/path/to/repository"
}
```

Executes the complete analysis pipeline and returns:

- Repository structure and metadata
- Dependency graph
- Fragility scores
- Detected incidents
- Mentorship recommendations
- Execution logs

### Workflow Visualization

```bash
GET /workflow/visualization
```

Returns a visual representation of the orchestration pipeline.

## Orchestration Pipeline

The pipeline executes in a deterministic sequence:

1. **Repository Node** - Parses repository structure
   - Input: `repo_id`, `repo_path`
   - Output: `parsed_repo`

2. **Dependency Node** - Analyzes code dependencies
   - Input: `parsed_repo`
   - Output: `dependency_graph`

3. **Fragility Node** - Calculates fragility scores
   - Input: `dependency_graph`
   - Output: `fragility_scores`

4. **Incident Node** - Detects potential incidents
   - Input: `fragility_scores`
   - Output: `incidents`

5. **Mentor Node** - Generates mentorship guidance
   - Input: `incidents`
   - Output: `mentor_context`

## State Management

All nodes share a common `IncidentState` that flows through the pipeline:

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

## Current Implementation Status

### ✅ Completed

- [x] Shared state management
- [x] LangGraph orchestration pipeline
- [x] All orchestration nodes (with mock data)
- [x] FastAPI endpoints
- [x] Comprehensive logging
- [x] Error handling
- [x] API documentation
- [x] Test suite
- [x] Documentation

### 🚧 To Be Implemented

- [ ] Actual agent implementations
- [ ] Real repository parsing
- [ ] Advanced dependency analysis
- [ ] ML-based fragility scoring
- [ ] Intelligent incident detection
- [ ] Context-aware mentorship
- [ ] Vector store integration
- [ ] Streaming responses
- [ ] Background job processing

## Integrating Real Agents

When agents are ready, update the corresponding nodes:

```python
# Example: orchestration/nodes/repository_node.py

# Remove mock implementation
# parsed_repo = {"mock": "data"}

# Add real agent
from agents.repository_agent import analyze_repository
parsed_repo = analyze_repository(state["repo_path"])
```

## Development

### Running Tests

```bash
# Run orchestration tests
python test_orchestration.py

# Run with verbose logging
python test_orchestration.py --verbose
```

### Adding New Nodes

1. Create node file in `orchestration/nodes/`
2. Implement node function following the pattern
3. Add to `orchestration/nodes/__init__.py`
4. Update `graph/workflow.py` to include in pipeline
5. Update state schema if needed

See `orchestration/README.md` for detailed instructions.

### API Development

The FastAPI server includes automatic documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Dependencies

- **FastAPI** - Web framework
- **LangGraph** - Orchestration framework
- **LangChain** - AI agent framework
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

See `requirements.txt` for complete list.

## Configuration

Environment variables (create `.env` file):

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO

# Future: AI model configuration
# OPENAI_API_KEY=your-key-here
# MODEL_NAME=gpt-4
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

Logs are included in the API response and written to stdout.

## Error Handling

The pipeline handles errors gracefully:

- Node failures are logged
- Error messages are included in response
- Pipeline status reflects failure
- Partial results are preserved

## Performance

Current implementation (with mocks):

- Execution time: ~100ms
- Memory usage: Minimal

Expected with real agents:

- Execution time: 7-28 seconds (depending on repo size)
- Memory usage: Moderate (depends on repo size)

## Future Enhancements

- [ ] Conditional routing based on analysis results
- [ ] Parallel execution for independent nodes
- [ ] Streaming results for long-running analyses
- [ ] Checkpoint/resume functionality
- [ ] Agent-specific configuration
- [ ] Performance metrics and monitoring
- [ ] Integration with vector stores
- [ ] Human-in-the-loop capabilities
- [ ] Multi-repository analysis
- [ ] Historical trend analysis

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Detailed setup and testing
- [Orchestration README](orchestration/README.md) - Orchestration layer details
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)

## Contributing

When contributing new agents or nodes:

1. Follow the existing node pattern
2. Include comprehensive logging
3. Handle errors gracefully
4. Update documentation
5. Add tests
6. Ensure type hints are correct

## License

[Add license information]

## Support

For questions or issues:

- Check the documentation
- Review the test suite
- Examine the logs
- Open an issue on GitHub

---

**Built with ❤️ for better code quality and developer mentorship**
