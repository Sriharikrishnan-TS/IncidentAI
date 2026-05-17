"""Shared state definition for IncidentOS orchestration pipeline.

This module defines the IncidentState TypedDict that flows through
the LangGraph orchestration pipeline, carrying data between agent nodes.
"""

from typing import TypedDict, Any, Optional
from datetime import datetime


class IncidentState(TypedDict):
    """Shared state that flows through the orchestration pipeline.
    
    This state is passed between all agent nodes and accumulates
    information as the analysis progresses.
    
    Attributes:
        repo_id: Unique identifier for the repository
        repo_path: Local filesystem path to the cloned repository
        parsed_repo: Structured representation of repository contents
        repository_metadata: Repository metadata (services, languages, frameworks)
        recent_commits: Number of recent commits analyzed
        top_contributors: List of top contributors
        high_churn_services: List of high-churn services
        dependency_graph: Graph of code dependencies and relationships
        fragility_scores: Fragility analysis results for code components
        incidents: List of detected incidents/issues
        mentor_context: Mentorship recommendations and guidance
        logs: Execution logs from each node
        status: Current pipeline execution status
        error: Error message if pipeline fails
        timestamp: Timestamp of pipeline execution start
    """
    
    # Input fields (required)
    repo_id: str
    repo_path: str
    logs: list[dict[str, Any]]
    status: str
    timestamp: str
    
    # Agent outputs (optional)
    parsed_repo: Optional[dict[str, Any]]
    repository_metadata: Optional[dict[str, Any]]
    recent_commits: Optional[int]
    top_contributors: Optional[list[str]]
    high_churn_services: Optional[list[str]]
    dependency_graph: Optional[dict[str, Any]]
    fragility_scores: Optional[dict[str, Any]]
    incidents: Optional[list[dict[str, Any]]]
    mentor_context: Optional[dict[str, Any]]
    error: Optional[str]


def create_initial_state(repo_id: str, repo_path: str) -> IncidentState:
    """Create initial state for orchestration pipeline.
    
    Args:
        repo_id: Unique identifier for the repository
        repo_path: Local filesystem path to the repository
        
    Returns:
        Initial IncidentState with required fields populated
    """
    return IncidentState(
        repo_id=repo_id,
        repo_path=repo_path,
        parsed_repo=None,
        repository_metadata=None,
        recent_commits=None,
        top_contributors=None,
        high_churn_services=None,
        dependency_graph=None,
        fragility_scores=None,
        incidents=None,
        mentor_context=None,
        logs=[],
        status="initialized",
        error=None,
        timestamp=datetime.utcnow().isoformat()
    )


def log_node_execution(
    state: IncidentState,
    node_name: str,
    status: str,
    message: str,
    data: Optional[dict[str, Any]] = None
) -> IncidentState:
    """Add a log entry to the state.
    
    Args:
        state: Current state
        node_name: Name of the node logging the entry
        status: Status of the operation (started, completed, failed)
        message: Log message
        data: Optional additional data to log
        
    Returns:
        Updated state with new log entry
    """
    log_entry: dict[str, Any] = {
        "node": node_name,
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data:
        log_entry["data"] = data
    
    state["logs"].append(log_entry)
    return state

# Made with Bob
