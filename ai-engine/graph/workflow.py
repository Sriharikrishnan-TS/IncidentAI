"""LangGraph workflow for IncidentOS orchestration pipeline.

This module defines the deterministic execution flow using LangGraph,
connecting all agent nodes in a sequential pipeline.
"""

import logging
from typing import Any

from langgraph.graph import StateGraph, END
from orchestration.state import IncidentState
from orchestration.nodes import (
    repository_node,
    dependency_node,
    fragility_node,
    incident_node,
    mentor_node,
)

logger = logging.getLogger(__name__)


def create_workflow() -> Any:
    """Create the LangGraph workflow for repository analysis.
    
    The workflow follows a deterministic pipeline:
    START → repository → dependency → fragility → incident → mentor → END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with IncidentState
    workflow = StateGraph(IncidentState)
    
    # Add nodes to the graph
    workflow.add_node("repository", repository_node)
    workflow.add_node("dependency", dependency_node)
    workflow.add_node("fragility", fragility_node)
    workflow.add_node("incident", incident_node)
    workflow.add_node("mentor", mentor_node)
    
    # Define the deterministic flow
    # START → repository_node
    workflow.set_entry_point("repository")
    
    # repository_node → dependency_node
    workflow.add_edge("repository", "dependency")
    
    # dependency_node → fragility_node
    workflow.add_edge("dependency", "fragility")
    
    # fragility_node → incident_node
    workflow.add_edge("fragility", "incident")
    
    # incident_node → mentor_node
    workflow.add_edge("incident", "mentor")
    
    # mentor_node → END
    workflow.add_edge("mentor", END)
    
    # Compile the graph
    compiled_workflow = workflow.compile()
    
    logger.info("LangGraph workflow created successfully")
    return compiled_workflow


def execute_workflow(repo_id: str, repo_path: str) -> dict[str, Any]:
    """Execute the complete orchestration workflow.
    
    Args:
        repo_id: Unique identifier for the repository
        repo_path: Local filesystem path to the repository
        
    Returns:
        Final state after workflow execution
        
    Raises:
        Exception: If workflow execution fails
    """
    from orchestration.state import create_initial_state
    
    logger.info(f"Starting workflow execution for repo_id={repo_id}")
    
    # Create initial state
    initial_state = create_initial_state(repo_id, repo_path)
    
    # Create and execute workflow
    workflow = create_workflow()
    
    try:
        # Execute the workflow
        final_state = workflow.invoke(initial_state)
        
        logger.info(f"Workflow execution completed with status: {final_state.get('status')}")
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise


async def execute_workflow_async(repo_id: str, repo_path: str) -> dict[str, Any]:
    """Execute the workflow asynchronously (for future use).
    
    Args:
        repo_id: Unique identifier for the repository
        repo_path: Local filesystem path to the repository
        
    Returns:
        Final state after workflow execution
        
    Raises:
        Exception: If workflow execution fails
    """
    from orchestration.state import create_initial_state
    
    logger.info(f"Starting async workflow execution for repo_id={repo_id}")
    
    # Create initial state
    initial_state = create_initial_state(repo_id, repo_path)
    
    # Create workflow
    workflow = create_workflow()
    
    try:
        # Execute the workflow asynchronously
        final_state = await workflow.ainvoke(initial_state)
        
        logger.info(f"Async workflow execution completed with status: {final_state.get('status')}")
        return final_state
        
    except Exception as e:
        logger.error(f"Async workflow execution failed: {str(e)}", exc_info=True)
        raise


def get_workflow_visualization() -> str:
    """Get a visual representation of the workflow graph.
    
    Returns:
        String representation of the workflow structure
    """
    workflow = create_workflow()
    
    # Get the graph structure
    graph_structure = """
    IncidentOS Orchestration Pipeline
    ==================================
    
    START
      ↓
    [Repository Node]
      ↓ (parsed_repo)
    [Dependency Node]
      ↓ (dependency_graph)
    [Fragility Node]
      ↓ (fragility_scores)
    [Incident Node]
      ↓ (incidents)
    [Mentor Node]
      ↓ (mentor_context)
    END
    
    State Flow:
    - repo_id, repo_path → parsed_repo → dependency_graph → 
      fragility_scores → incidents → mentor_context
    """
    
    return graph_structure


if __name__ == "__main__":
    # Example usage for testing
    logging.basicConfig(level=logging.INFO)
    
    print(get_workflow_visualization())
    
    # Test workflow creation
    workflow = create_workflow()
    print("\n✓ Workflow created successfully")

# Made with Bob
