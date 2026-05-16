# Git History Agent

## Overview

The Git History Agent is the second node in the IncidentOS LangGraph workflow (Workflow 6). It analyzes git repository history to identify high-churn services, track recent commit activity, and identify top contributors. Additionally, it generates comprehensive memory reports and persists them to ChromaDB for long-term retrieval.

## Implementation Details

### Core Functionality

The agent implements the following analysis pipeline:

1. **Commit Iteration**: Analyzes the last 100 commits using `repo.iter_commits(max_count=100)`
2. **Contributor Tracking**: Counts unique commit authors to determine top contributors
3. **Commit Counting**: Tracks total number of commits for the `recent_commits` metric
4. **High-Churn Analysis**: Uses `commit.stats.files` to identify which service folders are modified most frequently

### State Contract

The agent extends the `AgentState` TypedDict with three new keys:

```python
high_churn_services: List[str]  # Top 3 services by change frequency
recent_commits: int              # Total commits analyzed (last 100)
top_contributors: List[str]      # Top 5 contributors by commit count
```

### Node Function

```python
def git_history_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes git repository history to extract churn and contributor metrics.
    
    Args:
        state: Current AgentState containing repo_path and services list
        
    Returns:
        Dictionary with high_churn_services, recent_commits, and top_contributors
    """
```

## Defensive Design

The implementation includes robust error handling:

1. **Git Repository Validation**: Wraps `git.Repo()` initialization in try/except to handle non-git directories
2. **Fallback Data**: Returns hackathon-friendly dummy metrics if git analysis fails
3. **Optional GitPython**: Gracefully handles missing GitPython dependency
4. **Path Validation**: Checks for empty or nonexistent repository paths

### Fallback Data

When git analysis fails, the agent returns:

```python
{
    "high_churn_services": ["frontend", "backend-go", "ai-engine"],
    "recent_commits": 42,
    "top_contributors": [
        "Alice Developer",
        "Bob Engineer", 
        "Charlie Coder",
        "Diana Designer",
        "Eve Architect"
    ]
}
```

## Algorithm Details

### High-Churn Service Detection

For each commit:
1. Extract modified files using `commit.stats.files` (returns dict of filepath: stats)
2. Map each file path to a service by checking if path starts with service name
3. Increment change counter for that service
4. Return top 3 services by change frequency

### Service Mapping

```python
def _map_file_to_service(file_path: str, services: List[str]) -> str:
    """Maps a file path to a service name based on directory structure."""
    # Normalize path separators
    file_path = file_path.replace('\\', '/')
    
    # Check if first directory matches any service
    first_dir = file_path.split('/')[0]
    if first_dir in services:
        return first_dir
    
    return ""
```

## Usage Example

```python
from agents.git_history_agent import git_history_agent_node
from graph.state import AgentState

# Create state with repository info
state: AgentState = {
    "repo_id": "my-repo",
    "repo_path": "/path/to/repo",
    "services": ["frontend", "backend", "api"],
    "languages": ["Python", "TypeScript"],
    "frameworks": ["FastAPI", "React"],
    "high_churn_services": [],
    "recent_commits": 0,
    "top_contributors": [],
}

# Run the agent
result = git_history_agent_node(state)

# Result contains:
# {
#     "high_churn_services": ["frontend", "api", "backend"],
#     "recent_commits": 87,
#     "top_contributors": ["John Doe", "Jane Smith", ...]
# }
```

## ChromaDB Integration

### Memory Report Generation

After analyzing both repository structure and git history, the agent generates a comprehensive textual engineering memory report:

```
Repository {repo_id} contains services: {services}.
The codebase uses {languages} with frameworks: {frameworks}.
Analysis of the last {recent_commits} commits shows that high risk churn is isolated to: {high_churn_services}.
Top authors are: {top_contributors}.
This repository shows {activity_level} development activity.
```

### Vector Persistence

The memory report is automatically persisted to ChromaDB with:

1. **ChromaDB Client**: Connects to `localhost:8000` (Docker infrastructure)
2. **Collection**: `repository_memory`
3. **Document ID**: `{repo_id}_onboarding`
4. **Metadata**:
   - `repo_id`: Unique repository identifier
   - `type`: "onboarding_summary"
   - `services`: Comma-separated service list
   - `languages`: Comma-separated language list
   - `frameworks`: Comma-separated framework list
   - `high_churn_services`: Comma-separated high-churn services
   - `recent_commits`: Total commits analyzed
   - `top_contributors`: Top 3 contributors

### Defensive Design

- **Non-blocking**: ChromaDB failures don't crash the pipeline
- **Network Timeout Handling**: All network errors are caught and logged
- **Optional Dependency**: Works without ChromaDB installed
- **Graceful Degradation**: Continues workflow even if persistence fails

### ChromaDB Setup

Start ChromaDB server using Docker:

```bash
docker-compose up chromadb
```

Or run ChromaDB standalone:

```bash
chroma run --host localhost --port 8000
```

## Dependencies

- **GitPython** (3.1.43): Required for git repository analysis
- **ChromaDB** (0.4.22): Required for vector memory persistence
- **Python Standard Library**: collections.Counter for frequency tracking

Install dependencies:
```bash
pip install -r requirements.txt
```

## Testing

The agent includes comprehensive tests:

```bash
# Run git history tests
python ai-engine/tests/test_git_history_agent.py

# Run ChromaDB integration tests
python ai-engine/tests/test_chromadb_integration.py

# Run demo
python ai-engine/tests/demo_git_history.py
```

### Test Coverage

**Git History Tests:**
1. **Valid Git Repository**: Tests analysis with actual git repository
2. **Non-Git Directory**: Verifies fallback data for non-git directories
3. **Missing repo_path**: Tests error handling for empty paths
4. **Nonexistent Path**: Tests error handling for invalid paths

**ChromaDB Integration Tests:**
1. **Memory Report Generation**: Validates report format and content
2. **ChromaDB Client Initialization**: Tests connection to localhost:8000
3. **ChromaDB Persistence**: Tests full persistence workflow
4. **Defensive Error Handling**: Verifies graceful error handling

## Integration with LangGraph

This node is designed to be the second step in the LangGraph workflow:

```
Repository Agent → Git History Agent → [Next Agent]
```

The node receives:
- `repo_path`: From initial state
- `services`: From Repository Agent output

The node outputs:
- `high_churn_services`: For downstream fragility analysis
- `recent_commits`: For activity metrics
- `top_contributors`: For team insights

## Performance Considerations

- **Commit Limit**: Analyzes last 100 commits (configurable via `max_count`)
- **Service Mapping**: O(n) per file, where n = number of services
- **Memory**: Stores commit stats in Counter objects (efficient for frequency counting)

## API Reference

### Core Functions

#### `git_history_agent_node(state: AgentState) -> Dict[str, Any]`
Main node function that orchestrates git analysis and memory persistence.

#### `_generate_memory_report(...) -> str`
Generates comprehensive textual engineering memory report.

#### `_get_chromadb_client() -> Optional[chromadb.Client]`
Initializes ChromaDB client with connection to localhost:8000.

#### `_persist_to_chromadb(...) -> bool`
Persists memory report to ChromaDB with vector embeddings.

#### `_analyze_git_history(...) -> Dict[str, Any]`
Analyzes git repository history using GitPython.

#### `_map_file_to_service(file_path: str, services: List[str]) -> str`
Maps file paths to service names based on directory structure.

## Future Enhancements

Potential improvements:
1. Time-based filtering (e.g., last 90 days)
2. Configurable commit limit
3. File type filtering (e.g., exclude docs, tests)
4. Weighted churn scoring (lines changed vs. file count)
5. Contributor activity trends over time
6. Semantic search over memory reports
7. Multi-repository correlation analysis

## Made with Bob