# Live Repository Intelligence Orchestrator

## Overview

This module implements a production-ready LangGraph orchestrator that replaces mock data with real filesystem parsing and live Git extraction. It enforces strict data contracts and provides a complete intelligence pipeline for downstream agents.

## Architecture

### Phase 1: Strict Data Standardization
- **TypedDict Contract**: [`AgentState`](live_orchestrator.py:43) enforces type safety across all nodes
- **Validation Decorator**: [`validate_state_output`](live_orchestrator.py:66) sanitizes outputs before returning
- **Safe Defaults**: Auto-corrects malformed data to prevent downstream crashes

### Phase 2: Live Repository Ingestion
- **Real Filesystem Parsing**: Uses `os.walk` to traverse directories
- **Service Detection**: Identifies top-level directories containing code
- **Language Detection**: Maps file extensions to programming languages
- **Framework Detection**: Parses manifest files (package.json, requirements.txt, go.mod)
- **Ignores**: .git, node_modules, venv, __pycache__, etc.

### Phase 3: Live Git History Analysis
- **GitPython Integration**: Real Git repository analysis
- **Commit Metrics**: Analyzes last 100 commits
- **Contributor Tracking**: Identifies top contributors by commit frequency
- **Churn Analysis**: Maps file changes to services for fragility detection
- **Metadata Generation**: Comprehensive repository summary

### Phase 4: LangGraph Orchestration
- **StateGraph**: Manages workflow state transitions
- **Node Wiring**: START → repository_agent → git_history_agent → END
- **Compilation**: Produces executable graph ready for invocation

### Phase 5: Execution & Testing
- **Standalone Execution**: Run directly with `python orchestration/live_orchestrator.py`
- **JSON Output**: Pretty-printed results for verification
- **Error Handling**: Graceful fallbacks on failures

## Usage

### Direct Execution
```bash
cd ai-engine
python orchestration/live_orchestrator.py
```

### Programmatic Usage
```python
from orchestration.live_orchestrator import execute_orchestrator

final_state = execute_orchestrator(
    repo_path="/path/to/repository",
    repo_id="my-repo"
)

print(final_state['services'])
print(final_state['languages'])
print(final_state['high_churn_services'])
```

### Integration with Existing Nodes
```python
from orchestration.live_orchestrator import create_orchestrator

# Create the orchestrator
app = create_orchestrator()

# Initialize state
initial_state = {
    'repo_id': 'test-repo',
    'repo_path': './my-repo',
    'services': [],
    'languages': [],
    'frameworks': [],
    'architecture_summary': '',
    'high_churn_services': [],
    'recent_commits': 0,
    'top_contributors': [],
    'pr_analytics': {},
    'repo_metadata': ''
}

# Execute
final_state = app.invoke(initial_state)
```

## Data Contract

### Input State
```python
{
    'repo_id': str,      # Required: Unique repository identifier
    'repo_path': str,    # Required: Path to repository on disk
}
```

### Output State
```python
{
    'repo_id': str,
    'repo_path': str,
    'services': List[str],              # Detected services
    'languages': List[str],             # Programming languages
    'frameworks': List[str],            # Detected frameworks
    'architecture_summary': str,        # Natural language summary
    'high_churn_services': List[str],   # Services with high change frequency
    'recent_commits': int,              # Number of recent commits analyzed
    'top_contributors': List[str],      # Top 5 contributors
    'pr_analytics': Dict[str, Any],     # PR metrics (placeholder)
    'repo_metadata': str                # Comprehensive metadata summary
}
```

## Dependencies

All dependencies are specified in [`requirements.txt`](../requirements.txt):
- `langgraph>=0.2.45` - Workflow orchestration
- `langchain-core>=0.3.15` - Core abstractions
- `gitpython>=3.1.43` - Git repository analysis

## Error Handling

The orchestrator implements multiple layers of error handling:

1. **Validation Layer**: [`validate_state_output`](live_orchestrator.py:66) decorator ensures type safety
2. **Node-Level**: Each node has try/except with fallback data
3. **Graph-Level**: Compilation errors are caught and logged
4. **Execution-Level**: Top-level error handling with detailed logging

## Testing

The module includes a built-in test execution block:

```bash
cd ai-engine
python orchestration/live_orchestrator.py
```

Expected output:
```json
{
  "repo_id": "IncidentOS",
  "services": ["ai-engine", "backend-go", "frontend"],
  "languages": ["Go", "Python", "TypeScript"],
  "frameworks": ["FastAPI", "LangGraph", "Next.js", "React"],
  "high_churn_services": ["frontend", "backend-go", "ai-engine"],
  "recent_commits": 18,
  "top_contributors": ["Alice", "Bob", "Charlie"]
}
```

## Performance Considerations

- **Filesystem Scanning**: Ignores common build/cache directories
- **Git Analysis**: Limited to last 100 commits for performance
- **Framework Detection**: Only parses manifest files, not full dependency trees
- **Memory Efficient**: Streams data rather than loading entire repository

## Future Enhancements

1. **PR Analytics**: Full implementation of PR and branch churn analysis
2. **Caching**: Repository analysis result caching
3. **Parallel Processing**: Concurrent node execution where possible
4. **Extended Metrics**: Code complexity, test coverage, documentation quality

## Troubleshooting

### GitPython Not Available
```bash
pip install gitpython
```

### LangGraph Not Available
```bash
pip install langgraph
```

### Invalid Repository Path
Ensure the `repo_path` points to a valid directory containing a `.git` folder.

## Contributing

When modifying this orchestrator:
1. Maintain the strict data contract
2. Add validation for new fields
3. Update tests and documentation
4. Ensure backward compatibility

## License

Part of the IncidentOS project.