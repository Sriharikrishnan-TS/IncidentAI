"""
LangGraph State Definition for IncidentOS
Defines the shared state structure used across all agent nodes in the workflow.
"""
from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    """
    Shared state structure for the LangGraph workflow.
    
    This state is passed between all agent nodes and accumulates
    information as the workflow progresses through the graph.
    
    Attributes:
        repo_id: Unique identifier for the repository being analyzed
        repo_path: Absolute or relative path to the repository on disk
        services: List of detected services/microservices in the repository
        languages: List of programming languages detected in the repository
        frameworks: List of frameworks detected in the repository
        architecture_summary: Natural-language description of the repository architecture
        high_churn_services: List of services with high code churn (Workflow 6)
        recent_commits: Number of recent commits analyzed (Workflow 6)
        top_contributors: List of top contributors to the repository (Workflow 6)
        pr_analytics: PR and branch churn analytics data for fragility scoring
    """
    repo_id: str
    repo_path: str
    services: List[str]
    languages: List[str]
    frameworks: List[str]
    architecture_summary: str
    high_churn_services: List[str]
    recent_commits: int
    top_contributors: List[str]
    pr_analytics: Dict[str, Any]

# Made with Bob
