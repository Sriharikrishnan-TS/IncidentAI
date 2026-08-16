"""Incident detection node for the orchestration pipeline."""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution
from agents.incident_agent.node import detect_incidents

logger = logging.getLogger(__name__)


def incident_node(state: IncidentState) -> IncidentState:
    """Detect and classify potential incidents using ChatGroq Llama-3.3-70b AI reasoning."""
    node_name = "incident_node"
    
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
        
        # Invoke Groq Llama-3.3-70b powered incident_agent
        incidents = detect_incidents(
            repo_id=state["repo_id"],
            parsed_repo=state.get("parsed_repo"),
            dependency_graph=state.get("dependency_graph"),
            fragility_scores=state.get("fragility_scores"),
            git_history=state.get("git_history")
        )
        
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
                "high_severity": sum(1 for i in incidents if i.get("severity") == "high"),
                "medium_severity": sum(1 for i in incidents if i.get("severity") == "medium"),
                "low_severity": sum(1 for i in incidents if i.get("severity") == "low")
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
