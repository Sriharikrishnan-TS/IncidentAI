"""
Extended LangGraph Orchestrator with Backend Callback Integration.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.state import IncidentState, create_initial_state
from orchestration.shared_state import StateKeys
from orchestration.logging_config import configure_logging

# IMPORTANT: use orchestration wrapper nodes
from orchestration.nodes.repository_node import repository_node
from orchestration.nodes.dependency_node import dependency_node
from orchestration.nodes.fragility_node import fragility_node
from orchestration.nodes.incident_node import incident_node
from orchestration.nodes.mentor_node import mentor_node

# Configure logging
configure_logging(level="INFO", use_colors=True)
logger = logging.getLogger(__name__)


# ============================================================================
# EXTENDED ORCHESTRATOR
# ============================================================================

def create_extended_orchestrator():
    """
    Create extended LangGraph orchestrator with all analysis nodes.
    """

    try:
        from langgraph.graph import StateGraph, START, END

        logger.info("[ORCHESTRATOR] Initializing extended LangGraph...")

        workflow = StateGraph(IncidentState)

        # ------------------------------------------------------------------
        # IMPORTANT:
        # Use orchestration wrapper nodes
        # NOT raw agent nodes
        # ------------------------------------------------------------------

        workflow.add_node("repository", repository_node)
        workflow.add_node("dependency", dependency_node)
        workflow.add_node("fragility", fragility_node)
        workflow.add_node("incident", incident_node)
        workflow.add_node("mentor", mentor_node)

        # ------------------------------------------------------------------
        # PIPELINE
        # ------------------------------------------------------------------

        workflow.add_edge(START, "repository")
        workflow.add_edge("repository", "dependency")
        workflow.add_edge("dependency", "fragility")
        workflow.add_edge("fragility", "incident")
        workflow.add_edge("incident", "mentor")
        workflow.add_edge("mentor", END)

        # Compile graph
        app = workflow.compile()

        logger.info("[ORCHESTRATOR] Extended LangGraph compiled successfully")
        logger.info(
            "[ORCHESTRATOR] Pipeline: "
            "repository → dependency → fragility → incident → mentor"
        )

        return app

    except ImportError as e:
        logger.error(f"LangGraph not available: {e}")
        logger.error("Install with: pip install langgraph")
        raise

    except Exception as e:
        logger.error(
            f"Failed to create orchestrator: {e}",
            exc_info=True
        )
        raise


def execute_extended_orchestrator(
    repo_path: str,
    repo_id: str = "test-repo"
) -> Dict[str, Any]:
    """
    Execute the extended orchestrator on a repository.
    """

    logger.info(f"[EXECUTION] Starting extended orchestrator for {repo_id}")
    logger.info(f"[EXECUTION] Repository path: {repo_path}")

    # Create orchestrator
    app = create_extended_orchestrator()

    # ----------------------------------------------------------------------
    # INITIAL STATE
    # Create initial state using helper function, then add any custom fields
    # ----------------------------------------------------------------------

    initial_state: IncidentState = create_initial_state(repo_id, repo_path)

    logger.info("[EXECUTION] Invoking extended orchestrator...")
    logger.info(
        "[EXECUTION] This will run all analysis nodes "
        "with orchestration wrapper integration"
    )

    try:
        final_state = app.invoke(initial_state)

        logger.info("[EXECUTION] Extended orchestrator complete")

        logger.info(
            f"[EXECUTION] Final status: "
            f"{final_state.get(StateKeys.STATUS, 'unknown')}"
        )

        return final_state

    except Exception as e:
        logger.error(
            f"[EXECUTION] Orchestrator execution failed: {e}",
            exc_info=True
        )
        raise


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":

    print("=" * 80)
    print("IncidentOS Extended Repository Intelligence Orchestrator")
    print("With Backend Callback Integration")
    print("=" * 80)
    print()

    backend_url = os.getenv("BACKEND_URL")
    callback_api_key = os.getenv("CALLBACK_API_KEY")

    if backend_url and callback_api_key:
        print(f"✓ Backend callbacks configured: {backend_url}")
    else:
        print("⚠ Backend callbacks NOT configured (will be skipped)")
        print("  Set BACKEND_URL and CALLBACK_API_KEY in .env to enable")

    print()

    # IMPORTANT:
    # Analyze repo ROOT
    current_dir = os.getcwd()

    if current_dir.endswith("ai-engine"):
        repo_path = os.path.dirname(current_dir)
    else:
        repo_path = current_dir

    print(f"Analyzing repository at: {repo_path}")
    print()

    try:

        final_state = execute_extended_orchestrator(
            repo_path=repo_path,
            repo_id="IncidentOS"
        )

        print()
        print("=" * 80)
        print("ORCHESTRATOR RESULTS SUMMARY")
        print("=" * 80)
        print()

        print(f"Repository ID: {final_state.get(StateKeys.REPO_ID)}")
        print(f"Status: {final_state.get(StateKeys.STATUS)}")
        print()

        print(f"Services: {len(final_state.get(StateKeys.SERVICES, []))}")

        print(
            f"Languages: "
            f"{', '.join(final_state.get(StateKeys.LANGUAGES, []))}"
        )

        print(
            f"Frameworks: "
            f"{', '.join(final_state.get(StateKeys.FRAMEWORKS, []))}"
        )

        print()

        print(
            f"Dependencies: "
            f"{len(final_state.get(StateKeys.DEPENDENCY_GRAPH, []))}"
        )

        print(
            f"Fragility Scores: "
            f"{len(final_state.get(StateKeys.FRAGILITY_SCORES, []))}"
        )

        print(
            f"Incidents: "
            f"{len(final_state.get(StateKeys.INCIDENTS, []))}"
        )

        print()

        logs = final_state.get(StateKeys.LOGS, [])

        if logs:
            print("=" * 80)
            print("EXECUTION LOGS")
            print("=" * 80)

            for log in logs[-10:]:
                print(
                    f"[{log.get('level')}] "
                    f"[{log.get('node')}] "
                    f"{log.get('message')}"
                )

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