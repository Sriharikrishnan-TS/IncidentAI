"""
Fragility Agent Module

This agent analyzes microservice fragility by combining structural graph metrics
from Neo4j with operational metrics (code churn and incident frequency).

Key Components:
- FragilityAgent: Main agent class for fragility analysis
- OperationalMetrics: Input validation model
- FragilityOutput: Output model with scores and reasons
- analyze_fragility: Convenience function for quick analysis
"""

from .fragility_agent import (
    FragilityAgent,
    OperationalMetrics,
    FragilityScore,
    FragilityOutput,
    analyze_fragility,
)

__all__ = [
    "FragilityAgent",
    "OperationalMetrics",
    "FragilityScore",
    "FragilityOutput",
    "analyze_fragility",
]

__version__ = "1.0.0"
__author__ = "IncidentOS AI Engine"
__description__ = "Microservice fragility analysis agent"

# Made with Bob
