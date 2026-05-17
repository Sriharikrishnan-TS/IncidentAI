"""Orchestration nodes for the IncidentOS pipeline.

Each node wraps an agent and handles state management.
"""

from .repository_node import repository_node
from .dependency_node import dependency_node
from .fragility_node import fragility_node
from .incident_node import incident_node
from .mentor_node import mentor_node

# Export with _agent_node suffix for compatibility with extended_orchestrator
dependency_agent_node = dependency_node
fragility_agent_node = fragility_node
incident_agent_node = incident_node
mentor_agent_node = mentor_node

__all__ = [
    "repository_node",
    "dependency_node",
    "fragility_node",
    "incident_node",
    "mentor_node",
    "dependency_agent_node",
    "fragility_agent_node",
    "incident_agent_node",
    "mentor_agent_node",
]

# Made with Bob
