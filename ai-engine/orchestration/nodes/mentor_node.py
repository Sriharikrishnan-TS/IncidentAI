"""Mentor guidance node for the orchestration pipeline."""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution
from agents.mentor_agent.node import generate_mentorship

logger = logging.getLogger(__name__)


def mentor_node(state: IncidentState) -> IncidentState:
    """Generate mentorship guidance using ChatGroq Llama-3.3-70b AI reasoning."""
    node_name = "mentor_node"
    
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting mentor guidance generation"
    )
    logger.info(f"[{node_name}] Generating mentorship for {state['repo_id']}")
    
    try:
        # Validate prerequisites
        if not state.get("incidents"):
            raise ValueError("incidents is required but not found in state")
        
        # Invoke Groq Llama-3.3-70b powered mentor_agent
        mentor_context = generate_mentorship(
            repo_id=state["repo_id"],
            parsed_repo=state.get("parsed_repo"),
            incidents=state.get("incidents"),
            fragility_scores=state.get("fragility_scores")
        )
        
        # Update state
        state["mentor_context"] = mentor_context
        state["status"] = "completed"
        
        # Log completion
        recs = mentor_context.get("recommendations", [])
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Mentor guidance generated. {len(recs)} recommendations provided",
            data={
                "total_recommendations": len(recs),
                "high_priority": sum(1 for r in recs if r.get("priority") == "high")
            }
        )
        logger.info(f"[{node_name}] Successfully generated mentorship guidance")
        
    except Exception as e:
        error_msg = f"Mentor guidance generation failed: {str(e)}"
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
