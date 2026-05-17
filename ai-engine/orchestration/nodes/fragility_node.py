"""Fragility analysis node for the orchestration pipeline.

This node wraps the fragility_agent and calculates fragility scores.
"""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution

logger = logging.getLogger(__name__)


def fragility_node(state: IncidentState) -> IncidentState:
    """Calculate fragility scores for code components.
    
    This node invokes the fragility_agent to analyze code fragility
    based on dependencies, complexity, and other metrics.
    
    Args:
        state: Current pipeline state with dependency_graph
        
    Returns:
        Updated state with fragility_scores populated
    """
    node_name = "fragility_node"
    
    # Log start
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting fragility analysis"
    )
    logger.info(f"[{node_name}] Calculating fragility scores for {state['repo_id']}")
    
    try:
        # Validate prerequisites
        if not state.get("dependency_graph"):
            raise ValueError("dependency_graph is required but not found in state")
        
        # TODO: Import and invoke actual fragility_agent when available
        # from agents.fragility_agent import calculate_fragility
        # fragility_scores = calculate_fragility(
        #     state["parsed_repo"],
        #     state["dependency_graph"]
        # )
        
        # Mock implementation for now
        fragility_scores = {
            "components": [
                {
                    "path": "src/main.py",
                    "fragility_score": 0.75,
                    "risk_level": "high",
                    "factors": {
                        "complexity": 0.8,
                        "dependencies": 0.7,
                        "test_coverage": 0.6
                    }
                },
                {
                    "path": "src/utils.py",
                    "fragility_score": 0.35,
                    "risk_level": "low",
                    "factors": {
                        "complexity": 0.3,
                        "dependencies": 0.2,
                        "test_coverage": 0.8
                    }
                },
                {
                    "path": "tests/test_main.py",
                    "fragility_score": 0.25,
                    "risk_level": "low",
                    "factors": {
                        "complexity": 0.2,
                        "dependencies": 0.3,
                        "test_coverage": 1.0
                    }
                }
            ],
            "summary": {
                "average_fragility": 0.45,
                "high_risk_count": 1,
                "medium_risk_count": 0,
                "low_risk_count": 2
            }
        }
        
        # Update state
        state["fragility_scores"] = fragility_scores
        state["status"] = "fragility_analyzed"
        
        # Log completion
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Fragility analysis completed. Average score: {fragility_scores['summary']['average_fragility']:.2f}",
            data={
                "average_fragility": fragility_scores["summary"]["average_fragility"],
                "high_risk_count": fragility_scores["summary"]["high_risk_count"]
            }
        )
        logger.info(f"[{node_name}] Successfully calculated fragility scores")
        
    except Exception as e:
        error_msg = f"Fragility analysis failed: {str(e)}"
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
