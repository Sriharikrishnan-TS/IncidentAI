"""
LangGraph State Definition for IncidentOS
Defines the shared state structure used across all agent nodes in the workflow.
"""
from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """
    Shared state structure for the LangGraph workflow.
    
    This state is passed between all agent nodes and accumulates
    information as the workflow progresses through the graph.
    
    All fields are optional (total=False) to allow incremental state building.
    
    Core Identifiers:
        repo_id: Unique identifier for the repository being analyzed
        repo_path: Absolute or relative path to the repository on disk
    
    Repository Metadata:
        repository_metadata: Comprehensive repository metadata summary
        services: List of detected services/microservices in the repository
        languages: List of programming languages detected in the repository
        frameworks: List of frameworks detected in the repository
        architecture_summary: Natural-language description of the repository architecture
    
    Dependency Analysis:
        dependency_graph: List of dependency relationships in backend-compatible schema
    
    Git History Analysis:
        high_churn_services: List of services with high code churn
        recent_commits: Number of recent commits analyzed
        top_contributors: List of top contributors to the repository
        pr_analytics: PR and branch churn analytics data
    
    Fragility Analysis:
        fragility_scores: List of fragility scores for services
    
    Incident Analysis:
        incidents: List of identified incidents and their analysis
    
    Mentor Context:
        mentor_context: Context and knowledge for mentor agent
    
    Retrieval Context:
        retrieved_context: Context retrieved from ChromaDB/Neo4j via backend APIs
    
    Logging and Status:
        logs: List of structured log entries from all nodes
        status: Current workflow status
    """
    # Core identifiers
    repo_id: str
    repo_path: str
    
    # Repository metadata
    repository_metadata: str
    services: List[str]
    languages: List[str]
    frameworks: List[str]
    architecture_summary: str
    
    # Dependency analysis
    dependency_graph: List[Dict[str, Any]]
    
    # Git history analysis
    high_churn_services: List[str]
    recent_commits: int
    top_contributors: List[str]
    pr_analytics: Dict[str, Any]
    
    # Fragility analysis
    fragility_scores: List[Dict[str, Any]]
    
    # Incident analysis
    incidents: List[Dict[str, Any]]
    
    # Mentor context
    mentor_context: Dict[str, Any]
    
    # Retrieval context
    retrieved_context: Dict[str, Any]
    
    # Logging and status
    logs: List[Dict[str, Any]]
    status: str

# Made with Bob
