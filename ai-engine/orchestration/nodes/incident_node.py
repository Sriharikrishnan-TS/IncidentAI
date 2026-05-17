"""Incident detection node for the orchestration pipeline.

This node wraps the incident_agent and detects potential incidents.
"""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution

logger = logging.getLogger(__name__)


def incident_node(state: IncidentState) -> IncidentState:
    """Detect and classify potential incidents in the codebase.
    
    This node invokes the incident_agent to identify potential issues,
    bugs, and incidents based on fragility scores and code analysis.
    
    Args:
        state: Current pipeline state with fragility_scores
        
    Returns:
        Updated state with incidents populated
    """
    node_name = "incident_node"
    
    # Log start
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting incident detection"
    )
    logger.info(f"[{node_name}] Detecting incidents for {state['repo_id']}")
    
    try:
        # Validate prerequisites
        if not state.get("fragility_scores"):
            raise ValueError("fragility_scores is required but not found in state")
        
        # TODO: Import and invoke actual incident_agent when available
        # from agents.incident_agent import detect_incidents
        # incidents = detect_incidents(
        #     state["parsed_repo"],
        #     state["dependency_graph"],
        #     state["fragility_scores"]
        # )
        
        # Mock implementation for now
        incidents = [
            {
                "id": "INC-001",
                "type": "high_fragility",
                "severity": "high",
                "component": "src/main.py",
                "title": "High fragility score detected",
                "description": "Component has high fragility score (0.75) indicating potential stability issues",
                "recommendations": [
                    "Add more unit tests to improve coverage",
                    "Reduce cyclomatic complexity",
                    "Consider refactoring into smaller modules"
                ],
                "metrics": {
                    "fragility_score": 0.75,
                    "complexity": 0.8,
                    "test_coverage": 0.6
                }
            },
            {
                "id": "INC-002",
                "type": "dependency_risk",
                "severity": "medium",
                "component": "src/main.py",
                "title": "High dependency coupling",
                "description": "Component has multiple dependencies that could impact stability",
                "recommendations": [
                    "Review dependency structure",
                    "Consider dependency injection patterns",
                    "Add integration tests"
                ],
                "metrics": {
                    "dependency_count": 2,
                    "coupling_score": 0.7
                }
            }
        ]
        
        # Update state
        state["incidents"] = incidents
        state["status"] = "incidents_detected"
        
        # Log completion
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Incident detection completed. Found {len(incidents)} incidents",
            data={
                "total_incidents": len(incidents),
                "high_severity": sum(1 for i in incidents if i["severity"] == "high"),
                "medium_severity": sum(1 for i in incidents if i["severity"] == "medium"),
                "low_severity": sum(1 for i in incidents if i["severity"] == "low")
            }
        )
        logger.info(f"[{node_name}] Successfully detected {len(incidents)} incidents")
        
    except Exception as e:
        error_msg = f"Incident detection failed: {str(e)}"
        state["error"] = error_msg
        state["status"] = "failed"
        
        state = log_node_execution(
            state,
            node_name,
            "failed",
            error_msg
        )
        logger.error(f"[{node_name}] {error_msg}", exc_info=True)
    
    return state

# Made with Bob
