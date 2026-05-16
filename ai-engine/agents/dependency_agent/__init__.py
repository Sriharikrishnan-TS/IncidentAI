"""
Dependency Agent for IncidentOS AI Engine.

This agent processes microservice repository relationship data, generates
Neo4j graph data, and runs architectural risk analysis.
"""

from .dependency_graph_manager import (
    DependencyGraphManager,
    process_dependencies,
    ServicesInput,
    ServiceInput,
    DependencyAgentOutput,
    ExtractedDependency,
    RiskAnalysis,
    RiskNode,
)

__all__ = [
    "DependencyGraphManager",
    "process_dependencies",
    "ServicesInput",
    "ServiceInput",
    "DependencyAgentOutput",
    "ExtractedDependency",
    "RiskAnalysis",
    "RiskNode",
]

# Made with Bob
