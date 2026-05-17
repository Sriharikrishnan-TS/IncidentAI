"""Dependency analysis node for the orchestration pipeline.

This node wraps the dependency_agent and analyzes code dependencies.
"""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution

logger = logging.getLogger(__name__)


def dependency_node(state: IncidentState) -> IncidentState:
    """Analyze code dependencies and build dependency graph.
    
    This node invokes the dependency_agent to analyze dependencies
    between code components and build a dependency graph.
    
    Args:
        state: Current pipeline state with parsed_repo
        
    Returns:
        Updated state with dependency_graph populated
    """
    node_name = "dependency_node"
    
    # Log start
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting dependency analysis"
    )
    logger.info(f"[{node_name}] Analyzing dependencies for {state['repo_id']}")
    
    try:
        # Validate prerequisites
        if not state.get("parsed_repo"):
            raise ValueError("parsed_repo is required but not found in state")
        
        # TODO: Import and invoke actual dependency_agent when available
        # from agents.dependency_agent import analyze_dependencies
        # dependency_graph = analyze_dependencies(state["parsed_repo"])
        
        # Mock implementation for now
        dependency_graph = {
            "nodes": [
                {"id": "src/main.py", "type": "module", "imports": 2},
                {"id": "src/utils.py", "type": "module", "imports": 0},
                {"id": "tests/test_main.py", "type": "test", "imports": 2}
            ],
            "edges": [
                {"from": "src/main.py", "to": "src/utils.py", "type": "import"},
                {"from": "tests/test_main.py", "to": "src/main.py", "type": "import"},
                {"from": "tests/test_main.py", "to": "src/utils.py", "type": "import"}
            ],
            "metrics": {
                "total_dependencies": 3,
                "circular_dependencies": 0,
                "max_depth": 2
            }
        }
        
        # Update state
        state["dependency_graph"] = dependency_graph
        state["status"] = "dependencies_analyzed"
        
        # Log completion
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Dependency analysis completed. Found {dependency_graph['metrics']['total_dependencies']} dependencies",
            data={"total_dependencies": dependency_graph["metrics"]["total_dependencies"]}
        )
        logger.info(f"[{node_name}] Successfully analyzed dependencies")
        
    except Exception as e:
        error_msg = f"Dependency analysis failed: {str(e)}"
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
