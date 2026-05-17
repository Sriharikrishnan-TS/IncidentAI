"""
Shared state constants and schema definitions for IncidentOS orchestration.

This module defines:
- Standardized state keys used across all orchestration nodes
- Dependency type constants
- Schema validation helpers
"""

from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional


# ============================================================================
# STATE KEY CONSTANTS
# ============================================================================

class StateKeys:
    """Standardized keys for LangGraph shared state."""
    
    # Core identifiers
    REPO_ID = "repo_id"
    REPO_PATH = "repo_path"
    
    # Parsed repository (structured representation)
    PARSED_REPO = "parsed_repo"
    
    # Repository metadata
    REPOSITORY_METADATA = "repository_metadata"
    SERVICES = "services"
    LANGUAGES = "languages"
    FRAMEWORKS = "frameworks"
    ARCHITECTURE_SUMMARY = "architecture_summary"
    
    # Dependency analysis
    DEPENDENCY_GRAPH = "dependency_graph"
    
    # Git history analysis
    HIGH_CHURN_SERVICES = "high_churn_services"
    RECENT_COMMITS = "recent_commits"
    TOP_CONTRIBUTORS = "top_contributors"
    PR_ANALYTICS = "pr_analytics"
    
    # Fragility analysis
    FRAGILITY_SCORES = "fragility_scores"
    
    # Incident analysis
    INCIDENTS = "incidents"
    
    # Mentor context
    MENTOR_CONTEXT = "mentor_context"
    
    # Retrieval context
    RETRIEVED_CONTEXT = "retrieved_context"
    
    # Logging and status
    LOGS = "logs"
    STATUS = "status"


# ============================================================================
# DEPENDENCY TYPE CONSTANTS
# ============================================================================

class DependencyType(str, Enum):
    """Allowed dependency relationship types for Neo4j graph."""
    
    DEPENDS_ON = "DEPENDS_ON"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    USES = "USES"
    COMMUNICATES_WITH = "COMMUNICATES_WITH"
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    PUBLISHES_TO = "PUBLISHES_TO"
    SUBSCRIBES_TO = "SUBSCRIBES_TO"


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

class DependencySchema(TypedDict):
    """Backend-compatible dependency schema."""
    source: str
    target: str
    type: str  # Should be one of DependencyType values


class FragilityScore(TypedDict):
    """Fragility score schema."""
    service: str
    score: float
    reasons: List[str]


class Incident(TypedDict):
    """Incident schema."""
    id: str
    title: str
    description: str
    severity: str
    affected_services: List[str]
    root_cause: Optional[str]


class LogEntry(TypedDict):
    """Log entry schema."""
    timestamp: str
    level: str
    node: str
    message: str
    repo_id: Optional[str]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def convert_mock_to_backend_schema(mock_dependency: Dict[str, Any]) -> DependencySchema:
    """
    Convert mock dependency format to backend-compatible schema.
    
    Mock format:
        {"from": "service-a", "to": "service-b", "type": "import"}
    
    Backend format:
        {"source": "service-a", "target": "service-b", "type": "DEPENDS_ON"}
    
    Args:
        mock_dependency: Dependency in mock format
        
    Returns:
        Dependency in backend-compatible format
    """
    # Map mock types to backend types
    type_mapping = {
        "import": DependencyType.IMPORTS,
        "call": DependencyType.CALLS,
        "use": DependencyType.USES,
        "depends_on": DependencyType.DEPENDS_ON,
        "communicates_with": DependencyType.COMMUNICATES_WITH,
        "reads_from": DependencyType.READS_FROM,
        "writes_to": DependencyType.WRITES_TO,
        "publishes_to": DependencyType.PUBLISHES_TO,
        "subscribes_to": DependencyType.SUBSCRIBES_TO,
    }
    
    mock_type = mock_dependency.get("type", "import").lower()
    backend_type = type_mapping.get(mock_type, DependencyType.DEPENDS_ON)
    
    return DependencySchema(
        source=mock_dependency.get("from", mock_dependency.get("source", "")),
        target=mock_dependency.get("to", mock_dependency.get("target", "")),
        type=backend_type.value
    )


def validate_dependency_type(dep_type: str) -> bool:
    """
    Validate if a dependency type is allowed.
    
    Args:
        dep_type: Dependency type string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        DependencyType(dep_type)
        return True
    except ValueError:
        return False


def get_allowed_dependency_types() -> List[str]:
    """
    Get list of all allowed dependency types.
    
    Returns:
        List of allowed dependency type strings
    """
    return [dt.value for dt in DependencyType]


def create_log_entry(
    level: str,
    node: str,
    message: str,
    repo_id: Optional[str] = None
) -> LogEntry:
    """
    Create a standardized log entry.
    
    Args:
        level: Log level (INFO, WARNING, ERROR)
        node: Node name that generated the log
        message: Log message
        repo_id: Optional repository ID
        
    Returns:
        Standardized log entry
    """
    from datetime import datetime
    
    return LogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        level=level.upper(),
        node=node,
        message=message,
        repo_id=repo_id
    )

# Made with Bob
