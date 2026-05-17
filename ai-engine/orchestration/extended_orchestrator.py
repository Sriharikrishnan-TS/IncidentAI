"""
Extended LangGraph Orchestrator with Backend Callback Integration.

This orchestrator extends the existing live_orchestrator.py with:
- Backend callback integration
- Additional analysis nodes (dependency, fragility, incident, mentor)
- Standardized shared state flow
- Comprehensive logging
- Graceful error handling

Architecture:
Frontend → Backend → LangGraph Orchestrator → Agents → Backend Callbacks → Persistence
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.state import AgentState
from orchestration.shared_state import StateKeys
from orchestration.logging_config import configure_logging
from orchestration.live_orchestrator import (
    repository_agent_node,
    git_history_agent_node
)
from orchestration.nodes import (
    dependency_agent_node,
    fragility_agent_node,
    incident_agent_node,
    mentor_agent_node
)

# Configure logging
configure_logging(level="INFO", use_colors=True)
logger = logging.getLogger(__name__)


# ============================================================================
# EXTENDED ORCHESTRATOR
# ============================================================================

def create_extended_orchestrator():
    """
    Create extended LangGraph orchestrator with all analysis nodes.
    
    Pipeline:
    START → repository_agent → git_history_agent → dependency_agent →
    fragility_agent → incident_agent → mentor_agent → END
    
    Each node:
    - Performs analysis
    - Updates shared state
    - Sends backend callback
    - Logs operations
    - Handles errors gracefully
    
    Returns:
        Compiled LangGraph ready for execution
    """
    try:
        from langgraph.graph import StateGraph, START, END
        
        logger.info("[ORCHESTRATOR] Initializing extended LangGraph...")
        
        # Initialize graph with AgentState
        workflow = StateGraph(AgentState)
        
        # Add all nodes
        workflow.add_node("repository_agent", repository_agent_node)
        workflow.add_node("git_history_agent", git_history_agent_node)
        workflow.add_node("dependency_agent", dependency_agent_node)  # type: ignore
        workflow.add_node("fragility_agent", fragility_agent_node)  # type: ignore
        workflow.add_node("incident_agent", incident_agent_node)  # type: ignore
        workflow.add_node("mentor_agent", mentor_agent_node)  # type: ignore
        
        # Wire the complete pipeline
        workflow.add_edge(START, "repository_agent")
        workflow.add_edge("repository_agent", "git_history_agent")
        workflow.add_edge("git_history_agent", "dependency_agent")
        workflow.add_edge("dependency_agent", "fragility_agent")
        workflow.add_edge("fragility_agent", "incident_agent")
        workflow.add_edge("incident_agent", "mentor_agent")
        workflow.add_edge("mentor_agent", END)
        
        # Compile the graph
        app = workflow.compile()
        
        logger.info("[ORCHESTRATOR] Extended LangGraph compiled successfully")
        logger.info("[ORCHESTRATOR] Pipeline: repository → git_history → dependency → fragility → incident → mentor")
        
        return app
        
    except ImportError as e:
        logger.error(f"LangGraph not available: {e}")
        logger.error("Install with: pip install langgraph")
        raise
    except Exception as e:
        logger.error(f"Failed to create orchestrator: {e}", exc_info=True)
        raise


def execute_extended_orchestrator(
    repo_path: str,
    repo_id: str = "test-repo"
) -> Dict[str, Any]:
    """
    Execute the extended orchestrator on a repository.
    
    Args:
        repo_path: Path to repository to analyze
        repo_id: Unique identifier for the repository
        
    Returns:
        Final state dictionary with all analysis results
    """
    logger.info(f"[EXECUTION] Starting extended orchestrator for {repo_id}")
    logger.info(f"[EXECUTION] Repository path: {repo_path}")
    
    # Create orchestrator
    app = create_extended_orchestrator()
    
    # Initialize state with all required fields
    initial_state: AgentState = {
        StateKeys.REPO_ID: repo_id,
        StateKeys.REPO_PATH: repo_path,
        StateKeys.SERVICES: [],
        StateKeys.LANGUAGES: [],
        StateKeys.FRAMEWORKS: [],
        StateKeys.ARCHITECTURE_SUMMARY: "",
        StateKeys.REPOSITORY_METADATA: "",
        StateKeys.DEPENDENCY_GRAPH: [],
        StateKeys.HIGH_CHURN_SERVICES: [],
        StateKeys.RECENT_COMMITS: 0,
        StateKeys.TOP_CONTRIBUTORS: [],
        StateKeys.PR_ANALYTICS: {},
        StateKeys.FRAGILITY_SCORES: [],
        StateKeys.INCIDENTS: [],
        StateKeys.MENTOR_CONTEXT: {},
        StateKeys.RETRIEVED_CONTEXT: {},
        StateKeys.LOGS: [],
        StateKeys.STATUS: "started"
    }
    
    # Execute the graph
    logger.info("[EXECUTION] Invoking extended orchestrator...")
    logger.info("[EXECUTION] This will run all analysis nodes with backend callbacks")
    
    try:
        final_state = app.invoke(initial_state)
        logger.info("[EXECUTION] Extended orchestrator complete")
        logger.info(f"[EXECUTION] Final status: {final_state.get(StateKeys.STATUS, 'unknown')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[EXECUTION] Orchestrator execution failed: {e}", exc_info=True)
        raise


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Local execution block for testing the extended orchestrator.
    """
    print("=" * 80)
    print("IncidentOS Extended Repository Intelligence Orchestrator")
    print("With Backend Callback Integration")
    print("=" * 80)
    print()
    
    # Check environment configuration
    backend_url = os.getenv("BACKEND_URL")
    callback_api_key = os.getenv("CALLBACK_API_KEY")
    
    if backend_url and callback_api_key:
        print(f"✓ Backend callbacks configured: {backend_url}")
    else:
        print("⚠ Backend callbacks NOT configured (will be skipped)")
        print("  Set BACKEND_URL and CALLBACK_API_KEY in .env to enable")
    print()
    
    # Determine repository path
    current_dir = os.getcwd()
    
    if current_dir.endswith('ai-engine'):
        repo_path = os.path.dirname(current_dir)
    else:
        repo_path = current_dir
    
    print(f"Analyzing repository at: {repo_path}")
    print()
    
    try:
        # Execute extended orchestrator
        final_state = execute_extended_orchestrator(
            repo_path=repo_path,
            repo_id="IncidentOS"
        )
        
        # Print summary
        print()
        print("=" * 80)
        print("ORCHESTRATOR RESULTS SUMMARY")
        print("=" * 80)
        print()
        
        print(f"Repository ID: {final_state.get(StateKeys.REPO_ID)}")
        print(f"Status: {final_state.get(StateKeys.STATUS)}")
        print()
        
        print(f"Services: {len(final_state.get(StateKeys.SERVICES, []))}")
        print(f"Languages: {', '.join(final_state.get(StateKeys.LANGUAGES, []))}")
        print(f"Frameworks: {', '.join(final_state.get(StateKeys.FRAMEWORKS, []))}")
        print()
        
        print(f"Dependencies: {len(final_state.get(StateKeys.DEPENDENCY_GRAPH, []))}")
        print(f"Fragility Scores: {len(final_state.get(StateKeys.FRAGILITY_SCORES, []))}")
        print(f"Incidents: {len(final_state.get(StateKeys.INCIDENTS, []))}")
        print()
        
        # Print logs
        logs = final_state.get(StateKeys.LOGS, [])
        if logs:
            print("=" * 80)
            print("EXECUTION LOGS")
            print("=" * 80)
            for log in logs[-10:]:  # Last 10 logs
                print(f"[{log.get('level')}] [{log.get('node')}] {log.get('message')}")
            print()
        
        print("=" * 80)
        print("SUCCESS: Extended orchestrator executed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR: Orchestrator execution failed")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
