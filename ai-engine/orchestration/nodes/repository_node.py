"""Repository analysis node for the orchestration pipeline.

This node wraps the repository_agent and handles repository parsing.
"""

import logging
from typing import Any

from orchestration.state import IncidentState, log_node_execution

logger = logging.getLogger(__name__)


def repository_node(state: IncidentState) -> IncidentState:
    """Parse and analyze repository structure.
    
    This node invokes the repository_agent to parse the repository
    and extract its structure, files, and metadata.
    
    Args:
        state: Current pipeline state containing repo_id and repo_path
        
    Returns:
        Updated state with parsed_repo populated
    """
    node_name = "repository_node"
    
    # Log start
    state = log_node_execution(
        state,
        node_name,
        "started",
        f"Starting repository analysis for {state['repo_id']}"
    )
    logger.info(f"[{node_name}] Processing repository: {state['repo_path']}")
    
    try:
        # TODO: Import and invoke actual repository_agent when available
        # from agents.repository_agent import analyze_repository
        # parsed_repo = analyze_repository(state["repo_path"])
        
        # Mock implementation for now
        parsed_repo = {
            "repo_id": state["repo_id"],
            "repo_path": state["repo_path"],
            "files": [
                {"path": "src/main.py", "type": "python", "lines": 150},
                {"path": "src/utils.py", "type": "python", "lines": 80},
                {"path": "tests/test_main.py", "type": "python", "lines": 50},
            ],
            "structure": {
                "src": ["main.py", "utils.py"],
                "tests": ["test_main.py"]
            },
            "metadata": {
                "total_files": 3,
                "total_lines": 280,
                "languages": ["python"]
            }
        }
        
        # Update state
        state["parsed_repo"] = parsed_repo
        state["status"] = "repository_analyzed"
        
        # Log completion
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Repository analysis completed. Found {parsed_repo['metadata']['total_files']} files",
            data={"total_files": parsed_repo["metadata"]["total_files"]}
        )
        logger.info(f"[{node_name}] Successfully analyzed repository")
        
    except Exception as e:
        error_msg = f"Repository analysis failed: {str(e)}"
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
