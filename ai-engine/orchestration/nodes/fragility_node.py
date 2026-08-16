"""Fragility analysis node for the orchestration pipeline."""

import logging
import os
from typing import Any, List, Dict

from orchestration.state import IncidentState, log_node_execution

logger = logging.getLogger(__name__)


def fragility_node(state: IncidentState) -> IncidentState:
    """Calculate fragility scores dynamically for real components in the repository.
    
    Args:
        state: Current pipeline state with dependency_graph and repo_path
        
    Returns:
        Updated state with fragility_scores populated for actual repo files
    """
    node_name = "fragility_node"
    
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting fragility analysis"
    )
    logger.info(f"[{node_name}] Calculating fragility scores for {state['repo_id']}")
    
    try:
        dep_graph = state.get("dependency_graph", {})
        nodes = dep_graph.get("nodes", [])
        repo_path = state.get("repo_path", "")
        
        components: List[Dict[str, Any]] = []
        high_risk = 0
        med_risk = 0
        low_risk = 0
        total_score = 0.0
        
        for idx, node in enumerate(nodes):
            file_path = node.get("id", f"component_{idx}")
            import_count = node.get("imports", 0)
            
            # Read line count if file exists
            line_count = 50
            full_file_path = os.path.join(repo_path, file_path) if repo_path else ""
            if full_file_path and os.path.exists(full_file_path):
                try:
                    with open(full_file_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = len(f.readlines())
                except Exception:
                    pass

            # Dynamic fragility score formula based on lines & imports
            complexity_factor = min(line_count / 300.0, 1.0)
            dep_factor = min(import_count / 10.0, 1.0)
            score = round(0.4 * complexity_factor + 0.6 * dep_factor + 0.1, 2)
            score = min(max(score, 0.15), 0.95)
            
            if score >= 0.65:
                risk_level = "high"
                high_risk += 1
            elif score >= 0.4:
                risk_level = "medium"
                med_risk += 1
            else:
                risk_level = "low"
                low_risk += 1
                
            total_score += score
            
            components.append({
                "path": file_path,
                "fragility_score": score,
                "risk_level": risk_level,
                "factors": {
                    "complexity": round(complexity_factor, 2),
                    "dependencies": round(dep_factor, 2),
                    "test_coverage": round(0.8 if "test" in file_path.lower() else 0.4, 2)
                }
            })
            
        avg_fragility = round(total_score / max(len(components), 1), 2)
        
        fragility_scores = {
            "components": components,
            "summary": {
                "average_fragility": avg_fragility,
                "high_risk_count": high_risk,
                "medium_risk_count": med_risk,
                "low_risk_count": low_risk
            }
        }
        
        state["fragility_scores"] = fragility_scores
        state["status"] = "fragility_analyzed"
        
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Fragility analysis completed. Average score: {avg_fragility:.2f}",
            data={
                "average_fragility": avg_fragility,
                "high_risk_count": high_risk
            }
        )
        logger.info(f"[{node_name}] Successfully calculated fragility scores for {len(components)} real components")
        
    except Exception as e:
        error_msg = f"Fragility analysis failed: {str(e)}"
        state["error"] = error_msg
        state["status"] = "failed"
        state = log_node_execution(state, node_name, "failed", error_msg)
        logger.error(f"[{node_name}] {error_msg}", exc_info=True)
    
    return state
