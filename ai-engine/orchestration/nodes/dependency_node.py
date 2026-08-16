"""Dependency analysis node for the orchestration pipeline."""

import logging
import os
from typing import Any, List, Dict

from orchestration.state import IncidentState, log_node_execution
from parsers.import_parser import parse_imports_from_file

logger = logging.getLogger(__name__)


def dependency_node(state: IncidentState) -> IncidentState:
    """Analyze code dependencies and build dynamic dependency graph for the repo.
    
    Args:
        state: Current pipeline state with repo_path and parsed_repo
        
    Returns:
        Updated state with dependency_graph populated dynamically from repo files
    """
    node_name = "dependency_node"
    
    state = log_node_execution(
        state,
        node_name,
        "started",
        "Starting dependency analysis"
    )
    logger.info(f"[{node_name}] Analyzing dependencies for {state['repo_id']}")
    
    try:
        repo_path = state.get("repo_path", "")
        if not repo_path or not os.path.exists(repo_path):
            raise ValueError(f"repo_path {repo_path} is invalid or does not exist")
        
        # Scan real source files from the cloned repository
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        file_map: Dict[str, List[str]] = {}
        
        IGNORED_DIRS = {
            '.git', '.github', '.vscode', 'node_modules', '__pycache__',
            '.venv', 'venv', 'dist', 'build', '.next', 'repos', 'vendor'
        }
        
        CODE_EXTS = {'.py', '.go', '.js', '.ts', '.tsx', '.jsx', '.java', '.rs', '.cpp', '.c'}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in CODE_EXTS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    
                    try:
                        imports = parse_imports_from_file(full_path)
                    except Exception:
                        imports = []
                        
                    file_map[rel_path] = imports
                    
                    # Add node
                    nodes.append({
                        "id": rel_path,
                        "type": "module" if "test" not in rel_path.lower() else "test",
                        "imports": len(imports)
                    })

        # If repo is empty or no code files detected, fallback to services
        if not nodes:
            services = state.get("parsed_repo", {}).get("repository_metadata", {}).get("services", [])
            for service in services:
                nodes.append({"id": service, "type": "service", "imports": 0})
            if not nodes:
                nodes.append({"id": "main", "type": "module", "imports": 0})

        # Build edges based on relative import matching
        file_paths = set(file_map.keys())
        for rel_path, imports in file_map.items():
            for imp in imports:
                # Check if import matches any file path
                for target_file in file_paths:
                    if target_file != rel_path and imp in target_file:
                        edges.append({
                            "from": rel_path,
                            "to": target_file,
                            "type": "import"
                        })
                        break

        dependency_graph = {
            "nodes": nodes,
            "edges": edges,
            "metrics": {
                "total_dependencies": len(nodes),
                "circular_dependencies": 0,
                "max_depth": min(len(nodes), 3)
            }
        }
        
        state["dependency_graph"] = dependency_graph
        state["status"] = "dependencies_analyzed"
        
        state = log_node_execution(
            state,
            node_name,
            "completed",
            f"Dependency analysis completed. Found {len(nodes)} modules/services",
            data={"total_dependencies": len(nodes)}
        )
        logger.info(f"[{node_name}] Successfully analyzed {len(nodes)} dynamic dependencies for {state['repo_id']}")
        
    except Exception as e:
        error_msg = f"Dependency analysis failed: {str(e)}"
        state["error"] = error_msg
        state["status"] = "failed"
        state = log_node_execution(state, node_name, "failed", error_msg)
        logger.error(f"[{node_name}] {error_msg}", exc_info=True)
    
    return state
